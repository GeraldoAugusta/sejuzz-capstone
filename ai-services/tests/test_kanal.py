import pytest

from app import chat
from app.kanal import inti, telegram


def upd(teks="5 kg semangka cup large", uid=1, cid=111, tipe="private", **tambahan):
    msg = {"chat": {"id": cid, "type": tipe}}
    if teks is not None:
        msg["text"] = teks
    msg.update(tambahan)
    return {"update_id": uid, "message": msg}


@pytest.fixture
def bersih(monkeypatch):
    """Keadaan bersih untuk setiap tes: anti-ganda dan batas laju baru, tanpa daftar izin."""
    monkeypatch.setattr(telegram, "_DEDUP", inti.AntiGanda())
    monkeypatch.setattr(telegram, "_BATAS", inti.BatasLaju(maks=3))
    monkeypatch.delenv("TELEGRAM_ALLOWED_CHAT_IDS", raising=False)
    monkeypatch.setattr(chat, "handle_message", lambda t, takaran=None: {"reply": f"jawab:{t}"})
    terkirim = []
    return lambda cid, teks: terkirim.append((cid, teks)), terkirim


def test_perintah(bersih):
    assert inti.balasan("/start") == chat.GREETING_REPLY
    assert "/help" in inti.balasan("/help@SejuzzBot") and chat.HELP in inti.balasan("/help")
    assert inti.balasan("/id", 42) == "ID chat kamu: 42"
    assert "belum ada" in inti.balasan("/hapussemua")
    assert "teks" in inti.balasan("   ")


def test_balasan_memanggil_chat_dan_batas_panjang(bersih):
    assert inti.balasan("halo semangka") == "jawab:halo semangka"
    assert "terlalu panjang" in inti.balasan("x" * (inti.MAKS_PANJANG + 1))


def test_batas_laju_dengan_waktu_palsu():
    t = [0.0]
    b = inti.BatasLaju(maks=2, jendela=60, waktu=lambda: t[0])
    assert b.izinkan("a") and b.izinkan("a") and not b.izinkan("a")
    assert b.izinkan("b")  # chat lain tidak ikut terbatas
    t[0] = 61.0
    assert b.izinkan("a")  # jendela lewat


def test_anti_ganda():
    a = inti.AntiGanda(kapasitas=2)
    assert a.baru(1) and not a.baru(1) and a.baru(2) and a.baru(3) and a.baru(1)  # id 1 sudah tersingkir


def test_dibalas(bersih):
    kirim, terkirim = bersih
    assert telegram.proses_update(upd("takaran melon"), kirim) == "dibalas"
    assert terkirim == [(111, "jawab:takaran melon")]


def test_duplikat_tidak_dibalas_dua_kali(bersih):
    kirim, terkirim = bersih
    assert telegram.proses_update(upd(uid=7), kirim) == "dibalas"
    assert telegram.proses_update(upd(uid=7), kirim) == "duplikat" and len(terkirim) == 1


def test_grup_dan_selain_pesan_diabaikan(bersih):
    kirim, terkirim = bersih
    assert telegram.proses_update(upd(uid=1, tipe="group"), kirim) == "diabaikan_bukan_privat"
    assert telegram.proses_update({"update_id": 2, "edited_message": {}}, kirim) == "diabaikan_bukan_pesan"
    assert terkirim == []


def test_bukan_teks_dijawab_sopan(bersih):
    kirim, terkirim = bersih
    assert telegram.proses_update(upd(None, uid=3, photo=[{"file_id": "x"}]), kirim) == "diabaikan_bukan_teks"
    assert "teks" in terkirim[0][1]


def test_daftar_izin(bersih, monkeypatch):
    kirim, terkirim = bersih
    monkeypatch.setenv("TELEGRAM_ALLOWED_CHAT_IDS", "999, 111")
    assert telegram.proses_update(upd(uid=4, cid=111), kirim) == "dibalas"
    assert telegram.proses_update(upd(uid=5, cid=222), kirim) == "ditolak_izin"
    assert "terdaftar" in terkirim[-1][1]


def test_dibatasi_setelah_melewati_batas(bersih):
    kirim, terkirim = bersih
    hasil = [telegram.proses_update(upd(uid=10 + i), kirim) for i in range(5)]
    assert hasil == ["dibalas"] * 3 + ["dibatasi"] * 2


def test_error_tidak_mematikan_webhook(bersih, monkeypatch):
    kirim, terkirim = bersih

    def meledak(t, takaran=None):
        raise RuntimeError("rusak")
    monkeypatch.setattr(chat, "handle_message", meledak)
    assert telegram.proses_update(upd(uid=20), kirim) == "error"
    assert "gangguan" in terkirim[-1][1]


def test_rahasia_webhook(monkeypatch):
    monkeypatch.delenv("TELEGRAM_WEBHOOK_SECRET", raising=False)
    assert not telegram.rahasia_valid("apa-saja") and not telegram.rahasia_valid(None)  # gagal tertutup
    monkeypatch.setenv("TELEGRAM_WEBHOOK_SECRET", "rahasia-uji")
    assert telegram.rahasia_valid("rahasia-uji")
    assert not telegram.rahasia_valid("salah") and not telegram.rahasia_valid(None)
