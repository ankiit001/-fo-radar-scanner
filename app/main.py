
import os
import csv
import io

from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from app.scanner import score_rows
from app.groww_client import GrowwClient


app = FastAPI(
    title="F&O Radar Scanner API",
    description="Groww NSE F&O Intraday and Swing Scanner",
    version="1.0.0"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


def get_groww_client():
    return GrowwClient()


# -------------------------
# HOME
# -------------------------

@app.get("/")
def root():
    return {
        "app": "F&O Radar Scanner",
        "status": "running",
        "broker": "Groww",
        "timeframe": "5m",
        "universe": "NSE_FNO",
        "execution": "MANUAL_ONLY"
    }


# -------------------------
# HEALTH
# -------------------------

@app.get("/health")
def health():
    return {
        "status": "ok",
        "api": "online"
    }


# -------------------------
# CONFIG
# -------------------------

@app.get("/config")
def config():
    return {
        "broker": "Groww",
        "timeframe": "5m",
        "universe": "NSE_FNO",
        "direction": "BOTH",
        "indicators": [
            "EMA 34",
            "EMA 50",
            "EMA 200",
            "VWAP",
            "RSI",
            "ADX",
            "VOLUME"
        ],
        "execution": "MANUAL_ONLY",
        "live_api_ready": bool(
            os.getenv("GROWW_ACCESS_TOKEN")
        )
    }


# -------------------------
# GROWW API STATUS
# -------------------------

@app.get("/groww/status")
def groww_status():
    client = get_groww_client()

    return client.status()


# -------------------------
# GROWW QUOTE
# -------------------------

@app.get("/groww/quote")
def groww_quote(
    symbol: str = Query(..., min_length=1),
    segment: str = Query("CASH")
):
    if segment not in ("CASH", "FNO"):
        raise HTTPException(
            status_code=400,
            detail="Segment must be CASH or FNO"
        )

    try:
        client = get_groww_client()

        return client.get_quote(
            trading_symbol=symbol,
            segment=segment
        )

    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Groww quote request failed: {type(exc).__name__}"
        )


# -------------------------
# HISTORICAL 5 MIN CANDLES
# -------------------------

@app.get("/groww/candles")
def groww_candles(
    symbol: str = Query(..., min_length=1),
    segment: str = Query("CASH"),
    days: int = Query(5, ge=1, le=15)
):
    if segment not in ("CASH", "FNO"):
        raise HTTPException(
            status_code=400,
            detail="Segment must be CASH or FNO"
        )

    if not symbol.startswith("NSE-"):
        raise HTTPException(
            status_code=400,
            detail="Use NSE symbol format, e.g. NSE-RELIANCE"
        )

    try:
        client = get_groww_client()

        return client.get_historical_candles(
            groww_symbol=symbol,
            segment=segment,
            days=days
        )

    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Groww candles request failed: {type(exc).__name__}"
        )


# -------------------------
# DEMO SCANNER
# -------------------------

@app.get("/scan/demo")
def demo_scan():

    rows = [
        {
            "symbol": "DEMO_ALPHA",
            "close": 250,
            "ema34": 248,
            "ema50": 246,
            "ema200": 240,
            "vwap": 247,
            "prev_high": 249,
            "prev_low": 244,
            "volume": 180000,
            "avg_volume20": 100000,
            "rsi": 62,
            "adx": 27,
            "direction": "BUY"
        },
        {
            "symbol": "DEMO_BETA",
            "close": 510,
            "ema34": 512,
            "ema50": 514,
            "ema200": 520,
            "vwap": 513,
            "prev_high": 516,
            "prev_low": 511,
            "volume": 210000,
            "avg_volume20": 100000,
            "rsi": 38,
            "adx": 29,
            "direction": "SELL"
        }
    ]

    return {
        "mode": "DEMO_NOT_LIVE",
        "timeframe": "5m",
        "results": score_rows(rows)
    }


# -------------------------
# CSV SCANNER
# -------------------------

@app.post("/scan/csv")
async def scan_csv(file: UploadFile = File(...)):

    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=400,
            detail="Please upload a CSV file"
        )

    try:
        raw = (await file.read()).decode("utf-8-sig")

        rows = list(
            csv.DictReader(io.StringIO(raw))
        )

        if not rows:
            raise ValueError("CSV contains no data")

        numeric_fields = [
            "close",
            "ema34",
            "ema50",
            "ema200",
            "vwap",
            "prev_high",
            "prev_low",
            "volume",
            "avg_volume20",
            "rsi",
            "adx"
        ]

        for row in rows:
            for field in numeric_fields:
                row[field] = float(row[field])

            if not row.get("direction"):
                row["direction"] = "BUY"

        results = score_rows(rows)

        return {
            "mode": "CSV_IMPORTED_NOT_LIVE",
            "timeframe": "5m",
            "total_stocks": len(results),
            "results": results
        }

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f"CSV processing failed: {type(exc).__name__}"
        )
