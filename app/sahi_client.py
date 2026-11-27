
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
            raise RuntimeError(
                "SAHI_KEY_ID or SAHI_SECRET is missing"
            )

        if self._api is None:
            self._api = SahiAPI.from_credentials(
                key_id=self.key_id,
                secret=self.secret
            )

        return self._api

    def status(self):

        try:
            api = self._get_client()
            profile = api.get_profile()

            return {
                "connected": True,
                "authentication": "SUCCESS",
                "broker": "Sahi",
                "data_mode": "API_AUTHENTICATED",
                "execution": "MANUAL_ONLY",
                "profile": profile
            }

        except Exception as exc:
            logger.exception("Sahi authentication failed")

            return {
                "connected": False,
                "authentication": "FAILED",
                "broker": "Sahi",
                "error_type": type(exc).__name__,
                "execution": "MANUAL_ONLY"
            }
