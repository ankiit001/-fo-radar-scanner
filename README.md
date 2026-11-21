# F&O Radar Scanner API — Starter Module

This is a deployable backend starter for an Android-friendly F&O scanner.
It is **not a live trading system yet**.

## Current features
- `/health` — health check
- `/config` — scanner configuration and live readiness
- `/scan/demo` — synthetic demo rows (never treat as market data)
- `/scan/csv` — upload a CSV containing 5-minute indicator values
- `/groww/status` — reports whether a server-side token is configured

## Scanner columns required in CSV
`symbol, close, ema34, ema50, ema200, vwap, prev_high, prev_low, volume, avg_volume20, rsi, adx, direction`

`direction` must be `BUY` or `SELL`. This starter ranks rows using transparent rule points.
The score is **not** a probability and is not evidence of profitability.

## Run locally
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Android/Termux or Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```
Open `/docs` to test endpoints.

## Free hosting
1. Create a GitHub repository and upload these files.
2. In Render, choose New -> Blueprint and connect that repository.
3. Render reads `render.yaml`; deploy the free web service.
4. Test `/health` and `/docs`.

**Free-tier warning:** Render free web services can sleep after 15 minutes without inbound traffic, restart, and lose local filesystem changes. They are suitable for prototype/testing, not dependable 9:30 AM scheduled scans or production trading. A free service also does not provide a reliable always-on scheduler.

## Groww live integration — not enabled yet
Groww's official API documentation states that F&O live data endpoints exist, but an active Trading API subscription is required. Access tokens expire daily at 6:00 AM (for the documented access-token flow). Keep credentials only in server environment variables/secrets; never place them in browser JavaScript, GitHub, CSV files, or chat.

After subscribing:
- Add `GROWW_ACCESS_TOKEN` in Render -> Environment.
- Do not assume this alone enables live data. The Groww historical 5-minute candle endpoint and live-feed adapter still need to be implemented and tested against the current official API schema.
- Recheck token expiry/authentication daily.
- Observe published API rate limits.
- Do not add order-placement code until signal generation has been validated in paper trading.

## Strategy rules in this starter
- Trend: EMA34 > EMA50 > EMA200 for BUY; reverse for SELL
- VWAP: close above for BUY; below for SELL
- Breakout: close above previous high for BUY; below previous low for SELL
- Volume: compare current volume to 20-bar average
- RSI directional filter and ADX >= 20 as a watchlist gate
- Output status is WATCH / NO_TRADE only; no automatic orders.

import os
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo


class GrowwClient:
    def __init__(self):
        self.token = os.getenv("GROWW_ACCESS_TOKEN", "").strip()
        self._groww = None

    def _get_client(self):
        if not self.token:
            raise RuntimeError("GROWW_ACCESS_TOKEN is not configured")

        if self._groww is None:
            from growwapi import GrowwAPI
            self._groww = GrowwAPI(self.token)

        return self._groww

    def status(self):
        if not self.token:
            return {
                "connected": False,
                "reason": "GROWW_ACCESS_TOKEN is not configured"
            }

        try:
            groww = self._get_client()
            profile = groww.get_user_profile()

            return {
                "connected": True,
                "authentication": "SUCCESS",
                "broker": "Groww",
                "nse_enabled": profile.get("nse_enabled"),
                "active_segments": profile.get("active_segments", []),
                "data_mode": "API_AUTHENTICATED",
                "execution": "MANUAL_ONLY",
                "note": "Authentication passed. Market data access must be tested separately."
            }

        except Exception as exc:
            return {
                "connected": False,
                "authentication": "FAILED",
                "error_type": type(exc).__name__,
                "note": "Check API subscription, token validity and Groww API access."
            }

    def get_historical_candles(
        self,
        groww_symbol,
        segment="CASH",
        days=5
    ):
        if segment not in ("CASH", "FNO"):
            raise ValueError("segment must be CASH or FNO")

        if not groww_symbol.startswith("NSE-"):
            raise ValueError("Use a valid NSE Groww symbol, e.g. NSE-RELIANCE")

        if not 1 <= int(days) <= 15:
            raise ValueError("days must be between 1 and 15")

        groww = self._get_client()

        now = datetime.now(
            timezone.utc
        ).astimezone(ZoneInfo("Asia/Kolkata"))

        end_time = now.strftime("%Y-%m-%d %H:%M:%S")
        start_time = (
            now - timedelta(days=int(days))
        ).strftime("%Y-%m-%d %H:%M:%S")

        candles = groww.get_historical_candles(
            exchange=groww.EXCHANGE_NSE,
            segment=(
                groww.SEGMENT_FNO
                if segment == "FNO"
                else groww.SEGMENT_CASH
            ),
            groww_symbol=groww_symbol,
            start_time=start_time,
            end_time=end_time,
            candle_interval=groww.CANDLE_INTERVAL_MIN_5
        )

        return {
            "mode": "GROWW_HISTORICAL",
            "symbol": groww_symbol,
            "segment": segment,
            "timeframe": "5m",
            "candles": candles.get("candles", []),
            "count": len(candles.get("candles", [])),
            "note": "Historical candle response; not an automatic trading signal."
        }

    def get_quote(self, trading_symbol, segment="CASH"):
        if segment not in ("CASH", "FNO"):
            raise ValueError("segment must be CASH or FNO")

        groww = self._get_client()

        quote = groww.get_quote(
            exchange=groww.EXCHANGE_NSE,
            segment=(
                groww.SEGMENT_FNO
                if segment == "FNO"
                else groww.SEGMENT_CASH
            ),
            trading_symbol=trading_symbol
        )

        return {
            "mode": "GROWW_QUOTE",
            "symbol": trading_symbol,
            "segment": segment,
            "quote": quote
        }
