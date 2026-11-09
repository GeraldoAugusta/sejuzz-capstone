"""Pengaman sederhana untuk service yang di-deploy publik: API key di header X-API-Key.

Aktif hanya bila environment SERVICE_API_KEY terisi (di lokal dibiarkan kosong, jadi tidak mengganggu).
Tujuannya mencegah orang asing menghabiskan kuota LLM. Backend Express mengirim header ini.
"""
import os
import secrets

from fastapi import Security
from fastapi.security import APIKeyHeader

_header = APIKeyHeader(name="X-API-Key", auto_error=False, description="Diisi backend. Kosongkan bila service lokal tanpa SERVICE_API_KEY.")


class UnauthorizedError(Exception):
    """API key tidak ada atau salah."""


def verify_api_key(key: str | None = Security(_header)) -> None:
    expected = os.getenv("SERVICE_API_KEY", "")
    if not expected:
        return
    if not key or not secrets.compare_digest(key, expected):
        raise UnauthorizedError()
