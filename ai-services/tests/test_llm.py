import httpx
import pytest

from app import fallback, llm, prompts

CALC = {"fruit": "semangka", "cup_size": "small", "berat_total_gram": 10000.0, "berat_kulit_gram": 4890.0,
        "berat_isi_gram": 5110.0, "gram_per_cup": 200.0, "jumlah_cup": 25, "sisa_buah_gram": 110.0}


class FakeResp:
    def __init__(self, status, text="halo"):
        self.status_code, self._text = status, text
        self.text = str(text)

    def json(self):
        return {"candidates": [{"content": {"parts": [{"text": self._text}]}}]}


@pytest.fixture(autouse=True)
def env(monkeypatch):
    monkeypatch.setenv("LLM_API_KEY", "kunci-uji")
    monkeypatch.setenv("LLM_MODEL", "model-a")
    monkeypatch.setenv("LLM_FALLBACK_MODELS", "model-b")
    monkeypatch.setenv("LLM_RETRIES", "2")
    monkeypatch.setattr(llm.time, "sleep", lambda s: None)


def pasang(monkeypatch, urutan):
    """urutan: daftar respons/exception per panggilan; dicatat model yang dipanggil."""
    dipanggil = []

    def fake_post(url, **kw):
        dipanggil.append(url.split("/models/")[1].split(":")[0])
        item = urutan.pop(0)
        if isinstance(item, Exception):
            raise item
        return item

    monkeypatch.setattr(llm.httpx, "post", fake_post)
    return dipanggil


def test_berhasil_model_utama(monkeypatch):
    d = pasang(monkeypatch, [FakeResp(200, "siap")])
    assert llm.generate("x") == ("siap", "model-a") and d == ["model-a"]


def test_503_diulang_lalu_berhasil(monkeypatch):
    d = pasang(monkeypatch, [FakeResp(503), FakeResp(200, "ok")])
    assert llm.generate("x") == ("ok", "model-a") and d == ["model-a", "model-a"]


def test_timeout_terus_pindah_model_cadangan(monkeypatch):
    d = pasang(monkeypatch, [httpx.ReadTimeout("t"), httpx.ReadTimeout("t"), FakeResp(200, "dari b")])
    assert llm.generate("x") == ("dari b", "model-b") and d == ["model-a", "model-a", "model-b"]


def test_404_langsung_pindah_tanpa_ulang(monkeypatch):
    d = pasang(monkeypatch, [FakeResp(404), FakeResp(200, "dari b")])
    assert llm.generate("x")[1] == "model-b" and d == ["model-a", "model-b"]


def test_semua_gagal_raise(monkeypatch):
    pasang(monkeypatch, [FakeResp(429), FakeResp(503), FakeResp(503)])
    with pytest.raises(llm.LLMError):
        llm.generate("x")


def test_key_kosong(monkeypatch):
    monkeypatch.setenv("LLM_API_KEY", "")
    with pytest.raises(llm.LLMError):
        llm.generate("x")


def test_jawaban_kosong_pindah_model(monkeypatch):
    d = pasang(monkeypatch, [FakeResp(200, ""), FakeResp(200, "isi")])
    assert llm.generate("x")[1] == "model-b"


def test_prompt_memuat_angka_dari_rumus():
    p = prompts.build_prompt(CALC, 10, "kg")
    assert '"jumlah_cup": 25' in p and "10 kg" in p and "JAWABAN:" in p


def test_template_fallback_memuat_angka():
    t = fallback.explain_template(CALC, 10, "kg")
    assert "25 cup" in t and "5.110" in t and "110" in t and "estimasi" in t
    nol = fallback.explain_template({**CALC, "jumlah_cup": 0, "sisa_buah_gram": 91.45}, 0.1, "kg")
    assert "belum cukup" in nol
