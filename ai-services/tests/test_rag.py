import zlib

import pytest

from app import chat, llm, rag

DIM = 1024  # besar agar tabrakan hash pada embedding palsu hampir tidak terjadi
KORPUS = [
    ("takaran-awal", "Takaran awal", "Takaran awal per cup adalah 200 gram untuk small dan 250 gram untuk large."),
    ("rumus-hitung", "Rumus", "Jumlah cup adalah berat isi dibagi takaran per cup dan dibulatkan ke bawah."),
    ("buah-tersedia", "Buah", "Buah yang tersedia adalah semangka, melon, mangga, dan jeruk."),
    ("batas-asisten", "Batas", "Aplikasi tidak mengelola stok otomatis dan transaksi penjualan."),
]


def fake_embed(teks):
    v = [0.0] * DIM
    for w in teks.lower().replace(".", " ").replace(",", " ").replace("?", " ").split():
        v[zlib.crc32(w.encode()) % DIM] += 1.0
    return v


@pytest.fixture
def pasang(monkeypatch):
    """Pasang indeks palsu kecil dan embedding palsu (tanpa jaringan), paksa mesin Python."""
    indeks = {"model": "model-palsu", "dim": DIM, "dim_diminta": None, "chunks": [
        {"id": i, "judul": j, "teks": t, "vektor": fake_embed(t)} for i, j, t in KORPUS]}
    monkeypatch.setattr(rag, "_INDEX", indeks)
    monkeypatch.setattr(rag, "_MESIN", None)
    monkeypatch.setattr(rag, "_embed_query", fake_embed)
    monkeypatch.setenv("RAG_MESIN", "python")
    monkeypatch.setenv("RAG_AMBANG", "0.2")
    return indeks


def llm_balas(monkeypatch, teks):
    monkeypatch.setattr(llm, "generate", lambda *a, **k: (teks, "model-uji"))


def test_cari_potongan_terdekat(pasang, rag_aktif):
    h = rag.cari("takaran awal 200 gram small", k=2)
    assert h[0]["id"] == "takaran-awal" and h[0]["skor"] >= h[1]["skor"] and h[0]["mesin"] == "python"
    assert rag.cari("apakah ada pengelolaan stok", k=1)[0]["id"] == "batas-asisten"


def test_jawab_normal(pasang, rag_aktif, monkeypatch):
    llm_balas(monkeypatch, "Takaran awalnya 200 gram untuk small dan 250 gram untuk large ya.")
    r = rag.jawab("takaran awal 200 gram small")
    assert r["sumber"][0] == "takaran-awal" and r["model"] == "model-uji" and r["embedding"] == "model-palsu"


def test_skor_rendah_tidak_menjawab(pasang, rag_aktif, monkeypatch):
    llm_balas(monkeypatch, "jawaban")
    assert rag.jawab("siapa presiden indonesia") is None


def test_llm_gagal_none(pasang, rag_aktif, monkeypatch):
    def gagal(*a, **k):
        raise llm.LLMError("mati")
    monkeypatch.setattr(llm, "generate", gagal)
    assert rag.jawab("takaran awal 200 gram small") is None


def test_angka_karangan_ditolak(pasang, rag_aktif, monkeypatch):
    llm_balas(monkeypatch, "Takaran awalnya 999 gram.")
    assert rag.jawab("takaran awal 200 gram small") is None


def test_embedding_gagal_none(pasang, rag_aktif, monkeypatch):
    def gagal(t):
        raise rag.RagError("jaringan")
    monkeypatch.setattr(rag, "_embed_query", gagal)
    assert rag.jawab("takaran awal 200 gram small") is None


def test_indeks_tidak_ada(rag_aktif, monkeypatch):
    monkeypatch.setattr(rag, "_INDEX", None)
    assert not rag.tersedia() and rag.jawab("apa saja") is None


def test_angka_aman():
    assert rag._angka_aman("ada 200 gram", "takaran 200 gram")
    assert rag._angka_aman("ada 2 langkah", "tanpa angka")  # angka kecil dibebaskan
    assert not rag._angka_aman("ada 777 gram", "takaran 200 gram")


def test_faiss_dan_python_sepakat(pasang, rag_aktif, monkeypatch):
    pytest.importorskip("faiss")
    py = rag.cari("takaran awal 200 gram small", k=3)
    monkeypatch.setattr(rag, "_MESIN", None)
    monkeypatch.setenv("RAG_MESIN", "faiss")
    fa = rag.cari("takaran awal 200 gram small", k=3)
    assert fa[0]["mesin"] == "faiss" and [x["id"] for x in fa] == [x["id"] for x in py]
    assert all(abs(a["skor"] - b["skor"]) < 1e-4 for a, b in zip(fa, py))


def test_chat_bantuan_memakai_rag(monkeypatch):
    monkeypatch.setattr(rag, "jawab", lambda q: {"teks": "Jawaban dari RAG.", "sumber": ["cara-pakai"], "skor": 0.8,
                                                  "mesin": "python", "model": "m", "embedding": "e"})
    def gagal(*a, **k):
        raise llm.LLMError("mati")
    monkeypatch.setattr(llm, "generate", gagal)
    r = chat.handle_message("gimana cara ubah takaran?")
    assert r["intent"] == "bantuan_penggunaan" and r["reply"] == "Jawaban dari RAG." and r["rag"]["sumber"] == ["cara-pakai"]
    assert r["explanation_source"] == "llm"


def test_chat_bantuan_cadangan_bila_rag_gagal(monkeypatch):
    def gagal(*a, **k):
        raise llm.LLMError("mati")
    monkeypatch.setattr(llm, "generate", gagal)
    r = chat.handle_message("gimana cara ubah takaran?")
    assert r["reply"] == chat.HELP and r["rag"] is None
