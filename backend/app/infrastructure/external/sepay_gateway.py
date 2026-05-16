"""SePay payment gateway — HMAC-SHA256 webhook signature verification."""
import hashlib
import hmac
import logging

from app.application.ports.payment_port import IPaymentPort
from app.config import settings

logger = logging.getLogger(__name__)


class SePayGateway(IPaymentPort):
    """Verify HMAC-SHA256 signature từ SePay webhook.

    SePay gửi header `Authorization: Apikey <secret>` hoặc `X-Signature: <hex_sha256>`.
    Chúng ta chọn cách HMAC: hex(HMAC_SHA256(secret, body)) == signature.
    """

    def __init__(self, webhook_secret: str | None = None):
        self._secret = (webhook_secret or settings.sepay_webhook_secret).encode("utf-8")

    def verify_webhook_signature(self, body: bytes, signature: str) -> bool:
        if not self._secret:
            logger.error("SEPAY_WEBHOOK_SECRET chưa được cấu hình.")
            return False
        if not signature:
            return False

        # Strip prefix nếu SePay gửi "sha256=..." style
        sig = signature.strip()
        if sig.startswith("sha256="):
            sig = sig[len("sha256="):]

        expected = hmac.new(self._secret, body, hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, sig)
