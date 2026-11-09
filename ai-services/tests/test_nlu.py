import pytest

from app import llm, nlu


@pytest.mark.parametrize("raw,ok", [
    ({"intent": "hitung_estimasi", "fruit": "Semangka", "amount": "5", "unit": "Kilo", "cup_size": "Besar"}, True),
    ({"intent": "ngawur"}, False),
    ("bukan dict", False),
])
def test_normalize_validasi(raw, ok):
    if ok:
        r = nlu.normalize(raw)
        assert r == {"intent": "hitung_estimasi", "fruit": "semangka", "fruit_unknown": None,
                     "amount": 5.0, "unit": "kg", "cup_size": "large"}
    else:
        with pytest.raises(ValueError):
            nlu.normalize(raw)


def test_normalize_buah_tidak_dikenal_dan_angka_buruk():
    r = nlu.normalize({"intent": "hitung_estimasi", "fruit": "durian", "amount": -3, "unit": "liter", "cup_size": "medium"})
    assert r["fruit"] is None and r["fruit_unknown"] == "durian"
    assert r["amount"] is None and r["unit"] is None and r["cup_size"] is None


@pytest.mark.parametrize("kalimat,intent,fruit,amount,unit,size", [
    ("5 kilo semangka jadi berapa cup large?", "hitung_estimasi", "semangka", 5.0, "kg", "large"),
    ("lima kilo melon cup besar", "hitung_estimasi", "melon", 5.0, "kg", "large"),
    ("setengah kg mangga cup sedang", "hitung_estimasi", "mangga", 0.5, "kg", "small"),
    ("3 semangka bisa berapa cup", "hitung_estimasi", "semangka", 3.0, "buah", None),
    ("takaran melon per cup berapa gram?", "cek_takaran", "melon", None, None, None),
    ("mangga susutnya berapa persen", "info_susut_buah", "mangga", None, None, None),
    ("gimana cara ubah takaran?", "bantuan_penggunaan", None, None, None, None),
    ("siapa presiden indonesia?", "out_of_scope", None, None, None, None),
    ("berapa harga semangka per kilo", "out_of_scope", "semangka", None, None, None),
    ("halo", "out_of_scope", None, None, None, None),
])
def test_rules(kalimat, intent, fruit, amount, unit, size):
    r = nlu.extract_rules(kalimat)
    assert (r["intent"], r["fruit"], r["amount"], r["unit"], r["cup_size"]) == (intent, fruit, amount, unit, size)


def test_extract_pakai_llm_bila_valid(monkeypatch):
    monkeypatch.setattr(llm, "generate", lambda *a, **k: (
        '```json\n{"intent":"hitung_estimasi","fruit":"tomat","amount":2,"unit":"kg","cup_size":"small"}\n```', "m"))
    r, src, model = nlu.extract("2 kg tomat")
    assert src == "llm" and model == "m" and r["fruit"] == "tomat"


@pytest.mark.parametrize("keluaran", ["bukan json", '{"intent":"aneh"}'])
def test_extract_jatuh_ke_rules_bila_llm_buruk(monkeypatch, keluaran):
    monkeypatch.setattr(llm, "generate", lambda *a, **k: (keluaran, "m"))
    r, src, model = nlu.extract("5 kg semangka cup large")
    assert src == "rules" and model is None and r["intent"] == "hitung_estimasi"


def test_extract_jatuh_ke_rules_bila_llm_error(monkeypatch):
    def gagal(*a, **k):
        raise llm.LLMError("x")
    monkeypatch.setattr(llm, "generate", gagal)
    assert nlu.extract("halo")[1] == "rules"
