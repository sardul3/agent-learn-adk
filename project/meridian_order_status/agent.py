from __future__ import annotations

from google.adk.agents.llm_agent import Agent

from typing import Any


_ORDERS: dict[str, dict[str, Any]] = {
    "MC-1048292": {
        "order_id": "MC-1048292",
        "customer_id": "C-44102",
        "lifecycle": "delivered",
        "promised_window_local": "2026-08-10T16:00-18:00",
        "delivered_at_local": "2026-08-10T17:12:00",
        "pod_photo_present": False,
        "shipping_address_city": "Austin",
        "line_count": 14,
    },
    "MC-1048301": {
        "order_id": "MC-1048301",
        "customer_id": "C-11887",
        "lifecycle": "ready_for_pickup",
        "promised_window_local": "2026-08-11T17:00-19:00",
        "delivered_at_local": None,
        "pod_photo_present": False,
        "shipping_address_city": "Austin",
        "line_count": 6,
    },
}


def get_order(order_id: str) -> dict[str, Any]:
    """Look up a Meridian order in OMS (read-only stub).

    Args:
        order_id: Meridian order id, for example MC-1048292.

    Returns:
        A dict with status=success and order fields, or status=error.
    """
    order = _ORDERS.get(order_id.strip())
    if not order:
        return {
            "status": "error",
            "error_code": "ORDER_NOT_FOUND",
            "message": f"No order found for {order_id}",
        }
    return {"status": "success", "order": order}


root_agent = Agent(
    name="meridian_order_status",
    model="gemini-3.5-flash",
    description="Answers Meridian WISMO questions using OMS order lookup.",
    instruction="""
You are Meridian Commerce Order Status, an internal ops assistant.

Scope:
- Only answer questions about order status, ETA, delivery/pickup lifecycle.
- Refuse refunds, cancellations, password resets, and medical advice.

Tool rules:
- For any question about a specific order, you MUST call get_order before claiming facts.
- Never invent delivery scans, POD photos, or timestamps.
- If get_order returns status=error, say you cannot find the order and ask for a correct MC- id.

Style:
- Be concise and operational. Prefer bullet facts over marketing tone.
- If lifecycle is delivered but pod_photo_present is false, mention the missing POD as an investigation signal.
""".strip(),
    tools=[get_order],
)
