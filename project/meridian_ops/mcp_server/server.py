"""Meridian OrderOps MCP server — stdio tools for ADK McpToolset clients.

Run (example):
  PYTHONPATH=project python -m meridian_ops.mcp_server.server

ADK client side should use google.adk.tools.mcp_tool.McpToolset — not a DIY bus.
"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from meridian_ops.tools.oms import get_order
from meridian_ops.tools.payments_guarded import request_refund_guarded
from meridian_ops.tools.policy_rag import retrieve_policy

mcp = FastMCP("meridian-orderops")


@mcp.tool()
def tool_get_order(order_id: str) -> dict:
    """Look up a Meridian order in OMS (read-only)."""
    return get_order(order_id)


@mcp.tool()
def tool_retrieve_policy(query: str) -> dict:
    """Retrieve Meridian policy documents for a query."""
    return retrieve_policy(query)


@mcp.tool()
def tool_request_refund_preview(
    order_id: str,
    amount_usd: float,
    reason_code: str,
    idempotency_key: str,
) -> dict:
    """Preview a refund request — confirm=True is intentionally unavailable via MCP."""
    return request_refund_guarded(
        order_id,
        amount_usd,
        reason_code,
        idempotency_key,
        confirm=False,
    )


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()