from google.adk.workflow import Workflow

from meridian_ops.agents.specialists import inventory_agent, order_agent, synthesizer_agent

# Fixed path for inventory-exception style tickets:
# Order evidence → Inventory recommendation → customer-safe draft
root_agent = Workflow(
    name="meridian_orderops_sequential",
    description="Deterministic Order → Inventory → Synthesize pipeline.",
    edges=[
        ("START", order_agent),
        (order_agent, inventory_agent),
        (inventory_agent, synthesizer_agent),
    ],
)
