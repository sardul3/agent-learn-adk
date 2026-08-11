# Lesson 16 — MCP tool ecosystems (native ADK)

**Level:** Advanced  
**Time:** ~120 minutes  
**Prerequisites:** Lessons 04, 13; `mcp` + `google-adk` MCP toolset  
**Lab outcome:** Meridian tools served over MCP; ADK agent consumes them with **`McpToolset`** + `tool_filter` — no DIY tool bus

**Standard:** [docs/NATIVE-ADK.md](../docs/NATIVE-ADK.md)  
**Docs:** [ADK MCP tools](https://google.github.io/adk-docs/tools/mcp-tools/)

---

## At a glance

| Side | Native piece |
|------|----------------|
| Server | MCP Python server (`FastMCP` / MCP SDK) exposing Meridian tools |
| Client | `google.adk.tools.mcp_tool.McpToolset` |
| Least privilege | `tool_filter=[...]` on `McpToolset` |
| Transport | `StdioConnectionParams` + `StdioServerParameters` (lab) |

**Forbidden:** `MeridianToolBus` or hand-rolled JSON-RPC clients.

---

## Why this matters

OMS publishes an MCP server. Your ADK agent must connect with `McpToolset`, not a private Python import forever — and must filter tools per role.

---

## Know these

| Term | Meaning |
|------|---------|
| **McpToolset** | ADK client that discovers/proxies MCP tools as ADK tools |
| **tool_filter** | Allowlist of tool names from that server |
| **StdioConnectionParams** | Local subprocess MCP transport |

---

## Task 1 — Install MCP + verify ADK McpToolset

### Why

Without the ADK client class, people invent buses.

### Do this

```bash
source .venv/bin/activate
pip install -U mcp "google-adk>=2.0.0"

python - <<'PY'
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from mcp import StdioServerParameters
print("McpToolset OK")
PY
```

### Expect

Imports succeed. If paths differ slightly in your version, adapt to **installed** ADK docs — still `McpToolset`.

---

## Task 2 — Run the Meridian MCP server

### Why

Server owns OMS/payment previews; agents become clients.

### Do this

Ensure domain tools exist (`oms.py`, and preview/policy helpers used by the server). Then:

```bash
cd /Users/alishaghatane/dev/agent-learn-sme/project
export PYTHONPATH=.
python -m meridian_ops.mcp_server.server
```

In another terminal, use your MCP inspector **or** skip to Task 3 (`McpToolset` will spawn stdio).

Read `project/meridian_ops/mcp_server/server.py` — confirm **no** `confirm=True` refund tool is registered.

### Expect

Server module starts; only preview/read tools exposed.

---

## Task 3 — ADK agent via McpToolset

### Why

This is the whole point of the lesson.

### Do this

Use package `project/meridian_orderops_mcp/` (already wired to `McpToolset` + `tool_filter=["tool_get_order"]`).

```bash
cd /Users/alishaghatane/dev/agent-learn-sme/project
export PYTHONPATH=.
adk web --port 8000
```

Select `meridian_orderops_mcp`. Ask status for `MC-1048292`.

### Expect

Trajectory shows MCP-backed `tool_get_order` (name may appear as exposed MCP tool name). Inventory/refund tools are **not** available to this agent because of `tool_filter`.

> **Tip:** Create `meridian_refund_mcp` later with filter `tool_get_order`, `tool_retrieve_policy`, `tool_request_refund_preview` only.

---

## Task 4 — Role allowlists = tool_filter config

### Why

Allowlists belong in config applied to `McpToolset`, not in prompts.

### Do this

`project/meridian_ops/mcp_server/allowlists.yaml`:

```yaml
roles:
  order_agent:
    tools: [tool_get_order]
  refund_agent:
    tools: [tool_get_order, tool_retrieve_policy, tool_request_refund_preview]
  inventory_agent:
    tools: [tool_get_order]  # extend when ATP tools are MCP-exposed
```

Load YAML in agent constructors to pass `tool_filter=...`.

### Expect

Refund role cannot call a tool not listed — enforced by `McpToolset`, not prose.

---

## Task 5 — Threat model (MCP-specific)

### Why

Protocol power needs boundaries.

### Do this

`project/meridian_ops/mcp_server/THREAT_MODEL.md` — at least:

1. Over-broad tool_filter  
2. Exposing confirm/settle  
3. Untrusted MCP server binary  
4. PII in tool results  
5. Schema drift on tool rename  

### Expect

Mitigations reference `tool_filter`, server code review, slim payloads — not a DIY gateway product.

---

## How it works (deeper dive)

ADK `McpToolset`:

1. Connects to MCP server  
2. `list_tools` → ADK `BaseTool` adapters  
3. Proxies `call_tool` when the LLM selects a tool  
4. Optional `tool_filter` subsets discovery  

In-process function tools remain fine for monolith labs; MCP is for **platform boundaries**.

---

## Common pitfalls / troubleshooting

| Symptom | Fix |
|---------|-----|
| Agent invents ToolBus | Delete it; use `McpToolset` |
| Server not found | `PYTHONPATH=project`, correct `python -m ...` |
| Import path drift | Match your `google.adk.tools.mcp_tool` docs |
| All tools visible | Set `tool_filter` |

---

## You are done when

- [ ] `McpToolset` import works  
- [ ] MCP server exposes preview/read only  
- [ ] `meridian_orderops_mcp` works in `adk web`  
- [ ] YAML → `tool_filter` wired  
- [ ] Threat model written  
- [ ] No DIY bus code  

---

## Knowledge check

1. What ADK class replaces a custom MCP client?  
2. How do you enforce least privilege per agent?  
3. Why is settle/confirm absent from the server?  
4. When keep in-process tools?

### Answers

1. `McpToolset`  
2. `tool_filter` (and separate agent packages)  
3. Money confirmation stays on HITL/code pipelines  
4. Same-process tight loops / simple labs  

---

## Recap

- Meridian tools are MCP-served; ADK consumes them natively.  
- Next: webhooks call **ADK Runner**; A2A uses **RemoteA2aAgent** / `to_a2a`.

---

## Stretch goal

Second agent package with refund `tool_filter` list; prove order agent cannot preview refunds.

---

## Feedback

- Could you add `tool_get_atp` to server + inventory filter without a bus?  
- Note task number + expected vs actual.

---

## Navigate

**← Prev** [Lesson 15 — Long-running & HITL resume](15-long-running-hitl-resume.md)  
**Next →** [Lesson 17 — Event-driven & A2A](17-event-driven-a2a.md)