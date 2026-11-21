except Exception as exc:
    raise HTTPException(
        status_code=502,
        detail=f"Groww quote request failed: {type(exc).__name__}"
    )
