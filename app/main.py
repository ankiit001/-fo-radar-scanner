
import os
import csv
import io
import logging
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from app.scanner import score_rows
from app.sahi_client import SahiClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Correct project paths
APP_DIR = Path(__file__).resolve().parent
DASHBOARD_FILE = APP_DIR / "static" / "index.html"

app = FastAPI(
    title="ANKIT SMART SCANNER",
    description="NSE F&O Intraday Scanner using Sahi",
    version="2.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


def get_sahi_client():
    return SahiClient()


def serve_dashboard():
    if not DASHBOARD_FILE.is_file():
        logger.error("Dashboard missing: %s", DASHBOARD_FILE)
        raise HTTPException(
            status_code=404,
            detail="Dashboard not found: app/static/index.html"
        )

    return FileResponse(
        path=str(DASHBOARD_FILE),
        media_type="text/html"
    )


@app.get("/")
def root():
    return serve_dashboard()


@app.get("/dashboard")
def dashboard():
    return serve_dashboard()


@app.get("/health")
def health():
    return {
        "status": "ok",
        "api": "online",
        "app": "ANKIT SMART SCANNER",
        "dashboard": DASHBOARD_FILE.is_file(),
        "dashboard_path": str(DASHBOARD_FILE)
    }


@app.get("/config")
def config():
    return {
        "app": "ANKIT SMART SCANNER",
        "broker": "Sahi",
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
        "data_mode": "DEMO_UNTIL_SAHI_API_VERIFIED",
        "live_api_ready": bool(
            os.getenv("SAHI_KEY_ID", "").strip()
            and os.getenv("SAHI_SECRET", "").strip()
        )
    }


@app.get("/sahi/status")
def sahi_status():
    try:
        return get_sahi_client().status()

    except Exception:
        logger.exception("Sahi status failed")
        raise HTTPException(
            status_code=502,
            detail="Sahi API status check failed"
        )


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
        "broker": "Sahi",
        "timeframe": "5m",
        "total_stocks": len(rows),
        "results": score_rows(rows)
    }


@app.post("/scan/csv")
async def scan_csv(file: UploadFile = File(...)):

    if (
        not file.filename
        or not file.filename.lower().endswith(".csv")
    ):
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

        required_fields = [
            "symbol",
            *numeric_fields
        ]

        for field in required_fields:
            if field not in rows[0]:
                raise ValueError(
                    f"Missing CSV column: {field}"
                )

        for row in rows:

            for field in numeric_fields:
                row[field] = float(row[field])

            row["direction"] = (
                row.get("direction") or "BUY"
            ).upper()

            if row["direction"] not in ("BUY", "SELL"):
                raise ValueError(
                    "Direction must be BUY or SELL"
                )

        results = score_rows(rows)

        return {
            "mode": "CSV_IMPORTED_NOT_LIVE",
            "broker": "Sahi",
            "timeframe": "5m",
            "total_stocks": len(results),
            "results": results
        }

    except HTTPException:
        raise

    except Exception as exc:
        logger.exception("CSV processing failed")

        raise HTTPException(
            status_code=400,
            detail=f"CSV processing failed: {str(exc)}"
        )
