from __future__ import annotations

import json
from datetime import datetime, timezone

from google.adk.agents.llm_agent import Agent
from google.adk.tools.tool_context import ToolContext

from pathlib import Path
from typing import Any

from meridian_ops.tools.oms import get_order as oms_get_order

POLICY = (Path(__file__).parent / "policy.md").read_text()

def get_order(order_id: str, tool_context: ToolContext) -> dict[str, Any]:
    """Fetch order and remember it as the session's active order.

    Args:
        order_id: Meridian order id like MC-1048292.
        tool_context: Injected by ADK; do not pass manually.
    """
    result = oms_get_order(order_id)
    if result["status"] == "success":
        tool_context.state["active_order_id"] = order_id
        tool_context.state["active_lifecycle"] = result["order"]["lifecycle"]
    return result

def recall_active_order(tool_context: ToolContext) -> dict[str, Any]:
    """Return the active order id stored in session state, if any."""
    order_id = tool_context.state.get("active_order_id")
    if not order_id:
        return {
            "status": "error",
            "error_code": "NO_ACTIVE_ORDER",
            "message": "No active_order_id in session state",
        }
    return {"status": "success", "active_order_id": order_id}


def before_agent_call(callback_context) -> None:
    """Before agent call hook."""
    last_call_time = datetime.now(timezone.utc).isoformat()
    callback_context.state["last_call_time"] = last_call_time
    print(
        json.dumps(
            {
                "event": "before_agent_call",
                "message": "Before agent call",
                "last_call_time": last_call_time,
            },
            indent=2,
        ),
        flush=True,
    )


root_agent = Agent(
    name="meridian_order_status",
    model="gemini-3.5-flash",
    description="Answers Meridian WISMO questions using OMS order lookup.",
    instruction= POLICY + 
    """
Session rules:
- After a successful get_order, active_order_id is stored in state.
- If the user says "that order" or omits the id, call recall_active_order, then get_order.
""".strip(),
    tools=[get_order, recall_active_order],
    before_agent_callback=before_agent_call,
)
