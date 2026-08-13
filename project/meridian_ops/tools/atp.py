from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

from meridian_ops.tools.logging_utils import log_tool_event, new_correlation_id

_INV = Path(__file__).resolve().parents[1] / "fixtures" / "inventory.json"


def _load() -> dict[str, dict[str, Any]]:
    return json.loads(_INV.read_text())


async def get_atp(sku: str, store_id: str = "ST-221") -> dict[str, Any]:
    """Get available-to-promise quantity for a SKU at a store.

    Args:
        sku: Meridian SKU, digits only in this lab.
        store_id: Store id like ST-221.
    """
    corr = new_correlation_id()
    log_tool_event(tool="get_atp", correlation_id=corr, sku=sku, store_id=store_id)
    if not sku.isdigit():
        log_tool_event(
            tool="get_atp",
            correlation_id=corr,
            level="WARN",
            error_code="INVALID_SKU",
        )
        return {
            "status": "error",
            "error_code": "INVALID_SKU",
            "message": "sku must be numeric",
            "correlation_id": corr,
        }

    await asyncio.sleep(0.05)  # stand-in for network I/O
    row = _load().get(sku)
    if not row or row.get("store_id") != store_id:
        return {
            "status": "error",
            "error_code": "SKU_NOT_FOUND",
            "message": f"No ATP row for {sku} at {store_id}",
            "correlation_id": corr,
        }
    return {
        "status": "success",
        "correlation_id": corr,
        "sku": sku,
        "store_id": store_id,
        "atp_qty": row["atp_qty"],
        "name": row["name"],
    }


async def reserve_substitute(
    order_id: str,
    sku: str,
    substitute_sku: str,
    dry_run: bool = True,
) -> dict[str, Any]:
    """Preview or commit a substitute reservation for a shorted line.

    Args:
        order_id: Order id MC-...
        sku: Original SKU.
        substitute_sku: Replacement SKU.
        dry_run: When True (default), do not commit a reservation.
    """
    corr = new_correlation_id()
    if substitute_sku == sku:
        return {
            "status": "error",
            "error_code": "NOOP_SUBSTITUTE",
            "message": "substitute_sku must differ",
            "correlation_id": corr,
        }

    original = await get_atp(sku)
    replacement = await get_atp(substitute_sku)
    if original.get("status") != "success" or replacement.get("status") != "success":
        return {
            "status": "error",
            "error_code": "ATP_LOOKUP_FAILED",
            "message": "Could not load ATP for sku/substitute",
            "correlation_id": corr,
            "original": original,
            "replacement": replacement,
        }
    if replacement["atp_qty"] <= 0:
        return {
            "status": "error",
            "error_code": "SUBSTITUTE_OUT_OF_STOCK",
            "message": "substitute has atp_qty <= 0",
            "correlation_id": corr,
        }

    reservation_id = None if dry_run else f"RSV-{order_id}-{substitute_sku}"
    log_tool_event(
        tool="reserve_substitute",
        correlation_id=corr,
        dry_run=dry_run,
        reservation_id=reservation_id,
    )
    return {
        "status": "success",
        "correlation_id": corr,
        "order_id": order_id,
        "sku": sku,
        "substitute_sku": substitute_sku,
        "dry_run": dry_run,
        "reservation_id": reservation_id,
        "substitute_atp_qty": replacement["atp_qty"],
    }

async def suggest_substitute_for_short(
    order_id: str,
    sku: str,
    candidate_skus: list[str],
) -> dict[str, Any]:
    """Read ATP for original + candidates; preview-reserve the first in-stock alt.

    Args:
        order_id: Order needing a substitute.
        sku: Shorted SKU.
        candidate_skus: Ranked candidate SKUs.
    """
    corr = new_correlation_id()
    original = await get_atp(sku)
    if original.get("status") != "success":
        return {**original, "correlation_id": corr}
    if original["atp_qty"] > 0:
        return {
            "status": "success",
            "correlation_id": corr,
            "action": "NO_SUBSTITUTE_NEEDED",
            "original": original,
        }

    attempts: list[dict[str, Any]] = []
    for candidate in candidate_skus:
        preview = await reserve_substitute(order_id, sku, candidate, dry_run=True)
        attempts.append(preview)
        if preview.get("status") == "success":
            return {
                "status": "success",
                "correlation_id": corr,
                "action": "PREVIEW_RESERVE",
                "chosen_substitute": candidate,
                "preview": preview,
                "attempts": attempts,
            }

    return {
        "status": "error",
        "error_code": "NO_VIABLE_SUBSTITUTE",
        "correlation_id": corr,
        "attempts": attempts,
    }