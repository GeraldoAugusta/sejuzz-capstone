"""Modul rumus Sejuzz (murni Python

Rumus (sumber kebenaran angka, TIDAK diserahkan ke LLM):
    berat_total_g = berat_kg * 1000        (unit "kg")
                  = jumlah * berat_rata_rata_gram   (unit "buah")
    berat_isi_g   = berat_total_g * (1 - susut_persen / 100)
    berat_kulit_g = berat_total_g - berat_isi_g
    jumlah_cup    = floor(berat_isi_g / gram_per_cup)
    sisa_buah_g   = berat_isi_g - jumlah_cup * gram_per_cup
"""
from dataclasses import dataclass
from decimal import Decimal, ROUND_FLOOR

VALID_UNITS = ("kg", "buah")
VALID_SIZES = ("small", "large")


class CalculationError(ValueError):
    """Input tidak valid. Pesan ditujukan untuk pengguna akhir."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass(frozen=True)
class FruitSpec:
    susut_persen: Decimal
    berat_rata_rata_gram: Decimal
    gram_per_cup: dict  # {"small": Decimal, "large": Decimal}


def _d(x) -> Decimal:
    return Decimal(str(x))


def build_spec(raw: dict) -> FruitSpec:
    return FruitSpec(
        susut_persen=_d(raw["susut_persen"]),
        berat_rata_rata_gram=_d(raw["berat_rata_rata_gram"]),
        # takaran bernilai None = belum ada data komposisi menu
        gram_per_cup={k: (_d(v) if v is not None else None) for k, v in raw["gram_per_cup"].items()},
    )


def calculate(fruit: str, amount, unit: str, cup_size: str, spec: FruitSpec, gram_per_cup=None) -> dict:
    """gram_per_cup (opsional) menimpa takaran di spec, mis. dikirim backend dari tabel takaran."""
    if unit not in VALID_UNITS:
        raise CalculationError("INVALID_UNIT", "Satuan harus 'kg' atau 'buah'.")
    if cup_size not in VALID_SIZES:
        raise CalculationError("INVALID_CUP_SIZE", "Ukuran cup harus 'small' atau 'large'.")
    if isinstance(amount, bool) or not isinstance(amount, (int, float, Decimal)):
        raise CalculationError("INVALID_AMOUNT", "Berat atau jumlah harus berupa angka.")
    if _d(amount) <= 0:
        raise CalculationError("INVALID_AMOUNT", "Berat atau jumlah harus lebih dari 0.")

    gpc = _d(gram_per_cup) if gram_per_cup is not None else spec.gram_per_cup.get(cup_size)
    if gpc is None or gpc <= 0:
        raise CalculationError(
            "TAKARAN_NOT_SET",
            f"Takaran cup {cup_size} untuk {fruit} belum diisi.",
        )
    if not (Decimal(0) <= spec.susut_persen < Decimal(100)):
        raise CalculationError("INVALID_SUSUT", "Faktor susut harus 0 sampai kurang dari 100.")

    amount = _d(amount)
    total_g = amount * 1000 if unit == "kg" else amount * spec.berat_rata_rata_gram
    isi_g = total_g * (1 - spec.susut_persen / 100)
    kulit_g = total_g - isi_g
    cups = (isi_g / gpc).to_integral_value(rounding=ROUND_FLOOR)
    sisa_g = isi_g - cups * gpc

    r = lambda v: float(v.quantize(Decimal("0.01")))
    return {
        "fruit": fruit,
        "cup_size": cup_size,
        "berat_total_gram": r(total_g),
        "berat_kulit_gram": r(kulit_g),
        "berat_isi_gram": r(isi_g),
        "gram_per_cup": r(gpc),
        "jumlah_cup": int(cups),
        "sisa_buah_gram": r(sisa_g),
    }
