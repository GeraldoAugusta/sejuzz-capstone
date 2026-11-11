from typing import Literal, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


class CalculateRequest(BaseModel):
    model_config = ConfigDict(json_schema_extra={"examples": [
        {"fruit": "semangka", "amount": 10, "unit": "kg", "cup_size": "small", "gram_per_cup": 200}]})

    fruit: str = Field(..., examples=["semangka"])
    amount: float = Field(..., gt=0, examples=[10])
    unit: Literal["kg", "buah"] = "kg"
    cup_size: Literal["small", "large"] = "small"
    gram_per_cup: Optional[float] = Field(
        None, gt=0, description="Opsional: takaran gram per cup, menimpa data takaran di service.")


class RentangEstimasi(BaseModel):
    cup_min: int
    cup_max: int
    isi_gram_min: float
    isi_gram_max: float
    persentil: str = Field(..., description="Dasar rentang, mis. P10-P90 dari sebaran yield per buah")
    jenis_data: str = Field(..., description="simulasi / nyata: asal data sebaran yield")


class CalculateResponse(BaseModel):
    fruit: str
    cup_size: str
    berat_total_gram: float
    berat_kulit_gram: float
    berat_isi_gram: float
    gram_per_cup: float
    jumlah_cup: int
    sisa_buah_gram: float
    rentang: Optional[RentangEstimasi] = Field(None, description="Opsional: kisaran wajar jumlah cup")


class ErrorBody(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    error: ErrorBody


class FruitsResponse(BaseModel):
    fruits: list[str]


class ExplainResponse(BaseModel):
    calculation: CalculateResponse
    explanation: str
    source: Literal["llm", "fallback"] = Field(..., description="llm = dijelaskan model AI, fallback = balasan template")
    model: Optional[str] = Field(None, description="Nama model bila source = llm")


class ChatRequest(BaseModel):
    model_config = ConfigDict(json_schema_extra={"examples": [
        {"message": "5 kilo semangka jadi berapa cup large?",
         "takaran": {"semangka": {"small": 200, "large": 250}, "melon": {"small": 200, "large": 250}}}]})

    message: str = Field(..., min_length=1, max_length=300, examples=["5 kilo semangka jadi berapa cup large?"])
    takaran: Optional[dict[str, dict[str, float]]] = Field(
        None,
        description="Opsional, diisi backend dari database: takaran gram per cup per buah, "
                    'mis. {"semangka": {"small": 200, "large": 250}}. Diutamakan di atas takaran bawaan service.',
    )

    @field_validator("takaran")
    @classmethod
    def _takaran_valid(cls, v):
        for buah, d in (v or {}).items():
            for ukuran, gram in d.items():
                if ukuran not in ("small", "large") or gram <= 0:
                    raise ValueError(f"takaran {buah}.{ukuran} tidak valid")
        return v


class ChatResponse(BaseModel):
    intent: str
    status: Literal["answered", "need_more_info", "refused"]
    reply: str
    calculation: Optional[CalculateResponse] = None
    missing: list[str] = []
    extraction: dict
    extraction_source: Literal["llm", "rules", "none"]
    explanation_source: Optional[Literal["llm", "fallback"]] = None
    model: Optional[str] = None
    intent_source: Optional[Literal["classifier", "llm", "rules"]] = Field(None, description="Siapa yang menentukan intent")
    intent_confidence: Optional[float] = Field(None, description="Keyakinan classifier (0-1) bila tersedia")
