"""Native ADK critic loop — see Lesson 14."""

from __future__ import annotations

from google.adk.agents import LlmAgent
from google.adk.agents.context import Context
from google.adk.events.event import Event
from google.adk.workflow import Workflow
from google.genai import types
from pydantic import BaseModel


class CriticVerdict(BaseModel):
    status: str
    reason: str = ""


drafter = LlmAgent(
    name="drafter",
    model="gemini-2.5-flash",
    instruction="""
Draft a Meridian customer update.
Must include a 'Next step:' line.
Never say a refund was already issued unless tools proved it (they did not).
""".strip(),
    output_key="draft",
)


def critic(node_input) -> Event:
    text = node_input
    if isinstance(node_input, types.Content):
        text = " ".join((p.text or "") for p in (node_input.parts or []))
    text = str(text)
    lower = text.lower()
    if "we refunded" in lower or "refund issued" in lower:
        return Event(
            output=CriticVerdict(status="FAIL", reason="banned_refund_claim"),
            route="FAIL",
        )
    if "next step" not in lower:
        return Event(
            output=CriticVerdict(status="FAIL", reason="missing_next_step"),
            route="FAIL",
        )
    return Event(output=CriticVerdict(status="PASS"), route="PASS")


def bump_and_route(ctx: Context, node_input) -> Event:
    n = int(ctx.state.get("loop_i", 0)) + 1
    max_i = int(ctx.state.get("max_iterations", 2))
    status = getattr(node_input, "status", None) or (
        node_input.get("status") if isinstance(node_input, dict) else None
    )
    if status == "PASS":
        return Event(output=node_input, route="PASS", state={"loop_i": n})
    if n >= max_i:
        return Event(output=node_input, route="GIVE_UP", state={"loop_i": n})
    return Event(output=node_input, route="FAIL", state={"loop_i": n})


def done_pass(node_input):
    return {"result": "accepted", "critic": str(node_input)}


def done_give_up(node_input):
    return {"result": "max_iterations", "critic": str(node_input)}


root_agent = Workflow(
    name="meridian_reply_loop",
    edges=[
        ("START", drafter),
        (drafter, critic),
        (critic, bump_and_route),
        (bump_and_route, drafter, "FAIL"),
        (bump_and_route, done_pass, "PASS"),
        (bump_and_route, done_give_up, "GIVE_UP"),
    ],
)