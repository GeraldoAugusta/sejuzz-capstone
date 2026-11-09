"""Perhitungan tingkat service (tanpa FastAPI), dipakai /calculate, /ai/explain, dan /ai/chat."""
from app import rentang, store
from app.calculator import CalculationError, build_spec, calculate


def run_calculation(fruit: str, amount, unit: str, cup_size: str, gram_per_cup=None):
    """Kembalikan (hasil, None) atau (None, {"status", "code", "message"})."""
    raw = store.get_fruit(fruit)
    if raw is None:
        return None, {"status": 404, "code": "FRUIT_NOT_FOUND",
                      "message": f"Buah '{fruit}' belum ada di data takaran."}
    try:
        hasil = calculate(fruit.strip().lower(), amount, unit, cup_size, build_spec(raw), gram_per_cup)
        hasil["rentang"] = rentang.hitung_rentang(hasil["fruit"], hasil["berat_total_gram"], hasil["gram_per_cup"])
        return hasil, None
    except CalculationError as e:
        return None, {"status": 400, "code": e.code, "message": e.message}
