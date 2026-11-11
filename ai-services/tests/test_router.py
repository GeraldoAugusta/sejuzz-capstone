import json

import pytest

from app import chat, intent_model, llm

JSON_HITUNG = json.dumps({"intent": "hitung_estimasi", "fruit": "semangka", "amount": 0.75, "unit": "kg", "cup_size": "large"})


@pytest.fixture
def pasang(monkeypatch):
    """pasang(cls, llm_balasan): atur hasil classifier dan balasan LLM; kembalikan daftar flag json_mode tiap panggilan LLM."""
    panggilan = []

    def _pasang(cls, llm_balasan=None):
        monkeypatch.setattr(intent_model, "predict", lambda t: cls)

        def fake(prompt, system=None, temperature=0.4, json_mode=False):
            panggilan.append(json_mode)
            if llm_balasan is None:
                raise llm.LLMError("mati")
            return llm_balasan, "m"

        monkeypatch.setattr(llm, "generate", fake)
        return panggilan

    return _pasang


def C(intent, conf):
    return {"intent": intent, "confidence": conf, "probs": {}}


def test_oos_yakin_ditolak_tanpa_llm(pasang):
    p = pasang(C("out_of_scope", 0.8))
    r = chat.handle_message("siapa presiden indonesia")
    assert r["status"] == "refused" and r["intent_source"] == "classifier" and r["extraction_source"] == "none"
    assert r["intent_confidence"] == 0.8 and p == []


def test_bantuan_yakin_tanpa_llm(pasang):
    p = pasang(C("bantuan_penggunaan", 0.7))
    r = chat.handle_message("gimana cara ubah takaran")
    assert r["status"] == "answered" and r["intent"] == "bantuan_penggunaan" and p == []


def test_hitung_yakin_entitas_lengkap_tanpa_ekstraksi_llm(pasang):
    p = pasang(C("hitung_estimasi", 0.9))
    r = chat.handle_message("5 kg semangka cup large")
    assert r["status"] == "answered" and r["extraction_source"] == "rules" and r["intent_source"] == "classifier"
    assert r["calculation"]["jumlah_cup"] == 10
    assert True not in p  # tidak ada panggilan ekstraksi JSON


def test_hitung_entitas_kurang_ekstraksi_dibantu_llm(pasang):
    p = pasang(C("hitung_estimasi", 0.9), JSON_HITUNG)
    r = chat.handle_message("semangka 750 gram cup large")
    assert True in p and r["extraction_source"] == "llm" and r["intent_source"] == "classifier"
    assert r["calculation"]["berat_total_gram"] == 750.0


def test_tidak_yakin_jatuh_ke_jalur_lama(pasang):
    pasang(C("hitung_estimasi", 0.5))
    r = chat.handle_message("5 kg semangka cup large")
    assert r["intent_source"] == "rules" and r["intent_confidence"] == 0.5 and r["status"] == "answered"


def test_oos_ragu_tidak_langsung_ditolak(pasang):
    pasang(C("out_of_scope", 0.65), JSON_HITUNG)  # 0.65 < ambang tolak 0.7: LLM yang memutuskan
    r = chat.handle_message("semangka 750 gram cup large")
    assert r["status"] != "refused" and r["intent_source"] == "llm"


def test_classifier_tidak_tersedia(pasang):
    pasang(None)
    r = chat.handle_message("5 kg semangka cup large")
    assert r["intent_source"] == "rules" and r["intent_confidence"] is None and r["status"] == "answered"


def test_ambang_bisa_diatur_lewat_env(pasang, monkeypatch):
    pasang(C("hitung_estimasi", 0.9))
    monkeypatch.setenv("INTENT_THRESHOLD", "0.95")
    assert chat.handle_message("5 kg semangka cup large")["intent_source"] == "rules"


def test_takaran_yakin_buah_ditemukan_tanpa_llm(pasang):
    p = pasang(C("cek_takaran", 0.9))
    r = chat.handle_message("takaran melon per cup berapa gram")
    assert r["status"] == "answered" and "gram" in r["reply"] and p == []


def test_susut_buah_tak_dikenal_via_llm(pasang):
    p = pasang(C("info_susut_buah", 0.9), json.dumps(
        {"intent": "info_susut_buah", "fruit": "kiwi", "amount": None, "unit": None, "cup_size": None}))
    r = chat.handle_message("kiwi susutnya berapa")
    assert r["status"] == "need_more_info" and "kiwi" in r["reply"] and True in p
