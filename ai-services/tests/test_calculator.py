import pytest
from app.calculator import CalculationError, build_spec, calculate

SEMANGKA = build_spec({"susut_persen": 30, "berat_rata_rata_gram": 3000,
                       "gram_per_cup": {"small": 350, "large": 500}})


def test_kasus_project_plan_10kg_susut_30():
    # Kasus uji Project Plan: 10 kg, susut 30% -> isi 7 kg
    r = calculate("semangka", 10, "kg", "small", SEMANGKA)
    assert r["berat_isi_gram"] == 7000.0
    assert r["berat_kulit_gram"] == 3000.0
    assert r["jumlah_cup"] == 20          # 7000 / 350
    assert r["sisa_buah_gram"] == 0.0


def test_ukuran_large_cup_lebih_sedikit():
    s = calculate("semangka", 10, "kg", "small", SEMANGKA)["jumlah_cup"]
    l = calculate("semangka", 10, "kg", "large", SEMANGKA)["jumlah_cup"]
    assert l < s and l == 14              # 7000 / 500


def test_sisa_buah():
    r = calculate("semangka", 1, "kg", "small", SEMANGKA)  # isi 700 g
    assert r["jumlah_cup"] == 2 and r["sisa_buah_gram"] == 0.0
    r = calculate("semangka", 1.1, "kg", "small", SEMANGKA)  # isi 770 g
    assert r["jumlah_cup"] == 2 and r["sisa_buah_gram"] == 70.0


def test_unit_buah_pakai_berat_rata_rata():
    r = calculate("semangka", 2, "buah", "small", SEMANGKA)  # 6000 g total
    assert r["berat_total_gram"] == 6000.0 and r["berat_isi_gram"] == 4200.0


@pytest.mark.parametrize("amount", [0, -1, "abc", None, True])
def test_amount_tidak_valid(amount):
    with pytest.raises(CalculationError) as e:
        calculate("semangka", amount, "kg", "small", SEMANGKA)
    assert e.value.code == "INVALID_AMOUNT"


def test_unit_dan_ukuran_tidak_valid():
    with pytest.raises(CalculationError):
        calculate("semangka", 1, "liter", "small", SEMANGKA)
    with pytest.raises(CalculationError):
        calculate("semangka", 1, "kg", "medium", SEMANGKA)


def test_takaran_belum_diisi():
    spec = build_spec({"susut_persen": 30, "berat_rata_rata_gram": 3000, "gram_per_cup": {"small": 0, "large": 500}})
    with pytest.raises(CalculationError) as e:
        calculate("semangka", 1, "kg", "small", spec)
    assert e.value.code == "TAKARAN_NOT_SET"


def test_override_gram_per_cup_dan_spec_none():
    spec = build_spec({"susut_persen": 30, "berat_rata_rata_gram": 3000, "gram_per_cup": {"small": None, "large": None}})
    with pytest.raises(CalculationError) as e:
        calculate("semangka", 10, "kg", "small", spec)
    assert e.value.code == "TAKARAN_NOT_SET"
    assert calculate("semangka", 10, "kg", "small", spec, gram_per_cup=350)["jumlah_cup"] == 20
