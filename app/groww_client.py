import os

class GrowwClient:
    """
    Safe placeholder. No credentials are stored in source code.
    Live integration should be enabled only after an active Groww API subscription.
    """
    def __init__(self):
        self.token = os.getenv("GROWW_ACCESS_TOKEN")

    def status(self):
        if not self.token:
            return {
                "connected": False,
                "reason": "GROWW_ACCESS_TOKEN is not configured",
                "next_step": "Activate Groww Trading API subscription, generate token, then add it as a server environment secret."
            }
        return {
            "connected": False,
            "reason": "Token is present, but live-feed adapter is not enabled in this starter build.",
            "next_step": "Implement and test Groww historical 5-minute candle and live-data calls before using real signals."
        }
