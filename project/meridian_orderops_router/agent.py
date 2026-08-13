from google.adk.tools import transfer_to_agent_tool
from google.adk.agents.llm_agent import LlmAgent

from meridian_ops.agents.specialists import inventory_agent, order_agent
from meridian_ops.tools.classify_ticket import Route, classify_ticket

GEMINI = "gemini-3.5-flash"


def classify_for_router(text: str) -> dict:
    """Deterministic assist for the coordinator (not the final authority alone)."""
    route = classify_ticket(text)
    return {"status": "success", "route": route.value}


router_agent = LlmAgent(
    name="orderops_router",
    model=GEMINI,
    description="Routes Meridian OrderOps tickets to specialists.",
    instruction="""
You are the Meridian OrderOps coordinator.

Process:
1) Call classify_for_router on the user text.
2) Transfer to order_agent for WISMO / lifecycle questions.
3) Transfer to inventory_agent for ATP / substitute / shortage questions.
4) If both are required, prefer inventory_agent only after order_id is known —
   transfer to order_agent first when order facts are missing.
5) Refuse loyalty batch jobs and password resets.

Use agent transfer/handoff mechanisms available to you via the transfer_to_agent_tool rather than answering
with deep OMS expertise yourself.
""".strip(),
    tools=[classify_for_router],
    sub_agents=[order_agent, inventory_agent, transfer_to_agent_tool],
)

root_agent = router_agent