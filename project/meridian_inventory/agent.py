from meridian_ops.tools.atp import suggest_substitute_for_short
from meridian_ops.tools.atp import reserve_substitute
from meridian_ops.tools.atp import get_atp
from meridian_ops.tools.oms import get_order
from google.adk.agents.llm_agent import Agent

root_agent = Agent(
    model='gemini-3.5-flash',
    name='meridian_inventory',
    description='Handles Meridian inventory shorts and substitute previews.',
    instruction="""
    You are Meridian Inventory Exception agent.

    Rules:
    - Use get_order when an order_id is present.
    - Use get_atp / suggest_substitute_for_short for shortages.
    - NEVER call reserve_substitute with dry_run=false unless the user explicitly confirms.
    - Default to dry_run previews.
    - Failures must quote error_code from tools.
""".strip(),
    tools=[get_order, get_atp, reserve_substitute, suggest_substitute_for_short],
)
