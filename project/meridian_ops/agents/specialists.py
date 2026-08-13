from __future__ import annotations

from google.adk.agents.llm_agent import LlmAgent

from meridian_ops.tools.atp import get_atp, reserve_substitute, suggest_substitute_for_short
from meridian_ops.tools.oms import get_order

GEMINI = "gemini-3.5-flash"

order_agent = LlmAgent(
    name="order_agent",
    model=GEMINI,
    description="Meridian order status and delivery/pickup lifecycle specialist.",
    instruction="""
You are Meridian Order specialist.
- Use get_order before factual claims.
- Write concise evidence bullets into your final response.
- Do not discuss refunds or substitutes beyond noting the customer asked.
- If the issue is clearly an inventory short, say so and stop — the router may transfer.
""".strip(),
    tools=[get_order],
    output_key="order_findings",
)

inventory_agent = LlmAgent(
    name="inventory_agent",
    model=GEMINI,
    description="Meridian ATP shortage and substitute preview specialist.",
    instruction="""
You are Meridian Inventory specialist.
- Use get_atp / suggest_substitute_for_short for shortages.
- Default dry_run=true; never commit reserves unless user confirms.
- Put the chosen substitute and correlation ids in your final response.
- No refunds.
""".strip(),
    tools=[get_atp, reserve_substitute, suggest_substitute_for_short],
    output_key="inventory_findings",
)

synthesizer_agent = LlmAgent(
    name="synthesizer_agent",
    model=GEMINI,
    description="Drafts a customer-safe Meridian reply from specialist findings.",
    instruction="""
You draft customer-safe replies for Meridian CX.

Inputs in session state (may be empty):
- order_findings: {order_findings?}
- inventory_findings: {inventory_findings?}

Rules:
- Only use facts present in those findings or tool-backed earlier turns.
- Never invent refunds, ETAs, or POD photos.
- Structure: Empathy (1 line) → Facts → Next step → What we need from customer.
""".strip(),
    tools=[],  # pure drafting from state
    output_key="customer_reply_draft",
)