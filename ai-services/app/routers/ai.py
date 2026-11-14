from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from app import chat, explain, rag
from app.routers.calculate import compute
from app.security import verify_api_key
from app.schemas import CalculateRequest, ChatRequest, ChatResponse, ErrorResponse, ExplainResponse, FaqRequest, FaqResponse

router = APIRouter(prefix="/api/v1/ai", tags=["Asisten AI"], dependencies=[Depends(verify_api_key)])


@router.post(
    "/explain",
    response_model=ExplainResponse,
    responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
)
def explain_endpoint(req: CalculateRequest):
    """Hitung dengan rumus, lalu minta LLM menjelaskan hasilnya. Angka selalu dari rumus."""
    calc, err = compute(req)
    if err:
        return err
    teks, source, model = explain.explain_calc(calc, req.amount, req.unit)
    return {"calculation": calc, "explanation": teks, "source": source, "model": model}


@router.post("/chat", response_model=ChatResponse, responses={400: {"model": ErrorResponse}})
def chat_endpoint(req: ChatRequest):
    """Asisten Sejuzz: pahami kalimat bebas, jawab estimasi/takaran/susut, tolak di luar konteks."""
    pesan = req.message.strip()
    if not pesan:
        return JSONResponse(status_code=400, content={"error": {"code": "EMPTY_MESSAGE", "message": "Pesan tidak boleh kosong."}})
    return chat.handle_message(pesan, req.takaran)


@router.post("/faq", response_model=FaqResponse, responses={400: {"model": ErrorResponse}})
def faq_endpoint(req: FaqRequest):
    """Tanya jawab panduan aplikasi dengan RAG (embedding + vector database + LLM)."""
    pertanyaan = req.question.strip()
    if not pertanyaan:
        return JSONResponse(status_code=400, content={"error": {"code": "EMPTY_MESSAGE", "message": "Pertanyaan tidak boleh kosong."}})
    r = rag.jawab(pertanyaan)
    if r is None:
        return {"status": "not_found", "answer": chat.HELP, "rag": None, "model": None}
    return {"status": "answered", "answer": r["teks"], "model": r["model"],
            "rag": {"sumber": r["sumber"], "skor": r["skor"], "mesin": r["mesin"], "embedding": r["embedding"]}}
