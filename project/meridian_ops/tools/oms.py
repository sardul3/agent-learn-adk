from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_ORDERS_PATH = Path(__file__).resolve().parents[1] / "fixtures" / "orders.json"


def get_order(order_id: str) -> dict[str, Any]:
    """Look up a Meridian order in OMS (fixture-backed).

    Args:
        order_id: Meridian order id, for example MC-1048292.
    """
    orders = json.loads(_ORDERS_PATH.read_text())
    order = orders.get(order_id.strip())
    if not order:
        return {
            "status": "error",
            "error_code": "ORDER_NOT_FOUND",
            "message": f"No order found for {order_id}",
        }
    return {"status": "success", "order": order}