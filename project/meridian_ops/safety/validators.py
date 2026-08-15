from __future__ import annotations

from typing import Any

ALLOWED_REASON_CODES: set[str] = {
    "DAMAGED_ITEM",
    "MISSING_DELIVERY",
    "LATE_DELIVERY_CREDIT",
    "WRONG_ITEM",
}


def validate_refund_args(
    *,
    order_id: str,
    amount_usd: float,
    reason_code: str,
    idempotency_key: str,
) -> dict[str, Any]:
    """Return ok=True or an error_code. Never raises — the tool contract is a dict."""
    if not order_id.startswith("MC-"):
        return {"ok": False, "error_code": "INVALID_ORDER_ID"}
    if amount_usd <= 0 or amount_usd > 500:
        return {"ok": False, "error_code": "AMOUNT_OUT_OF_RANGE"}
    if reason_code not in ALLOWED_REASON_CODES:
        return {"ok": False, "error_code": "REASON_NOT_ALLOWED"}
    if len(idempotency_key) < 6:
        return {"ok": False, "error_code": "WEAK_IDEMPOTENCY_KEY"}
    return {"ok": True}