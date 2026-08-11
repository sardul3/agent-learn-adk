from __future__ import annotations

from typing import Any

HITL_THRESHOLD_USD = 75.0
_IDEMPOTENCY: dict[str, dict[str, Any]] = {}


def request_refund_guarded(
    order_id: str,
    amount_usd: float,
    reason_code: str,
    idempotency_key: str,
    confirm: bool = False,
) -> dict[str, Any]:
    """Preview or open a refund request (domain tool — used by MCP preview only)."""
    allowed = {"DAMAGED_ITEM", "MISSING_DELIVERY", "LATE_DELIVERY_CREDIT", "WRONG_ITEM"}
    if amount_usd <= 0:
        return {"status": "error", "error_code": "INVALID_AMOUNT"}
    if not idempotency_key:
        return {"status": "error", "error_code": "MISSING_IDEMPOTENCY_KEY"}
    if reason_code not in allowed:
        return {"status": "error", "error_code": "REASON_NOT_ALLOWED"}
    if not confirm:
        return {
            "status": "success",
            "preview": True,
            "order_id": order_id,
            "amount_usd": amount_usd,
            "reason_code": reason_code,
            "requires_hitl": amount_usd > HITL_THRESHOLD_USD,
        }
    if idempotency_key in _IDEMPOTENCY:
        return {**_IDEMPOTENCY[idempotency_key], "replayed": True}
    payload = {
        "status": "success",
        "preview": False,
        "order_id": order_id,
        "amount_usd": amount_usd,
        "reason_code": reason_code,
        "idempotency_key": idempotency_key,
        "refund_request_id": f"RFQ-{idempotency_key[:8]}",
        "requires_hitl": amount_usd > HITL_THRESHOLD_USD,
        "request_status": (
            "PENDING_HITL" if amount_usd > HITL_THRESHOLD_USD else "AUTO_APPROVED_LAB_ONLY"
        ),
    }
    _IDEMPOTENCY[idempotency_key] = payload
    return payload