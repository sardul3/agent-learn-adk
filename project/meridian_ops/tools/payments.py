from __future__ import annotations

from typing import Any

from meridian_ops.tools.logging_utils import log_tool_event, new_correlation_id

# Process-local idempotency store for the lab. Lesson 09 moves this to Redis.
_IDEMPOTENCY: dict[str, dict[str, Any]] = {}

HITL_THRESHOLD_USD = 75.0


def request_refund(
    order_id: str,
    amount_usd: float,
    reason_code: str,
    idempotency_key: str,
    *,
    confirm: bool = False,
) -> dict[str, Any]:
    """Create a refund *request* (not a settlement).

    Args:
        order_id: Meridian order id.
        amount_usd: Amount in USD; must be > 0.
        reason_code: Stable code such as DAMAGED_ITEM or MISSING_DELIVERY.
        idempotency_key: Required key to make retries safe.
        confirm: Must be True to open a request; False returns a preview only.
    """
    corr = new_correlation_id()
    log_tool_event(
        tool="request_refund",
        correlation_id=corr,
        order_id=order_id,
        amount_usd=amount_usd,
        confirm=confirm,
    )

    if amount_usd <= 0:
        return {
            "status": "error",
            "error_code": "INVALID_AMOUNT",
            "correlation_id": corr,
        }
    if not idempotency_key:
        return {
            "status": "error",
            "error_code": "MISSING_IDEMPOTENCY_KEY",
            "correlation_id": corr,
        }
    if not reason_code:
        return {
            "status": "error",
            "error_code": "MISSING_REASON_CODE",
            "correlation_id": corr,
        }

    if not confirm:
        return {
            "status": "success",
            "preview": True,
            "order_id": order_id,
            "amount_usd": amount_usd,
            "reason_code": reason_code,
            "requires_hitl": amount_usd > HITL_THRESHOLD_USD,
            "correlation_id": corr,
            "message": "Pass confirm=true to open the refund request",
        }

    if idempotency_key in _IDEMPOTENCY:
        prior = _IDEMPOTENCY[idempotency_key]
        log_tool_event(
            tool="request_refund",
            correlation_id=corr,
            level="INFO",
            replay=True,
            refund_request_id=prior["refund_request_id"],
        )
        return {**prior, "replayed": True, "correlation_id": corr}

    requires_hitl = amount_usd > HITL_THRESHOLD_USD
    payload = {
        "status": "success",
        "preview": False,
        "order_id": order_id,
        "amount_usd": amount_usd,
        "reason_code": reason_code,
        "idempotency_key": idempotency_key,
        "refund_request_id": f"RFQ-{idempotency_key[:8]}",
        "requires_hitl": requires_hitl,
        "request_status": "PENDING_HITL" if requires_hitl else "AUTO_APPROVED_LAB_ONLY",
    }
    _IDEMPOTENCY[idempotency_key] = payload
    return {**payload, "correlation_id": corr}