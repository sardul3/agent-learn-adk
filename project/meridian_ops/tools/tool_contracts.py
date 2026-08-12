from __future__ import annotations

from typing import Any


def get_order(order_id: str) -> dict[str, Any]:
    """Fetch an order by Meridian order id (read-only).

    Args:
        order_id: Order id like MC-1048292.

    Returns:
        status/success payload or status/error with error_code.
    """
    if not order_id or not order_id.startswith("MC-"):
        return {
            "status": "error",
            "error_code": "INVALID_ORDER_ID",
            "message": "order_id must look like MC-#######",
        }
    return {
        "status": "success",
        "order_id": order_id,
        "lifecycle": "out_for_delivery",
        "eta_local": "2026-08-10T18:30:00",
    }


def reserve_substitute(
    order_id: str,
    sku: str,
    substitute_sku: str,
    dry_run: bool = True,
) -> dict[str, Any]:
    """Reserve a substitute SKU for a shorted line (side-effectful).

    Args:
        order_id: Meridian order id.
        sku: Original SKU that is short.
        substitute_sku: Replacement SKU.
        dry_run: If True, validate only — do not write.

    Returns:
        Structured success/error. Retries must use the same logical request.
    """
    if not dry_run and substitute_sku == sku:
        return {
            "status": "error",
            "error_code": "NOOP_SUBSTITUTE",
            "message": "substitute_sku must differ from sku",
        }
    return {
        "status": "success",
        "order_id": order_id,
        "sku": sku,
        "substitute_sku": substitute_sku,
        "dry_run": dry_run,
        "reservation_id": None if dry_run else f"RSV-{order_id}-{substitute_sku}",
    }


def request_refund(
    order_id: str,
    amount_usd: float,
    reason_code: str,
    idempotency_key: str,
) -> dict[str, Any]:
    """Open a refund request (never silently succeeds without a key).

    Args:
        order_id: Meridian order id.
        amount_usd: Dollars to refund; must be > 0.
        reason_code: Stable code like DAMAGED_ITEM.
        idempotency_key: Client-generated key to prevent double refunds.

    Returns:
        success with refund_request_id, or error_code.
    """
    if amount_usd <= 0:
        return {
            "status": "error",
            "error_code": "INVALID_AMOUNT",
            "message": "amount_usd must be > 0",
        }
    if not idempotency_key:
        return {
            "status": "error",
            "error_code": "MISSING_IDEMPOTENCY_KEY",
            "message": "idempotency_key is required for refunds",
        }
    return {
        "status": "success",
        "order_id": order_id,
        "amount_usd": amount_usd,
        "reason_code": reason_code,
        "idempotency_key": idempotency_key,
        "refund_request_id": f"RFQ-{idempotency_key[:8]}",
        "requires_hitl": amount_usd > 75.0,
    }