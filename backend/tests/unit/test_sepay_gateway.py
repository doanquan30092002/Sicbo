"""Unit tests cho SePayGateway HMAC verification."""
import hashlib
import hmac

from app.infrastructure.external.sepay_gateway import SePayGateway


class TestSePayGateway:
    def test_valid_signature_verifies(self):
        secret = "my-test-secret-1234567890"
        body = b'{"amount": 100000, "transfer_content": "NAP001123"}'
        sig = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()

        gw = SePayGateway(webhook_secret=secret)
        assert gw.verify_webhook_signature(body, sig) is True

    def test_signature_with_sha256_prefix_accepted(self):
        secret = "my-test-secret"
        body = b'{"foo": "bar"}'
        sig = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()

        gw = SePayGateway(webhook_secret=secret)
        assert gw.verify_webhook_signature(body, sig) is True

    def test_invalid_signature_rejected(self):
        gw = SePayGateway(webhook_secret="some-secret")
        assert gw.verify_webhook_signature(b'{"x": 1}', "deadbeef") is False

    def test_empty_signature_rejected(self):
        gw = SePayGateway(webhook_secret="some-secret")
        assert gw.verify_webhook_signature(b'{"x": 1}', "") is False

    def test_no_secret_configured_returns_false(self):
        gw = SePayGateway(webhook_secret="")
        assert gw.verify_webhook_signature(b'{"x": 1}', "anything") is False

    def test_tampered_body_rejected(self):
        secret = "my-test-secret"
        body = b'{"amount": 100000}'
        sig = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()

        gw = SePayGateway(webhook_secret=secret)
        tampered = b'{"amount": 999999}'
        assert gw.verify_webhook_signature(tampered, sig) is False
