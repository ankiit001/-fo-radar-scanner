import os
import requests


class SahiClient:
    def __init__(self):
        self.api_key = os.getenv("SAHI_API_KEY", "").strip()
        self.base_url = "https://api.sahi.com"

    def status(self):
        if not self.api_key:
            return {
                "connected": False,
                "reason": "SAHI_API_KEY not configured"
            }

        return {
            "connected": False,
            "broker": "Sahi",
            "authentication": "NOT_TESTED",
            "execution": "MANUAL_ONLY",
            "note": "Official Sahi API endpoint and authentication must be configured."
        }
