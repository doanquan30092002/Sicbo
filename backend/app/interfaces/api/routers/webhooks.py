"""Webhooks router — SePay payment webhook (public endpoint, HMAC-verified)."""
import logging
import re

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status

from app.application.use_cases.wallet.confirm_deposit import (
    ConfirmDeposit,
    DepositAlreadyConfirmedError,
)
from app.infrastructure.external.sepay_gateway import SePayGateway
from app.interfaces.api.dependencies import (
    get_confirm_deposit_uc,
    get_sepay_gateway,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])

NAP_CODE_RE = re.compile(r"(NAP\d{3,9})", re.IGNORECASE)


def _extract_transfer_content(content: str) -> str | None:
    if not content:
        return None
    m = NAP_CODE_RE.search(content)
    return m.group(1).upper() if m else None


@router.post("/sepay", status_code=status.HTTP_200_OK)
async def sepay_webhook(
    request: Request,
    x_signature: str | None = Header(default=None, alias="X-Signature"),
    authorization: str | None = Header(default=None, alias="Authorization"),
    gateway: SePayGateway = Depends(get_sepay_gateway),
    uc: ConfirmDeposit = Depends(get_confirm_deposit_uc),
):
    body = await request.body()

    # SePay free tier hỗ trợ 2 cách: API key qua Authorization, hoặc HMAC qua X-Signature.
    # Verify HMAC trước — nếu không có thì check Apikey.
    verified = False
    if x_signature:
        verified = gateway.verify_webhook_signature(body, x_signature)
    elif authorization:
        from app.config import settings as _s
        token = authorization.strip()
        if token.lower().startswith("apikey "):
            token = token[len("Apikey "):].strip()
        verified = bool(_s.sepay_webhook_secret) and (token == _s.sepay_webhook_secret)

    if not verified:
        logger.warning("SePay webhook: signature/apikey không hợp lệ.")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid signature")

    try:
        payload = await request.json()
    except Exception as e:
        logger.error(f"SePay webhook: body không phải JSON hợp lệ: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid JSON")

    transfer_type = (payload.get("transferType") or "").lower()
    if transfer_type != "in":
        logger.info(f"SePay webhook: bỏ qua giao dịch {transfer_type} (chỉ xử lý 'in').")
        return {"success": True, "skipped": True, "reason": "not incoming"}

    content = payload.get("content") or payload.get("description") or ""
    transfer_content = _extract_transfer_content(content)
    if not transfer_content:
        logger.warning(f"SePay webhook: không tìm thấy mã NAP trong content='{content}'.")
        return {"success": True, "skipped": True, "reason": "no NAP code"}

    raw_amount = payload.get("transferAmount") or payload.get("amount") or 0
    from decimal import Decimal
    try:
        amount = Decimal(str(raw_amount))
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid amount")

    sepay_tx_id = str(
        payload.get("id")
        or payload.get("referenceCode")
        or payload.get("transactionDate", "")
    )

    try:
        deposit = await uc.execute(
            transfer_content=transfer_content,
            amount=amount,
            sepay_transaction_id=sepay_tx_id,
        )
    except DepositAlreadyConfirmedError as e:
        logger.info(f"SePay webhook: deposit đã confirm trước đó — {e}")
        return {"success": True, "skipped": True, "reason": "already confirmed"}
    except Exception as e:
        logger.exception(f"SePay webhook: lỗi khi confirm deposit: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Confirm failed")

    if deposit is None:
        logger.warning(f"SePay webhook: không tìm thấy deposit cho mã '{transfer_content}'.")
        return {"success": True, "skipped": True, "reason": "deposit not found"}

    return {
        "success": True,
        "deposit_id": deposit.id,
        "transfer_content": transfer_content,
        "amount": str(amount),
    }
