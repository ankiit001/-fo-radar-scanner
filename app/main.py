except Exception as exc:
    raise HTTPException(
        status_code=502,
        detail={
            "error_type": type(exc).__name__,
            "error_code": getattr(exc, "code", None),
            "error_message": getattr(exc, "msg", str(exc))
        }
    )
