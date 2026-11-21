from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.scanner import score_rows
from app.groww_client import GrowwClient

app = FastAPI(title="F&O Radar Scanner API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict to your dashboard domain before production.
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"app": "F&O Radar Scanner", "mode": "starter", "message": "Backend is running"}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/config")
def config():
    return {
        "broker": "Groww",
        "data_mode": "CSV_OR_DEMO",
        "timeframe": "5m",
        "universe": "NSE_FNO",
        "execution": "MANUAL_ONLY",
        "live_api_ready": bool(__import__("os").getenv("GROWW_ACCESS_TOKEN")),
        "note": "Live feed is disabled until an active Groww Trading API subscription and token are configured."
    }

@app.get("/scan/demo")
def demo_scan():
    # Clearly synthetic examples for testing the UI and ranking logic only.
    rows = [
        {"symbol":"DEMO_ALPHA","close":250,"ema34":248,"ema50":246,"ema200":240,"vwap":247,"prev_high":249,"prev_low":244,"volume":180000,"avg_volume20":100000,"rsi":62,"adx":27,"direction":"BUY"},
        {"symbol":"DEMO_BETA","close":510,"ema34":512,"ema50":514,"ema200":520,"vwap":513,"prev_high":516,"prev_low":511,"volume":210000,"avg_volume20":100000,"rsi":38,"adx":29,"direction":"SELL"},
        {"symbol":"DEMO_GAMMA","close":120,"ema34":119,"ema50":118,"ema200":116,"vwap":119,"prev_high":121,"prev_low":117,"volume":90000,"avg_volume20":100000,"rsi":54,"adx":18,"direction":"BUY"}
    ]
    return {"mode":"DEMO_NOT_LIVE","timeframe":"5m","results":score_rows(rows)}

@app.post("/scan/csv")
async def scan_csv(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Please upload a CSV file.")
    raw = (await file.read()).decode("utf-8-sig")
    import csv, io
    try:
        rows = list(csv.DictReader(io.StringIO(raw)))
        if not rows:
            raise ValueError("CSV has no data rows")
        numeric = ["close","ema34","ema50","ema200","vwap","prev_high","prev_low","volume","avg_volume20","rsi","adx"]
        for row in rows:
            for key in numeric:
                row[key] = float(row[key])
        return {"mode":"CSV_IMPORTED_NOT_LIVE","timeframe":"5m","results":score_rows(rows)}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"CSV format error: {exc}")

@app.get("/groww/status")
def groww_status():
    client = GrowwClient()
    return client.status()
