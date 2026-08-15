from __future__ import annotations

from typing import Any

from meridian_ops.safety.validators import validate_refund_args
from meridian_ops.tools.payments import request_refund as _request_refund


def request_refund_guarded(
    order_id: str,
    amount_usd: float,
    reason_code: str,
    idempotency_key: str,
    confirm: bool = False,
) -> dict[str, Any]:
    """Validate, then preview or open a refund request.

    confirm=False is a preview. confirm=True is still only a *request*,
    not a bank settlement — same contract as Lesson 04.
    """
    check = validate_refund_args(
        order_id=order_id,
        amount_usd=amount_usd,
        reason_code=reason_code,
        idempotency_key=idempotency_key,
    )
    if not check["ok"]:
        return {"status": "error", **check}
    return _request_refund(
        order_id,
        amount_usd,
        reason_code,
        idempotency_key,
        confirm=confirm,
    )