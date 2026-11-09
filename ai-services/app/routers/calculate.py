from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from app import service, store
from app.security import verify_api_key
from app.schemas import CalculateRequest, CalculateResponse, ErrorResponse, FruitsResponse

router = APIRouter(prefix="/api/v1", tags=["Kalkulator"], dependencies=[Depends(verify_api_key)])


@router.get("/fruits", response_model=FruitsResponse)
def fruits():
    return {"fruits": store.list_fruits()}


def compute(req: CalculateRequest):
    """Kembalikan (hasil, None) atau (None, JSONResponse error). Dipakai /calculate dan /ai/explain."""
    res, err = service.run_calculation(req.fruit, req.amount, req.unit, req.cup_size, req.gram_per_cup)
    if err:
        return None, JSONResponse(status_code=err["status"],
                                  content={"error": {"code": err["code"], "message": err["message"]}})
    return res, None


@router.post(
    "/calculate",
    response_model=CalculateResponse,
    responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
)
def calculate_endpoint(req: CalculateRequest):
    res, err = compute(req)
    return err if err else res
