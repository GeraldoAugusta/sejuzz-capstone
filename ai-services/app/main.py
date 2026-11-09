import os

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.routers import ai, calculate
from app.security import UnauthorizedError

load_dotenv()

app = FastAPI(
    title="Sejuzz AI Service",
    version="0.1.0",
    description="Modul perhitungan estimasi cup jus dan Asisten AI Sejuzz.",
)

origins = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "*").split(",")]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_methods=["*"], allow_headers=["*"])


@app.exception_handler(RequestValidationError)
async def validation_handler(_: Request, exc: RequestValidationError):
    # Format error seragam untuk Full-stack: {"error": {"code", "message"}}
    try:
        lokasi = []
        for e in exc.errors():
            path = ".".join(str(p) for p in e.get("loc", ()) if p != "body")
            if path and path not in lokasi:
                lokasi.append(path)
        rinci = f" pada: {', '.join(lokasi[:3])}" if lokasi else ""
    except Exception:
        rinci = ""
    return JSONResponse(
        status_code=422,
        content={"error": {"code": "VALIDATION_ERROR",
                           "message": f"Input tidak valid{rinci}. Periksa format sesuai dokumentasi di /docs."}},
    )


@app.exception_handler(UnauthorizedError)
async def unauthorized_handler(_: Request, __: UnauthorizedError):
    return JSONResponse(status_code=401, content={"error": {"code": "UNAUTHORIZED",
                                                            "message": "API key tidak ada atau tidak valid (header X-API-Key)."}})


@app.get("/health", tags=["Sistem"])
def health():
    return {"status": "ok"}


app.include_router(calculate.router)
app.include_router(ai.router)
