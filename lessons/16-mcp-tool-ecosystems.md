# Lesson 16 — MCP tool ecosystems (native ADK)

**Level:** Advanced  
**Time:** ~120–150 minutes  
**Prerequisites:** Lessons 04, 13, 15; OrderOps Workflow loads; OMS + guarded refund tools exist  
**Lab outcome:** Meridian tools served over MCP; ADK consumes them with **`McpToolset` + `StdioConnectionParams` + `tool_filter`** — no DIY tool bus

**Standard:** [docs/NATIVE-ADK.md](../docs/NATIVE-ADK.md)  
**Docs:** [ADK MCP tools](https://google.github.io/adk-docs/tools/mcp-tools/)

---

## At a glance

OMS can live in **another process**. Your agent must not grow a private JSON-RPC client to talk to it. ADK 2.6.3 already has the client: `McpToolset`.

| Side | Native piece | Meridian file |
|------|----------------|---------------|
| Server | MCP Python server (`FastMCP`) exposing read / preview tools | `project/meridian_ops/mcp_server/server.py` |
| Client | `google.adk.tools.mcp_tool.McpToolset` | `project/meridian_orderops_mcp/agent.py` |
| Transport (lab) | `StdioConnectionParams` + `StdioServerParameters` | Same agent file |
| Least privilege | `tool_filter=["tool_get_order", …]` | Allowlist YAML → constructor |

| Task | What you do | Who enforces it | How you prove it |
|------|-------------|-----------------|------------------|
| 1 | Install ADK’s **mcp extra**; print the real imports | `google-adk[mcp]==2.6.3` | `McpToolset` / `StdioConnectionParams` import |
| 2 | Walk the Meridian MCP server; no `confirm=True` tool | `FastMCP` + domain tools | `python -m` stdio; grep the file |
| 3 | Walk `meridian_orderops_mcp`; pin the model; `adk web` WISMO | `McpToolset` + `tool_filter` | Trajectory shows `tool_get_order` only |
| 4 | YAML allowlists → `tool_filter`; pytest lists tools | `McpToolset.get_tools` | Order role sees 1 tool; refund role sees 3 |
| 5 | Second agent package with the refund filter | A second `tool_filter` | Order agent cannot preview refunds |

If you get lost, scroll back to this table. Each task fills one row. The scoreboard at the end of every task repeats the same rows.

**Forbidden:** `MeridianToolBus`, a hand-rolled MCP client, or `pip install mcp` **without** the `<2` pin (mcp 2.x breaks ADK 2.6.3).

---

## Why this matters

Store 441’s OMS team ships a **server**. Order Status is a **client**. If Order Status `from meridian_ops.tools.oms import get_order` forever, you cannot:

- Give Inventory a **smaller** tool list than Refund
- Restart OMS without restarting every agent
- Review “what can this agent call?” without reading Python imports

Two failure modes, one lesson:

1. **Over-broad client** — the order agent can see `tool_request_refund_preview` because you passed the whole server. The model will try it on a WISMO.
2. **Confirm over MCP** — someone registers `confirm=True` on the server. Priya’s HITL graph (Lesson 15) becomes optional.

Today the server exposes **read + preview only**. Each agent passes an allowlist into `McpToolset`. Money confirm stays on Lesson 07 / 15.

---

## Know these

Read this table before Task 1. Every later task reuses these words.

| Term | Plain English | Meridian example |
|------|---------------|------------------|
| **MCP** | Model Context Protocol: a standard way to expose tools to models | OMS as a stdio server |
| **`FastMCP`** | Helper from the `mcp` package to register Python functions as MCP tools | `mcp = FastMCP("meridian-orderops")` |
| **`McpToolset`** | ADK client: `list_tools` → ADK tools; `call_tool` when the LLM picks one | `tools=[McpToolset(...)]` |
| **`tool_filter`** | Allowlist (list of names) **or** a predicate. Applied **after** `list_tools`. | `["tool_get_order"]` |
| **`StdioServerParameters`** | How to **spawn** the server process: command, args, cwd, env | `python -m meridian_ops.mcp_server.server` |
| **`StdioConnectionParams`** | ADK wrapper: `server_params` + **timeout** (seconds) | `timeout=15.0` |
| **stdio** | Child process, tools over stdin/stdout. Fine for a laptop lab. | Not HTTP. Lesson 17 is webhooks. |
| **SSE / Streamable HTTP** | Other `McpToolset` transports for a **remote** server | Not today’s lab |
| **Least privilege** | An agent only sees the tools its job needs | Order Status cannot preview refunds |

### Picture this: the radio vs a private walkie

| Approach | Store 441 analogue | What goes wrong |
|----------|--------------------|-----------------|
| `McpToolset` + `tool_filter` | Official radio, channel locked to OMS lookup | Reviewable allowlist |
| `from meridian_ops.tools.oms import get_order` in every agent | Everyone walks into the back room | No process boundary |
| `MeridianToolBus` | Homemade walkie on a new frequency | Second protocol. ADK evals do not see it. |
| MCP tool with `confirm=True` | Radio that can open the cash drawer | HITL becomes a suggestion |

```
LlmAgent (meridian_orderops_mcp)
    tools=[ McpToolset(tool_filter=["tool_get_order"]) ]
            │  stdio spawn
            ▼
FastMCP  meridian-orderops
    tool_get_order                 ← yes, order agent
    tool_retrieve_policy           ← server has it; filter hides it
    tool_request_refund_preview    ← server has it; filter hides it
    (no confirm / settle tool)     ← must not exist
```

> **Tip:** In-process function tools remain fine for a monolith lab (Lessons 03–07). MCP is the **platform boundary**. Same domain functions; different door.

---

## What you already have (do not rebuild)

| Path | Job |
|------|-----|
| `project/meridian_ops/mcp_server/server.py` | FastMCP server — three tools |
| `project/meridian_ops/mcp_server/__init__.py` | Package marker |
| `project/meridian_orderops_mcp/agent.py` | `LlmAgent` + `McpToolset` |
| `project/meridian_orderops_mcp/__init__.py` | `from . import agent` |
| `project/meridian_ops/tools/oms.py` | `get_order` |
| `project/meridian_ops/tools/policy_rag.py` | `retrieve_policy` |
| `project/meridian_ops/tools/payments_guarded.py` | Preview wrapper; MCP forces `confirm=False` |
| `.venv/` | Source it. Do not recreate it. |

You will **add**:

```
project/meridian_ops/mcp_server/allowlists.yaml
project/meridian_ops/mcp_server/allowlists.py
project/meridian_ops/tests/test_mcp_tool_filter.py
project/meridian_refund_mcp/agent.py
project/meridian_refund_mcp/__init__.py
```

If `server.py` is missing, stop. This lesson teaches that file. It does not invent a bus.

---

## Task 1 — Install the MCP extra and print the real imports

### Why

ADK 2.6.3 declares `mcp>=1.24,<2` on the **`mcp` extra**. A bare `pip install mcp` can pull **mcp 2.x**. That import fails (`mcp.shared.session`, `McpHttpClientFactory`) and `google.adk.tools.mcp_tool` swallows the error — `__all__` becomes `[]`. People then write a bus.

You will install the extra ADK already defined, then import from `google.adk.tools.mcp_tool`.

### Do this

1. Activate the existing venv. Do not create a new one.

```bash
cd /Users/alishaghatane/dev/agent-learn-sme
source .venv/bin/activate
python -c "import google.adk as adk; print(adk.__version__)"
```

### Expect

```
2.6.3
```

2. Install the extra. This keeps ADK at 2.6.3 and installs a 1.x `mcp`.

```bash
pip install "google-adk[mcp]==2.6.3"
python -c "from importlib.metadata import version; print('adk', version('google-adk')); print('mcp', version('mcp'))"
```

   | Piece | What it does |
   |-------|----------------|
   | `google-adk[mcp]` | Square brackets = extra. Pulls `mcp>=1.24,<2` and `anyio`. |
   | `==2.6.3` | Pin. Do not `-U` into a mystery ADK. |

### Expect

```
adk 2.6.3
mcp 1.29.0
```

   Patch on `1.29.0` can be `1.24`–`1.x`. It must be **`<2`**. If you already installed mcp 2.x, this command **downgrades** it. That is required.

3. Print the public MCP types from the **package** `__init__` (not a guess):

```bash
python - <<'PY'
import inspect
from google.adk.tools.mcp_tool import (
    McpToolset,
    StdioConnectionParams,
    SseConnectionParams,
    StreamableHTTPConnectionParams,
)
from mcp import StdioServerParameters
from mcp.server.fastmcp import FastMCP

print("McpToolset", McpToolset)
print("McpToolset.__init__", inspect.signature(McpToolset.__init__))
print("StdioConnectionParams fields", list(StdioConnectionParams.model_fields.keys()))
print("StdioServerParameters fields", list(StdioServerParameters.model_fields.keys()))
print("FastMCP", FastMCP)
print("also valid:", "from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams")
print("OK")
PY
```

### Expect

Imports succeed. `StdioConnectionParams` fields: `server_params`, `timeout`. `StdioServerParameters` fields: `command`, `args`, `env`, `cwd`, `encoding`, `encoding_error_handler`.

Walk the `McpToolset` kwargs you will use:

| Kwarg | What it does |
|-------|----------------|
| `connection_params=` | `StdioConnectionParams` (lab) or SSE / HTTP (remote) |
| `tool_filter=` | `list[str]` of tool names **or** a `ToolPredicate`. `None` = all tools the server listed |
| `tool_name_prefix=` | Optional prefix on every name. Leave unset today. |
| `require_confirmation=` | Tool-confirmation (Lesson 15). Leave `False`. Refund HITL stays `RequestInput`. |

Walk `StdioConnectionParams`:

| Field | Default | What it does |
|-------|---------|----------------|
| `server_params` | required | The `StdioServerParameters` spawn spec |
| `timeout` | `5.0` | Seconds to wait when talking to the MCP session. Slow cold start → raise it (we use `15.0`). |

Walk `StdioServerParameters`:

| Field | What you set |
|-------|----------------|
| `command` | `"python"` — the interpreter **inside the venv** once activated |
| `args` | `["-m", "meridian_ops.mcp_server.server"]` — module form, not a brittle file path |
| `cwd` | `project/` so the server’s imports resolve |
| `env` | Must include `PYTHONPATH` pointing at `project/` |
| `encoding` | Leave `utf-8` |

`McpToolset` also accepts a raw `StdioServerParameters` as `connection_params`. ADK’s own docstring says to prefer `StdioConnectionParams` when you need a timeout. We prefer it.

> **Tip:** `from google.adk.tools.mcp_tool import McpToolset, StdioConnectionParams` is the public surface (`__all__` on 2.6.3 once mcp 1.x is installed). `from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams` is the same class.

> **Watch out:** If `from google.adk.tools.mcp_tool import McpToolset` raises `ImportError`, you are on mcp 2.x or the extra is missing. Do not write a client. Fix the pin.

### Scoreboard after Task 1

| Control | In place? |
|---------|-----------|
| `McpToolset` imports on mcp 1.x | **Yes** |
| Server walked; no confirm tool | Not yet |
| `adk web` order agent | Not yet |
| YAML → `tool_filter` pytest | Not yet |
| Refund MCP agent | Not yet |

---

## Task 2 — Walk the Meridian MCP server (preview / read only)

### Why

The server is the **capability list**. If confirm lives here, every client can settle money. You will read every tool, then start the module so you know what “stdio ready” looks like (it looks like a hang).

### Do this

1. Open `project/meridian_ops/mcp_server/server.py`.

```python
from mcp.server.fastmcp import FastMCP

from meridian_ops.tools.oms import get_order
from meridian_ops.tools.payments_guarded import request_refund_guarded
from meridian_ops.tools.policy_rag import retrieve_policy

mcp = FastMCP("meridian-orderops")
```

   | Piece | Why |
   |-------|-----|
   | `FastMCP("meridian-orderops")` | Server name. Clients see this in logs, not as an ADK agent name. |
   | Domain imports | Same functions Lessons 03–07 tested. MCP is a **door**, not a rewrite. |

2. Walk each tool. `@mcp.tool()` registers the **function name** as the MCP tool name.

```python
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
```

   | Tool | Allowed? | Why |
   |------|----------|-----|
   | `tool_get_order` | Yes | Read-only OMS |
   | `tool_retrieve_policy` | Yes | Policy binder |
   | `tool_request_refund_preview` | Yes, **preview** | Hard-codes `confirm=False` |
   | Anything with `confirm=True` | **No** | Not in this file. Do not add it. |

   The preview still goes through `payments_guarded` (allowlist, amount, idempotency key). A bad `reason_code` still returns `REASON_NOT_ALLOWED`. MCP does not bypass Lesson 07.

3. Walk startup:

```python
def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
```

   `mcp.run()` with no transport argument is **stdio**. The process waits on stdin for MCP messages. There is no “listening on 8080” banner.

4. Prove there is no confirm tool in the file:

```bash
cd /Users/alishaghatane/dev/agent-learn-sme
grep -n "confirm" project/meridian_ops/mcp_server/server.py
```

   `grep -n` prints matching lines with **line numbers** (`-n`). You want to see `confirm=False`, not a confirm tool.

### Expect

The `confirm=False` line and the docstring. **No** `confirm=True`. **No** `tool_request_refund_confirm`.

5. Start the server once so you see stdio. From `project/` with `PYTHONPATH`.

```bash
cd /Users/alishaghatane/dev/agent-learn-sme/project
source ../.venv/bin/activate
export PYTHONPATH=.
python -m meridian_ops.mcp_server.server
```

   | Piece | What it does |
   |-------|----------------|
   | `python -m meridian_ops.mcp_server.server` | `-m` runs a **module**. The server’s `__main__` calls `mcp.run()`. |
   | `PYTHONPATH=.` | `import meridian_ops` works. The MCP **child** in Task 3 needs this in `env=` too. |

### Expect

The process sits there with little or no output. **That is success.** Type a random character and you may see a protocol error — it wanted MCP JSON, not a keyboard. `Ctrl+C` to stop.

Do not leave it running for Task 3. `McpToolset` will **spawn** its own child.

> **Tip:** `Processing request of type ListToolsRequest` in later logs is the server answering `list_tools`. That line is how you know ADK reached MCP.

> **Watch out:** Running the server in the foreground is **not** how agents connect. If you keep it in a terminal and also spawn stdio, you have two servers and a confused debug session. Stop this one.

### Scoreboard after Task 2

| Control | In place? |
|---------|-----------|
| `McpToolset` imports on mcp 1.x | Yes |
| Server walked; no confirm tool | **Yes** |
| `adk web` order agent | Not yet |
| YAML → `tool_filter` pytest | Not yet |
| Refund MCP agent | Not yet |

---

## Task 3 — Order Status via `McpToolset` in `adk web`

### Why

This is the point of the lesson: the LLM calls MCP-backed `tool_get_order`, not a private import, and **cannot** see refund preview because of `tool_filter`.

### Do this

1. Open `project/meridian_orderops_mcp/agent.py`. Pin the model and give the subprocess a real `cwd` / `PYTHONPATH`. Replace the file with:

```python
"""Order Status agent that loads OMS tools via native ADK McpToolset."""

from __future__ import annotations

import os
from pathlib import Path

from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool import McpToolset, StdioConnectionParams
from mcp import StdioServerParameters

_REPO_PROJECT = Path(__file__).resolve().parents[1]

root_agent = LlmAgent(
    name="meridian_orderops_mcp",
    model="gemini-3.5-flash",
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
                    cwd=str(_REPO_PROJECT),
                    env={**os.environ, "PYTHONPATH": str(_REPO_PROJECT)},
                ),
                timeout=15.0,
            ),
            tool_filter=["tool_get_order"],
        )
    ],
)
```

   Walk every new bit:

   | Piece | Why |
   |-------|-----|
   | `model="gemini-3.5-flash"` | Curriculum pin. Same as OrderOps Workflow. |
   | `_REPO_PROJECT` | `parents[1]` from `meridian_orderops_mcp/agent.py` is `project/` |
   | `command="python"` | Venv interpreter once `adk web` is launched from that venv |
   | `args=["-m", "meridian_ops.mcp_server.server"]` | Same module you ran by hand |
   | `cwd=str(_REPO_PROJECT)` | Child’s working directory |
   | `env={**os.environ, "PYTHONPATH": ...}` | Inherit `GOOGLE_API_KEY`; **force** PYTHONPATH even if the parent forgot |
   | `timeout=15.0` | Cold import of FastMCP can exceed the 5s default |
   | `tool_filter=["tool_get_order"]` | Least privilege. Policy + preview exist on the server and stay hidden. |

   Instruction “Refuse refunds” is a **hint**. The lock is `tool_filter`. A jailbreak cannot call a tool ADK never listed.

2. Prove the agent module loads (spawns MCP once if you call `get_tools`; here we only construct):

```bash
cd /Users/alishaghatane/dev/agent-learn-sme
source .venv/bin/activate
export PYTHONPATH=project
python -c "from meridian_orderops_mcp.agent import root_agent; print(root_agent.name, root_agent.model)"
```

### Expect

```
meridian_orderops_mcp gemini-3.5-flash
```

3. Start `adk web` from `project/`:

```bash
cd /Users/alishaghatane/dev/agent-learn-sme/project
source ../.venv/bin/activate
export PYTHONPATH=.
export GOOGLE_API_KEY="YOUR_KEY"
adk web --port 8000
```

   | Flag / env | What it does |
   |------------|----------------|
   | `cd …/project` | Packages `meridian_orderops_mcp/` and `meridian_ops/` are children of cwd |
   | `--port 8000` | UI at `http://localhost:8000` |

4. Select **`meridian_orderops_mcp`** (not `meridian_orderops` — that is the Workflow). New session. Paste:

```
What's the status of order MC-1048292? nothing at the door
```

### Expect

- Trajectory includes **`tool_get_order`** (MCP-backed) with `order_id` `MC-1048292`
- Reply: delivered, **no POD photo**, a next step
- **No** `tool_request_refund_preview`
- **No** `tool_retrieve_policy`
- Asking “preview a refund for MC-1048277” should **refuse** or fail to call a refund tool — the tool is not in the list

If the agent invents a POD photo, `tool_get_order` did not run. Check stderr on the `adk web` terminal for MCP spawn errors (`ModuleNotFoundError: meridian_ops` = missing `PYTHONPATH` in `env=`).

> **Tip:** `meridian_orderops` (Workflow) and `meridian_orderops_mcp` (MCP client) are **two packages**. Pick the MCP one today.

> **Watch out:** Do not `pip install -U mcp` if a blog says so. Stay on `mcp>=1.24,<2`.

### Scoreboard after Task 3

| Control | In place? |
|---------|-----------|
| `McpToolset` imports on mcp 1.x | Yes |
| Server walked; no confirm tool | Yes |
| `adk web` order agent | **Yes** |
| YAML → `tool_filter` pytest | Not yet |
| Refund MCP agent | Not yet |

---

## Task 4 — Allowlists in YAML; pytest is the lock

### Why

A filter buried only in `agent.py` will drift between two agents. Config is the reviewable list. `McpToolset` still **enforces** it — YAML does nothing until you pass `tool_filter=...`.

You will prove enforcement with `get_tools()`, **no Gemini**. That is the PR-cheap test.

### Do this

1. Create `project/meridian_ops/mcp_server/allowlists.yaml`:

```yaml
roles:
  order_agent:
    tools:
      - tool_get_order
  refund_agent:
    tools:
      - tool_get_order
      - tool_retrieve_policy
      - tool_request_refund_preview
  inventory_agent:
    tools:
      - tool_get_order
```

   Inventory does not get ATP over MCP yet (not registered on the server). Do not list a tool the server does not have — the filter would just yield an empty extra.

2. Create `project/meridian_ops/mcp_server/allowlists.py`:

```python
from __future__ import annotations

from pathlib import Path

import yaml

_PATH = Path(__file__).resolve().parent / "allowlists.yaml"


def tools_for_role(role: str) -> list[str]:
    data = yaml.safe_load(_PATH.read_text())
    roles = data["roles"]
    if role not in roles:
        raise KeyError(f"unknown MCP role: {role}")
    return list(roles[role]["tools"])
```

   | Piece | Why |
   |-------|-----|
   | `yaml.safe_load` | Parse YAML. `safe_load` refuses arbitrary Python objects. |
   | `KeyError` on unknown role | Fail loud. Do not return `[]` (that would look like “least privilege” while meaning “typo”). |

   If `PyYAML` is missing:

```bash
pip install pyyaml
```

3. Point the order agent at the YAML (one source of truth). In `meridian_orderops_mcp/agent.py`, add the import and change `tool_filter=`:

```python
from meridian_ops.mcp_server.allowlists import tools_for_role
```

```python
            tool_filter=tools_for_role("order_agent"),
```

4. Create `project/meridian_ops/tests/test_mcp_tool_filter.py`. This **spawns** the real server (stdio), so it is an integration test — still no LLM.

```python
from __future__ import annotations

import os
from pathlib import Path

import pytest

from google.adk.tools.mcp_tool import McpToolset, StdioConnectionParams
from mcp import StdioServerParameters

from meridian_ops.mcp_server.allowlists import tools_for_role

PROJECT = Path(__file__).resolve().parents[2]


def _toolset(filt: list[str] | None) -> McpToolset:
    return McpToolset(
        connection_params=StdioConnectionParams(
            server_params=StdioServerParameters(
                command="python",
                args=["-m", "meridian_ops.mcp_server.server"],
                cwd=str(PROJECT),
                env={**os.environ, "PYTHONPATH": str(PROJECT)},
            ),
            timeout=15.0,
        ),
        tool_filter=filt,
    )


@pytest.mark.asyncio
async def test_server_lists_preview_and_reads_not_confirm():
    ts = _toolset(None)
    try:
        names = sorted(t.name for t in await ts.get_tools())
    finally:
        await ts.close()
    assert names == [
        "tool_get_order",
        "tool_request_refund_preview",
        "tool_retrieve_policy",
    ]
    assert "tool_request_refund_confirm" not in names


@pytest.mark.asyncio
async def test_order_role_only_get_order():
    ts = _toolset(tools_for_role("order_agent"))
    try:
        names = [t.name for t in await ts.get_tools()]
    finally:
        await ts.close()
    assert names == ["tool_get_order"]


@pytest.mark.asyncio
async def test_refund_role_has_preview_not_confirm():
    ts = _toolset(tools_for_role("refund_agent"))
    try:
        names = sorted(t.name for t in await ts.get_tools())
    finally:
        await ts.close()
    assert names == [
        "tool_get_order",
        "tool_request_refund_preview",
        "tool_retrieve_policy",
    ]
```

   Walk the asserts:

   | Test | Lock |
   |------|------|
   | `tool_filter=None` | Server surface is exactly three tools, sorted by name (ADK sorts for cache stability) |
   | `order_agent` | One tool |
   | `refund_agent` | Preview yes, confirm tool **absent** |
   | `await ts.close()` | Drop the stdio child so pytest does not leak processes |

5. Run:

```bash
cd /Users/alishaghatane/dev/agent-learn-sme
source .venv/bin/activate
export PYTHONPATH=project
pytest project/meridian_ops/tests/test_mcp_tool_filter.py -v
```

   | Flag | What it does |
   |------|----------------|
   | `-v` | Verbose test names |

### Expect

```
test_mcp_tool_filter.py::test_server_lists_preview_and_reads_not_confirm PASSED
test_mcp_tool_filter.py::test_order_role_only_get_order PASSED
test_mcp_tool_filter.py::test_refund_role_has_preview_not_confirm PASSED
```

You may see `UserWarning: [EXPERIMENTAL]` and `Processing request of type ListToolsRequest`. That is ADK + FastMCP talking. Not a failure.

If `get_tools` times out, raise `timeout=` or check `PYTHONPATH` in `env=`.

> **Tip:** `get_tools` is what the LLM sees. If a name is missing here, the model cannot call it — jailbreak text does not add tools.

> **Watch out:** `tool_filter=["tool_get_order", "tool_request_refund_preview"]` on the **order** agent is how WISMO grows a refund hand. Keep YAML reviews as strict as code reviews.

### Scoreboard after Task 4

| Control | In place? |
|---------|-----------|
| `McpToolset` imports on mcp 1.x | Yes |
| Server walked; no confirm tool | Yes |
| `adk web` order agent | Yes |
| YAML → `tool_filter` pytest | **Yes** |
| Refund MCP agent | Not yet |

---

## Task 5 — Refund agent package (second filter, same server)

### Why

Two roles, one server. If you only ever run the order agent, you have not proved the refund allowlist in the UI.

You will **not** give this agent a `confirm=True` tool. Preview + policy + OMS. HITL confirm stays Lesson 15’s graph.

### Do this

1. Create `project/meridian_refund_mcp/__init__.py`:

```python
from . import agent

__all__ = ["agent"]
```

2. Create `project/meridian_refund_mcp/agent.py`:

```python
"""Refund specialist that loads preview tools via native ADK McpToolset."""

from __future__ import annotations

import os
from pathlib import Path

from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool import McpToolset, StdioConnectionParams
from mcp import StdioServerParameters

from meridian_ops.mcp_server.allowlists import tools_for_role

_REPO_PROJECT = Path(__file__).resolve().parents[1]

root_agent = LlmAgent(
    name="meridian_refund_mcp",
    model="gemini-3.5-flash",
    description="Refund preview via MCP — confirm is not on this server.",
    instruction="""
You are Meridian Refund (preview only).
Look up the order and retrieve policy before quoting a preview.
Never claim a refund completed. You have no confirm/settle tool.
""".strip(),
    tools=[
        McpToolset(
            connection_params=StdioConnectionParams(
                server_params=StdioServerParameters(
                    command="python",
                    args=["-m", "meridian_ops.mcp_server.server"],
                    cwd=str(_REPO_PROJECT),
                    env={**os.environ, "PYTHONPATH": str(_REPO_PROJECT)},
                ),
                timeout=15.0,
            ),
            tool_filter=tools_for_role("refund_agent"),
        )
    ],
)
```

   Same spawn as the order agent. **Different** `tool_filter`. Same `gemini-3.5-flash`.

3. Restart `adk web` from `project/` (Task 3 command). Select **`meridian_refund_mcp`**. New session. Paste:

```
Preview a DAMAGED_ITEM refund of $214.55 for melted dairy on MC-1048277. Idempotency key maya-214-mcp.
```

### Expect

- Trajectory may include `tool_get_order`, `tool_retrieve_policy`, and/or `tool_request_refund_preview`
- Preview JSON-ish facts: amount 214.55, `requires_hitl` true (over $75), `preview: true`
- Must **not** claim the refund was issued
- Must **not** call a confirm tool (none exists)

4. Switch back to **`meridian_orderops_mcp`**. New session. Paste the **same** refund preview prompt.

### Expect

- No `tool_request_refund_preview` in the trajectory
- Agent refuses or stays on order lookup only — out of scope

That is least privilege you can show Priya without a threat-model essay.

> **Tip:** SSE / Streamable HTTP params (`SseConnectionParams`, `StreamableHTTPConnectionParams`) are how you would point at a **remote** MCP server later. Lab transport stays stdio. Do not wrap HTTP in a homemade bus.

> **Watch out:** Copy-pasting `tool_filter=["tool_get_order"]` into the refund agent “just to start” ships the wrong role. Always `tools_for_role("refund_agent")`.

### Scoreboard after Task 5

| Control | In place? |
|---------|-----------|
| `McpToolset` imports on mcp 1.x | Yes |
| Server walked; no confirm tool | Yes |
| `adk web` order agent | Yes |
| YAML → `tool_filter` pytest | Yes |
| Refund MCP agent | **Yes** |

---

## How it works (deeper dive)

`McpToolset.get_tools` on 2.6.3:

1. `MCPSessionManager` starts the stdio child (`python -m …`)
2. MCP `list_tools`
3. Each MCP tool becomes an ADK `MCPTool` / `McpTool`
4. `_is_tool_selected` applies `tool_filter` (name list or predicate)
5. Tools are **sorted by name** so the list is stable across turns (context cache)

When the LLM picks `tool_get_order`, ADK proxies `call_tool` on that session.

In-process tools (`tools=[get_order]`) skip all of this. Use them until you need a process boundary. Do not run both for the same job “for safety” — two doors, two allowlists to forget.

### Threats you already mitigated (no extra markdown file)

| Risk | Mitigation you implemented |
|------|----------------------------|
| Over-broad `tool_filter` | YAML per role + pytest |
| Confirm / settle on MCP | Not registered; `confirm=False` hard-coded |
| Untrusted server binary | You spawn **your** module, not `npx` from the internet |
| PII in tool results | Same OMS fixture discipline as Lesson 04; do not log full payloads in prod |
| Tool rename drift | Pytest lists **exact** names |

---

## Common pitfalls / troubleshooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| `ImportError: McpToolset` / empty `__all__` | mcp 2.x | `pip install "google-adk[mcp]==2.6.3"` |
| `ModuleNotFoundError: meridian_ops` in the child | `PYTHONPATH` missing in `env=` | Set `env={**os.environ, "PYTHONPATH": str(_REPO_PROJECT)}` |
| `get_tools` timeout | Default 5s | `StdioConnectionParams(..., timeout=15.0)` |
| Agent invents ToolBus | Panic after a bad import | Delete it; fix the extra |
| All three tools visible on order agent | `tool_filter=None` or wrong role | `tools_for_role("order_agent")` |
| `adk web` missing `meridian_refund_mcp` | cwd not `project/` | `cd project` then `adk web --port 8000` |
| Refund MCP claims money moved | Instruction drift | No confirm tool; check trajectory |

---

## You are done when

- [ ] `google-adk[mcp]==2.6.3`; `mcp` is 1.x; `McpToolset` imports
- [ ] Server exposes exactly get / policy / preview; `confirm=False` on preview
- [ ] `meridian_orderops_mcp` uses `gemini-3.5-flash` and `tool_filter` from YAML
- [ ] `adk web` WISMO on `MC-1048292` calls `tool_get_order` only
- [ ] `pytest project/meridian_ops/tests/test_mcp_tool_filter.py -v` green
- [ ] `meridian_refund_mcp` can preview; order agent cannot
- [ ] No `MeridianToolBus`

---

## Knowledge check

1. What ADK class replaces a custom MCP client? What extra installs it on 2.6.3?  
2. How do you enforce least privilege per agent?  
3. Why is settle/confirm absent from the server?  
4. Why `StdioConnectionParams` instead of passing only `StdioServerParameters`?  
5. Why must `env` include `PYTHONPATH` even if you exported it in the parent shell?  
6. When keep in-process tools?

### Answers

1. `McpToolset`. Install `google-adk[mcp]==2.6.3` (`mcp>=1.24,<2`).  
2. `tool_filter=` (here from YAML `tools_for_role`) plus separate agent packages.  
3. Money confirmation stays on HITL / code pipelines (Lessons 07 and 15).  
4. Timeout. Raw `StdioServerParameters` has no ADK timeout field.  
5. The **child** process does not inherit your mental model; `env=` is what it gets.  
6. Same-process labs with no team boundary — Lessons 03–07. MCP when OMS is a platform.

---

## Recap

**What you built today:** a FastMCP server of Meridian read/preview tools, two ADK agents that consume them with `McpToolset`, and a pytest lock on `tool_filter`.

**What you now understand:** the allowlist is a constructor argument, not a paragraph in the instruction; mcp 2.x is not “newer = better” for ADK 2.6.3.

**What you can do next:** Lesson 17 — webhooks call **`InMemoryRunner.run_async`**; remote policy uses **`to_a2a` / `RemoteA2aAgent`**. Still no DIY bus.

**Not done yet:** Remote SSE MCP, ATP tools on the server, confirm tools (never, unless HITL is gone — it is not).

---

## Stretch goal

Register `tool_get_atp` on the server (Lesson 04 `get_atp`), add it to `inventory_agent` in YAML, and create `meridian_inventory_mcp` with that filter. Prove the order agent still cannot call it. Same `McpToolset` pattern. No bus.

---

## Feedback

- Could you add `tool_get_atp` to server + inventory filter without a bus?  
- What tripped you up: mcp 2.x import, stdio “hang,” `PYTHONPATH` in the child, or YAML vs hardcoded filter?  
- Note the **task number** and expected vs actual (command + first lines).

---

## Navigate

**← Prev** [Lesson 15 — Long-running & HITL resume](15-long-running-hitl-resume.md)  
**Next →** [Lesson 17 — Event-driven & A2A](17-event-driven-a2a.md)
