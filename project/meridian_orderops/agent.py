"""Meridian OrderOps — native ADK 2.x Workflow (no custom graph engine).

Requires: google-adk >= 2.0, Python >= 3.11
"""

from __future__ import annotations

import re
from typing import Any

from google.adk.agents import LlmAgent
from google.adk.agents.context import Context
from google.adk.events.event import Event
from google.adk.events.request_input import RequestInput
from google.adk.workflow import JoinNode, Workflow
from google.genai import types
from pydantic import BaseModel, Field

from meridian_ops.tools.oms import get_order

GEMINI = "gemini-2.5-flash"


class RouteDecision(BaseModel):
    route: str = Field(description="WISMO | SHORTAGE | REFUND | POLICY | UNSUPPORTED")
    order_id: str | None = None


class OrderFindings(BaseModel):
    order_id: str | None = None
    lifecycle: str | None = None
    pod_photo_present: bool | None = None
    raw_status: str = "unknown"
    route: str = "WISMO"


def _text_from_start(node_input: Any) -> str:
    if isinstance(node_input, types.Content):
        parts = node_input.parts or []
        return " ".join(getattr(p, "text", "") or "" for p in parts).strip()
    return str(node_input)


def route_ticket(node_input: Any) -> Event:
    """Deterministic router — path law lives in code, not in a prompt."""
    text = _text_from_start(node_input)
    lower = text.lower()
    m = re.search(r"(MC-\d+)", text)
    order_id = m.group(1) if m else None

    if re.search(r"\brecompute\b|\bnightly\b|\bsegment\b", lower):
        route = "UNSUPPORTED"
    elif "refund" in lower:
        route = "REFUND"
    elif re.search(r"\batp\b|\bsku\b|\bsubstitute\b|\bshorted\b", lower):
        route = "SHORTAGE"
    elif "policy" in lower and "refund" not in lower:
        route = "POLICY"
    else:
        route = "WISMO"

    decision = RouteDecision(route=route, order_id=order_id)
    return Event(
        output=decision,
        route=route,
        state={"route_decision": decision.model_dump(), "active_order_id": order_id},
    )


def lookup_order(ctx: Context, node_input: RouteDecision | dict[str, Any]) -> Event:
    data = node_input if isinstance(node_input, RouteDecision) else RouteDecision(**node_input)
    route = data.route
    if not data.order_id:
        findings = OrderFindings(raw_status="MISSING_ORDER_ID", route=route)
        return Event(output=findings, route=route)

    result = get_order(data.order_id)
    if result.get("status") != "success":
        findings = OrderFindings(
            order_id=data.order_id,
            raw_status=str(result.get("error_code", "ERROR")),
            route=route,
        )
        return Event(output=findings, route=route)

    order = result["order"]
    findings = OrderFindings(
        order_id=order.get("order_id"),
        lifecycle=order.get("lifecycle"),
        pod_photo_present=order.get("pod_photo_present"),
        raw_status="success",
        route=route,
    )
    return Event(
        output=findings,
        route=route,
        state={"order_findings": findings.model_dump()},
    )


_ORDER_INSTR = """
You are Meridian Order Status.
Use only the structured order findings provided as input.
Never invent POD photos, refunds, or timestamps.
If pod_photo_present is false on a delivered order, say so and propose a next step.
""".strip()

order_narrator = LlmAgent(
    name="order_narrator",
    model=GEMINI,
    description="Turns OMS findings into concise ops bullets.",
    instruction=_ORDER_INSTR,
    output_key="order_narrative",
)

# Separate instance — ADK graphs require unique node names when fan-out/reuse.
order_narrator_shortage = LlmAgent(
    name="order_narrator_shortage",
    model=GEMINI,
    description="Order findings for shortage path.",
    instruction=_ORDER_INSTR,
    output_key="order_narrative",
)

inventory_agent = LlmAgent(
    name="inventory_agent",
    model=GEMINI,
    description="Shortage / substitute guidance (preview only).",
    instruction="""
You are Meridian Inventory.
Given order findings, discuss shortage handling.
Do not claim a reservation was committed. Prefer dry-run / preview language.
""".strip(),
    output_key="inventory_narrative",
)

policy_agent = LlmAgent(
    name="policy_agent",
    model=GEMINI,
    description="Policy FAQ narrator.",
    instruction="""
Answer Meridian policy questions cautiously.
If you lack retrieved policy text, say you cannot cite a policy id.
Never invent dollar credits.
""".strip(),
    output_key="policy_narrative",
)

synthesizer = LlmAgent(
    name="synthesizer",
    model=GEMINI,
    description="Customer-safe final reply.",
    instruction="""
Draft a customer-safe Meridian reply from prior findings/narratives.
Structure: Empathy → Facts → Next step.
Never claim a refund completed.
""".strip(),
    output_key="customer_reply_draft",
)


async def hitl_refund_gate(node_input: Any):
    """Native ADK HITL — RequestInput pause/resume (not a DIY checkpoint DB)."""
    yield RequestInput(
        message=(
            "Refund requires supervisor approval. "
            "Reply with APPROVE or DENY and a short note."
        ),
        payload={"order_findings": str(node_input)},
    )


def refund_finalize(node_input: Any) -> Event:
    """Code-only post-HITL decision."""
    text = _text_from_start(node_input).strip().upper()
    approved = text.startswith("APPROVE")
    out = {
        "hitl_approved": approved,
        "hitl_raw": _text_from_start(node_input),
        "request_status": "CONFIRMED_LAB" if approved else "DENIED",
    }
    return Event(output=out, state={"refund_decision": out})


def unsupported_msg(_: Any) -> dict[str, str]:
    return {"customer_reply_draft": "This request is out of scope for Meridian OrderOps agents."}


join_shortage = JoinNode(name="join_shortage")

root_agent = Workflow(
    name="meridian_orderops",
    description="Native ADK OrderOps graph with HITL refund branch.",
    edges=[
        ("START", route_ticket),
        # Route → shared OMS lookup (re-emits same route)
        (route_ticket, lookup_order, "WISMO"),
        (route_ticket, lookup_order, "SHORTAGE"),
        (route_ticket, lookup_order, "REFUND"),
        (route_ticket, policy_agent, "POLICY"),
        (route_ticket, unsupported_msg, "UNSUPPORTED"),
        # WISMO
        (lookup_order, order_narrator, "WISMO"),
        (order_narrator, synthesizer),
        # SHORTAGE: fan-out narrator + inventory, join, synthesize
        (lookup_order, (order_narrator_shortage, inventory_agent), "SHORTAGE"),
        ((order_narrator_shortage, inventory_agent), join_shortage),
        (join_shortage, synthesizer),
        # REFUND: HITL then code finalize
        (lookup_order, hitl_refund_gate, "REFUND"),
        (hitl_refund_gate, refund_finalize),
        (refund_finalize, synthesizer),
        # POLICY
        (policy_agent, synthesizer),
    ],
)
