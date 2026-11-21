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
