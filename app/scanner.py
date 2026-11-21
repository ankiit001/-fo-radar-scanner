def _clamp(n, low=0, high=100):
    return max(low, min(high, n))

def score_rows(rows):
    results = []
    for row in rows:
        direction = str(row.get("direction", "BUY")).upper()
        is_buy = direction == "BUY"
        close, e34, e50, e200, vwap = (float(row[k]) for k in ("close","ema34","ema50","ema200","vwap"))
        vol, avgvol = float(row["volume"]), max(float(row["avg_volume20"]), 1.0)
        rsi, adx = float(row["rsi"]), float(row["adx"])

        trend = (e34 > e50 > e200) if is_buy else (e34 < e50 < e200)
        vwap_ok = close > vwap if is_buy else close < vwap
        breakout = close > float(row["prev_high"]) if is_buy else close < float(row["prev_low"])
        volume_ratio = vol / avgvol

        # Transparent rule score. It is a ranking heuristic, not a probability or guarantee.
        score = 0
        score += 25 if trend else 0
        score += 20 if vwap_ok else 0
        score += 20 if breakout else 0
        score += 20 if volume_ratio > 1.0 else round(20 * volume_ratio)
        score += 15 if 50 <= rsi <= 70 and is_buy or 30 <= rsi <= 50 and not is_buy else 0
        score = _clamp(score)

        reasons = []
        if trend: reasons.append("EMA trend aligned")
        if vwap_ok: reasons.append("Price on correct side of VWAP")
        if breakout: reasons.append("Previous candle level broken")
        if volume_ratio > 1: reasons.append("Volume above 20-bar average")
        if adx >= 20: reasons.append("ADX trend-strength filter passed")
        status = "WATCH" if score >= 60 and adx >= 20 else "NO_TRADE"

        results.append({
            "symbol": row["symbol"],
            "direction": direction,
            "score": score,
            "status": status,
            "close": close,
            "volume_ratio": round(volume_ratio, 2),
            "rsi": rsi,
            "adx": adx,
            "reasons": reasons,
            "risk_note": "Entry/SL/Target must be calculated from verified candles; no order is placed."
        })
    return sorted(results, key=lambda x: x["score"], reverse=True)
