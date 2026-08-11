"""Policy specialist — expose via ADK to_a2a() / consume via RemoteA2aAgent."""

from google.adk.agents import LlmAgent

from meridian_ops.tools.policy_rag import retrieve_policy

root_agent = LlmAgent(
    name="meridian_policy_a2a",
    model="gemini-2.5-flash",
    description="Meridian policy QA with retrieve_policy tool.",
    instruction="""
You are Meridian Policy.
Always call retrieve_policy before stating rules.
Cite policy ids when present. Never invent credits.
""".strip(),
    tools=[retrieve_policy],
)