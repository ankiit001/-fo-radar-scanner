
import os
import logging
from sahiapi import SahiAPI

logger = logging.getLogger(__name__)


class SahiClient:

    def __init__(self):
        self.key_id = os.getenv("SAHI_KEY_ID", "").strip()
        self.secret = os.getenv("SAHI_SECRET", "").strip()
        self._api = None

    def _get_client(self):

        if not self.key_id or not self.secret:
            raise RuntimeError("Sahi API credentials missing")

        if self._api is None:
            self._api = SahiAPI.from_credentials(
                key_id=self.key_id,
                secret=self.secret
            )

        return self._api

    def status(self):

        try:
            api = self._get_client()
            api.get_profile()

            return {
                "connected": True,
                "authentication": "SUCCESS",
                "broker": "Sahi",
                "message": "API authentication successful",
                "execution": "MANUAL_ONLY"
            }

        except Exception as exc:
            logger.exception("Sahi authentication failed")

            return {
                "connected": False,
                "authentication": "FAILED",
                "error_type": type(exc).__name__,
                "message": "Check API credentials, approval and permissions",
                "execution": "MANUAL_ONLY"
            }

