import pytest

from app import explain, service, store


@pytest.mark.parametrize("buah", store.list_fruits())
def test_rentang_membungkus_estimasi(buah):
    for ukuran in ("small", "large"):
        calc, err = service.run_calculation(buah, 10, "kg", ukuran)
        assert err is None and calc["rentang"] is not None
        r = calc["rentang"]
        assert r["cup_min"] <= calc["jumlah_cup"] <= r["cup_max"]
        assert r["isi_gram_min"] <= calc["berat_isi_gram"] <= r["isi_gram_max"]


def test_kelapa_rentang_lebih_lebar_dari_blackberry():
    lebar = lambda b: (lambda r: r["isi_gram_max"] - r["isi_gram_min"])(service.run_calculation(b, 10, "kg", "small")[0]["rentang"])
    assert lebar("kelapa") > lebar("blackberry")


def test_kalimat_kisaran_dan_label_simulasi():
    calc, _ = service.run_calculation("semangka", 10, "kg", "small")
    k = explain.kisaran(calc)
    assert "Kisaran" in k and "simulasi" in k
    assert explain.kisaran({}) == ""


def test_override_takaran_ikut_mengubah_rentang():
    a, _ = service.run_calculation("semangka", 10, "kg", "small", 200)
    b, _ = service.run_calculation("semangka", 10, "kg", "small", 400)
    assert b["rentang"]["cup_max"] < a["rentang"]["cup_max"]
