from fastapi import APIRouter
from fastapi.responses import JSONResponse
from core.bybit_client import get_spot_balances, get_futures_positions

router = APIRouter()

@router.get("/api/spot_balances")
def api_spot_balances():
    try:
        data = get_spot_balances("UNIFIED")
        return JSONResponse({"spot": data.get("result", {}).get("list", data)}, status_code=200)
    except Exception as e:
        return JSONResponse({"spot": [{"error": str(e)}]}, status_code=500)

@router.get("/api/futures_positions")
def api_futures_positions():
    try:
        data = get_futures_positions("linear")
        return JSONResponse({"futures": data.get("result", {}).get("list", data)}, status_code=200)
    except Exception as e:
        return JSONResponse({"futures": [{"error": str(e)}]}, status_code=500)
