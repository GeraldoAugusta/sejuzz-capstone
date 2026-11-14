from typing import Annotated, List, Literal, Optional

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, StringConstraints

from app.security import verify_api_key
from app.sentimen import layanan

MAKS_KARAKTER = 1000
MAKS_BATCH = 100

router = APIRouter(prefix="/api/v1", tags=["Sentimen"], dependencies=[Depends(verify_api_key)])

RESPONS_ERROR = {
    401: {"description": "API key tidak ada atau tidak valid (header X-API-Key)"},
    422: {"description": "Input tidak valid, atau kalimat tidak berisi kata yang bisa dianalisis"},
    503: {"description": "Model sentimen belum tersedia atau gagal dimuat"},
}

Teks = Annotated[str, StringConstraints(max_length=MAKS_KARAKTER)]


class PermintaanSentimen(BaseModel):
    teks: Teks = Field(..., min_length=1, examples=["Jusnya segar banget, pelayanannya ramah"])


class PermintaanBatch(BaseModel):
    daftar_teks: List[Teks] = Field(..., min_length=1, max_length=MAKS_BATCH)


class HasilSentimen(BaseModel):
    teks: str
    sentimen: Optional[Literal["positif", "negatif"]] = None
    skor: Optional[float] = Field(None, description="Makin jauh dari 0 makin yakin. Positif = tebakan positif.")
    yakin: Optional[bool] = Field(None, description="False kalau |skor| < 0.5 (model ragu)")
    peringatan: Optional[str] = None


class HasilBatch(BaseModel):
    jumlah: int
    jumlah_positif: int
    jumlah_negatif: int
    jumlah_tidak_terbaca: int
    hasil: List[HasilSentimen]


def _error(status: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(status_code=status, content={"error": {"code": code, "message": message}})


@router.post("/sentimen", response_model=HasilSentimen, responses=RESPONS_ERROR,
             summary="Tebak sentimen satu kalimat")
def sentimen(req: PermintaanSentimen):
    try:
        hasil = layanan.analisis_banyak([req.teks])[0]
    except layanan.ModelTidakTersedia as e:
        return _error(503, "MODEL_UNAVAILABLE", e.pesan)
    if hasil is None:
        return _error(422, "TEXT_NOT_ANALYZABLE", layanan.PESAN_KOSONG)
    return hasil


@router.post("/sentimen/batch", response_model=HasilBatch, responses=RESPONS_ERROR,
             summary="Tebak sentimen banyak kalimat (maksimal 100)")
def sentimen_batch(req: PermintaanBatch):
    try:
        hasil = layanan.analisis_banyak(req.daftar_teks)
    except layanan.ModelTidakTersedia as e:
        return _error(503, "MODEL_UNAVAILABLE", e.pesan)
    items = [h if h is not None else {"teks": t, "peringatan": layanan.PESAN_KOSONG}
             for h, t in zip(hasil, req.daftar_teks)]
    return {
        "jumlah": len(items),
        "jumlah_positif": sum(1 for h in hasil if h and h["sentimen"] == "positif"),
        "jumlah_negatif": sum(1 for h in hasil if h and h["sentimen"] == "negatif"),
        "jumlah_tidak_terbaca": sum(1 for h in hasil if h is None),
        "hasil": items,
    }


@router.get("/sentimen/info", responses={k: v for k, v in RESPONS_ERROR.items() if k != 422},
            summary="Info model dan kecocokan versi scikit-learn")
def info():
    try:
        return layanan.info_model()
    except layanan.ModelTidakTersedia as e:
        return _error(503, "MODEL_UNAVAILABLE", e.pesan)
