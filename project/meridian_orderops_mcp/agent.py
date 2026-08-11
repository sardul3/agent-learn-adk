"""Order Status agent that loads OMS tools via native ADK McpToolset."""

from __future__ import annotations

from pathlib import Path

from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from mcp import StdioServerParameters

_REPO_PROJECT = Path(__file__).resolve().parents[1]
_SERVER = _REPO_PROJECT / "meridian_ops" / "mcp_server" / "server.py"

root_agent = LlmAgent(
    name="meridian_orderops_mcp",
    model="gemini-2.5-flash",
    description="WISMO via MCP-exposed Meridian tools.",
    instruction="""
You are Meridian Order Status.
Use MCP tools to look up orders before stating facts.
Never invent POD photos. Refuse refunds (out of scope for this agent).
""".strip(),
    tools=[
        McpToolset(
            connection_params=StdioConnectionParams(
                server_params=StdioServerParameters(
                    command="python",
                    args=["-m", "meridian_ops.mcp_server.server"],
                    # Client should set cwd/PYTHONPATH to `project/` when running.
                )
            ),
            # Least privilege: order agent only sees order lookup (+ optional policy).
            tool_filter=["tool_get_order"],
        )
    ],
)