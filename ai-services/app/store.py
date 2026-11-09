"""Sumber data takaran.

Sementara membaca fruits.json (data contoh). Nanti diganti membaca tabel dari
backend Full-stack (PostgreSQL) agar owner bisa mengubah takaran. Cukup ubah
get_fruit() dan list_fruits(); modul lain tidak terpengaruh.
"""
import json
from pathlib import Path

_PATH = Path(__file__).parent / "data" / "fruits.json"
_DATA = json.loads(_PATH.read_text(encoding="utf-8"))["fruits"]


def list_fruits() -> list[str]:
    return sorted(_DATA)


def get_fruit(name: str) -> dict | None:
    return _DATA.get(name.strip().lower())
