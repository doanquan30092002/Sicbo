from abc import ABC, abstractmethod


class IPaymentPort(ABC):
    @abstractmethod
    def verify_webhook_signature(self, body: bytes, signature: str) -> bool:
        """Verify HMAC-SHA256 signature từ SePay webhook."""
        ...
