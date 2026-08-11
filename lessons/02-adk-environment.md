# Lesson 02 — ADK environment & developer loop

**Level:** Beginner  
**Time:** ~60–75 minutes  
**Prerequisites:** Lesson 01; Python 3.10+; Gemini API key  
**Lab outcome:** A running Meridian **Order Status** agent you can inspect in `adk web`

---

## At a glance

You install **Google ADK** (Agent Development Kit), create an agent package, wire a tiny OMS lookup tool, and learn the daily loop: edit → run → inspect trajectory → tighten instructions.

Also covered:

- Gemini API vs Vertex / Google Cloud routing
- Flash vs Pro tradeoffs (cost / latency / quality)
- Why you should understand generated scaffolding — not cargo-cult it

---

## Why this matters

At Meridian, Devon from store ops pastes:

> “Customer on MC-1048292 says delivered — what does OMS show?”

If your agentic platform cannot answer that in a local dev UI with a visible tool call, you are not ready for multi-agent graphs.

---

## Know these

| Term | Meaning |
|------|---------|
| **ADK** | Google’s code-first toolkit to build, run, evaluate, and deploy agents (Python first; also TS/Go/Java/Kotlin) |
| **`root_agent`** | The agent entrypoint ADK looks for in your package |
| **`adk create`** | CLI scaffolder for a starter agent package |
| **`adk run`** | Terminal chat loop against your agent |
| **`adk web`** | Local browser UI for development/debugging (not production) |
| **Gemini API** | Consumer/dev API keyed with `GOOGLE_API_KEY` (AI Studio) |
| **Vertex AI** | Google Cloud model serving; uses project/region + ADC instead of a raw AI Studio key |
| **Flash vs Pro** | Model tiers: Flash = cheaper/faster; Pro = stronger reasoning (usually higher cost/latency) |

### Mental model of the developer loop

```
edit agent.py / tools
        │
        ▼
   adk web  (or adk run)
        │
        ▼
 inspect: did it call the right tool with the right args?
        │
        ▼
 tighten instruction / schema / tests
```

---

## Task 1 — Create a clean virtualenv and install ADK

### Why

ADK pulls model/runtime dependencies. Isolating them keeps Meridian’s future FastAPI/service deps from fighting ADK’s versions.

### Do this

```bash
cd /Users/alishaghatane/dev/agent-learn-sme
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip

# Optional but recommended: pin with ADK constraints for your Python minor version
PYVER=$(python -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
curl -fsSL -o "constraints-${PYVER}.txt" \
  "https://raw.githubusercontent.com/google/adk-python/main/constraints-${PYVER}.txt"
pip install google-adk -c "constraints-${PYVER}.txt"
rm "constraints-${PYVER}.txt"

adk --help | head
```

### Expect

- `adk` prints help with subcommands such as `create`, `run`, `web`
- `pip show google-adk` shows a version

> **Tip:** Prefer the constraints file when you see scary dependency resolvers. It is the ADK team’s “known good” set for that Python version.

> **Watch out:** Installing into system Python is how teams get “works on my laptop” forever. Stay in `.venv`.

---

## Task 2 — Scaffold the Order Status agent package

### Why

ADK expects a package with `root_agent`. Scaffolding gets the shape right; you will replace toy code with Meridian logic immediately.

### Do this

```bash
cd /Users/alishaghatane/dev/agent-learn-sme/project
adk create meridian_order_status
```

When prompted:

- **Model:** choose a Gemini Flash-class model (fast iteration). If the wizard offers a concrete id like `gemini-2.5-flash` or `gemini-flash-latest`, pick Flash for this lesson.
- **Backend:** Gemini API (AI Studio key) unless your company already standardized on Vertex.

Explore:

```bash
ls -la meridian_order_status
cat meridian_order_status/agent.py
```

### Expect

Something shaped like:

```
meridian_order_status/
  agent.py
  __init__.py
  .env
```

> **Watch out:** Run later `adk web` from the **parent** folder that contains the agent package (`project/`), not from inside the package.

---

## Task 3 — Put secrets in `.env`, never in source

### Why

A leaked OMS or Gemini key in git is an incident. Meridian security will fail your PR for less.

### Do this

1. Create an API key in [Google AI Studio](https://aistudio.google.com/app/apikey).

2. Put it only in the agent env file:

```bash
# inside project/meridian_order_status/.env
# use YOUR key — never commit this file if it contains secrets
GOOGLE_API_KEY="YOUR_API_KEY"
```

3. Confirm git will not happily commit secrets:

```bash
cd /Users/alishaghatane/dev/agent-learn-sme
printf '%s\n' '.env' '**/.env' '.venv/' >> .gitignore
```

### Expect

- Agent package `.env` exists locally
- `.gitignore` ignores `.env` and `.venv`

> **Tip:** Gemini API = `GOOGLE_API_KEY`. Vertex usually means Google Cloud project + application default credentials and different env vars — do not mix the two setups blindly.

---

## Task 4 — Replace the scaffold with a Meridian Order Status agent

### Why

Generated `get_current_time` demos teach nothing about OMS. You want a tool the model *must* call for factual order state.

### Do this

Replace `project/meridian_order_status/agent.py` with:

```python
from __future__ import annotations

from typing import Any

from google.adk.agents.llm_agent import Agent

# In-memory OMS stub — Lesson 04 replaces this with a real module + tests.
_ORDERS: dict[str, dict[str, Any]] = {
    "MC-1048292": {
        "order_id": "MC-1048292",
        "customer_id": "C-44102",
        "lifecycle": "delivered",
        "promised_window_local": "2026-08-10T16:00-18:00",
        "delivered_at_local": "2026-08-10T17:12:00",
        "pod_photo_present": False,
        "shipping_address_city": "Austin",
        "line_count": 14,
    },
    "MC-1048301": {
        "order_id": "MC-1048301",
        "customer_id": "C-11887",
        "lifecycle": "ready_for_pickup",
        "promised_window_local": "2026-08-11T17:00-19:00",
        "delivered_at_local": None,
        "pod_photo_present": False,
        "shipping_address_city": "Austin",
        "line_count": 6,
    },
}


def get_order(order_id: str) -> dict[str, Any]:
    """Look up a Meridian order in OMS (read-only stub).

    Args:
        order_id: Meridian order id, for example MC-1048292.

    Returns:
        A dict with status=success and order fields, or status=error.
    """
    order = _ORDERS.get(order_id.strip())
    if not order:
        return {
            "status": "error",
            "error_code": "ORDER_NOT_FOUND",
            "message": f"No order found for {order_id}",
        }
    return {"status": "success", "order": order}


root_agent = Agent(
    name="meridian_order_status",
    model="gemini-2.5-flash",
    description="Answers Meridian WISMO questions using OMS order lookup.",
    instruction="""
You are Meridian Commerce Order Status, an internal ops assistant.

Scope:
- Only answer questions about order status, ETA, delivery/pickup lifecycle.
- Refuse refunds, cancellations, password resets, and medical advice.

Tool rules:
- For any question about a specific order, you MUST call get_order before claiming facts.
- Never invent delivery scans, POD photos, or timestamps.
- If get_order returns status=error, say you cannot find the order and ask for a correct MC- id.

Style:
- Be concise and operational. Prefer bullet facts over marketing tone.
- If lifecycle is delivered but pod_photo_present is false, mention the missing POD as an investigation signal.
""".strip(),
    tools=[get_order],
)
```

If `adk create` wrote a different import style that already works for your installed ADK (for example `from google.adk.agents import Agent`), keep **that** import and only replace the agent body — do not fight the package’s canonical import.

Ensure `__init__.py` exposes the agent the way the scaffold expects (often `from . import agent` or `from .agent import root_agent`). Keep the scaffold’s pattern unless `adk run` errors.

### Expect

- File saves cleanly
- No API key appears in `agent.py`

---

## Task 5 — Run with CLI, then inspect with `adk web`

### Why

`adk run` is quick. `adk web` is where you *see* tool calls — the habit that separates SME from demo.

### Do this

**CLI smoke test:**

```bash
cd /Users/alishaghatane/dev/agent-learn-sme/project
source ../.venv/bin/activate
adk run meridian_order_status
```

Try prompts:

```
What's the status of order MC-1048292?
```

```
Refund MC-1048292 please.
```

Exit the CLI when done (typically `exit` / Ctrl+C per the prompt).

**Web inspect:**

```bash
cd /Users/alishaghatane/dev/agent-learn-sme/project
adk web --port 8000
```

Open `http://localhost:8000`, select `meridian_order_status`, and rerun the WISMO prompt.

### Expect

- For `MC-1048292`, the UI/trace shows a `get_order` tool call **before** factual claims
- Lifecycle comes back as `delivered` with `pod_photo_present: false`
- Refund request is refused (instruction scope) — no fake money tool exists anyway

> **Tip:** When the answer is wrong, do not start by rewriting the whole prompt. First ask: *Did the tool run? Were the args right? Did the model ignore the tool result?*

> **Watch out:** `adk web` is for development only. Do not expose it on a public network as “the production OrderOps API.”

---

## Task 6 — Model routing judgment (Flash vs Pro, API vs Vertex)

### Why

Meridian will ask why you chose a model. “It was the default” fails design review.

### Do this

Add `project/meridian_ops/decisions/02-model-routing.md` with your answers:

1. **Dev loop for WISMO:** Flash or Pro? Cost/latency/quality rationale.  
2. **Refund decision narrative for supervisors (Lesson 07):** Flash or Pro?  
3. **Gemini API vs Vertex for Meridian production:** which fits a company that already runs GKE + IAM? One paragraph.  
4. Paste one trajectory note from `adk web` for `MC-1048292` (tool name + args + whether POD caveat appeared).

### Expect

A short decision doc you could paste into a PR description.

---

## How it works (deeper dive)

### What `Agent` / `LlmAgent` is doing

Your `root_agent` packages:

- **identity** (`name`, `description`) — helps routers/multi-agent later  
- **model** — who reasons  
- **instruction** — product policy for this specialty  
- **tools** — Python callables with type hints + docstrings (schemas)

ADK turns the docstring + type hints into a tool schema the model can call. That is why Lesson 01 insisted on structured returns.

### Cargo-cult warning

Scaffolding is a courtesy, not architecture.

| Keep | Replace early |
|------|----------------|
| Package layout, `root_agent`, `.env` pattern | Toy tools unrelated to your domain |
| `adk web` inspection habit | Copy-pasted mega-prompts from blogs |
| Explicit model id you can pin | Random “latest” aliases in production without a rollback story |

---

## Common pitfalls / troubleshooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| `adk: command not found` | venv not active | `source .venv/bin/activate` |
| Auth / API key errors | Missing `.env` or wrong var name | Set `GOOGLE_API_KEY` in the agent `.env` |
| Web UI shows no agents | Ran `adk web` from the wrong directory | Run from `project/` parent of the agent folder |
| Model invents order fields | Tool not called / instruction weak | Confirm tool call in UI; tighten “MUST call get_order” |
| `ORDER_NOT_FOUND` for valid-looking id | Typo or stub missing id | Use `MC-1048292` / `MC-1048301` from the stub |

---

## You are done when

- [ ] `google-adk` installed in `.venv`
- [ ] `meridian_order_status` answers WISMO via `get_order`
- [ ] You inspected at least one tool call in `adk web`
- [ ] `02-model-routing.md` exists with Flash/Pro and API/Vertex judgment
- [ ] Secrets are not in source

---

## Knowledge check

1. Why run `adk web` from the parent directory of the agent package?  
2. What is the difference between Gemini API auth and Vertex auth at a high level?  
3. Name two signals in a trajectory that matter more than the final sentence.  
4. When would you bump Order Status from Flash to Pro?  
5. What should happen if a user asks your Lesson 02 agent for a refund?

### Answers

1. ADK discovers agent packages as siblings/children of the cwd; running inside the wrong folder yields an empty selector.  
2. Gemini API typically uses an AI Studio API key (`GOOGLE_API_KEY`); Vertex uses Google Cloud project/region + cloud credentials/IAM.  
3. Whether `get_order` ran; args (`order_id`); tool error vs success; stop reason.  
4. When Flash repeatedly mis-routes multi-constraint investigations and measured evals show Pro wins enough to justify cost — not because Pro sounds fancier.  
5. Refuse (out of scope); no refund tool should run.

---

## Recap

- You installed ADK and learned the edit → run → inspect loop.  
- Meridian Order Status is alive with a stub OMS tool.  
- Next: turn instructions into real product policy and learn sessions/events/artifacts.

---

## Stretch goal

Add `get_delivery_events(order_id: str)` returning a short list of scan events for `MC-1048292` (include a gap that explains missing POD). Update the instruction so the agent must call it when `lifecycle == delivered`.

---

## Feedback

- Could you recreate the agent package from memory with a different name (`meridian_wismo`)?  
- What tripped you up: install/constraints, `.env`, `adk web` discovery, or instruction scope?  
- Note task number + expected vs actual.

---

## Navigate

**← Prev** [Lesson 01 — Agentic foundations](01-agentic-foundations.md)  
**Next →** [Lesson 03 — Core ADK building blocks](03-core-building-blocks.md)