
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

    def get_historical_candles(self, groww_symbol, segment="CASH", days=5):
        if segment not in ("CASH", "FNO"):
            raise ValueError("segment must be CASH or FNO")

        if not groww_symbol.startswith("NSE-"):
            raise ValueError("Use a valid NSE Groww symbol")

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

        rows = candles.get("candles", [])

        return {
            "mode": "GROWW_HISTORICAL",
            "symbol": groww_symbol,
            "segment": segment,
            "timeframe": "5m",
            "candles": rows,
            "count": len(rows),
            "note": "Historical candles only; not an automatic trading signal."
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
