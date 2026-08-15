from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from meridian_ops.tools.payments_guarded import request_refund_guarded


@dataclass
class HitlDecision:
    """Priya's click. None (no object) means she has not been asked yet."""

    approved: bool
    actor: str
    note: str


def run_refund_pipeline(
    *,
    order_id: str,
    amount_usd: float,
    reason_code: str,
    idempotency_key: str,
    hitl: HitlDecision | None,
) -> dict[str, Any]:
    """Deterministic refund pipeline used by the CLI, tests, and (later) graphs.

    1. Preview (confirm=False).
    2. If the preview is an error, stop.
    3. If HITL is required and Priya has not approved, stop.
    4. Confirm (confirm=True) with the same idempotency key.
    """
    preview = request_refund_guarded(
        order_id, amount_usd, reason_code, idempotency_key, confirm=False
    )
    if preview.get("status") != "success":
        return {"stage": "preview", "result": preview}

    if preview.get("requires_hitl"):
        if hitl is None or not hitl.approved:
            return {
                "stage": "hitl_required",
                "result": preview,
                "hitl_status": "PENDING" if hitl is None else "DENIED",
                "hitl": hitl,
            }

    final = request_refund_guarded(
        order_id, amount_usd, reason_code, idempotency_key, confirm=True
    )
    return {
        "stage": "confirmed",
        "result": final,
        "hitl": hitl,
    }