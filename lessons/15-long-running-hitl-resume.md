# Lesson 15 — Long-running HITL resume (native ADK)

**Level:** Advanced  
**Time:** ~120–150 minutes  
**Prerequisites:** Lessons 13–14; OrderOps `Workflow` loads with a **routing map** (not 3-tuple `"WISMO"` edges)  
**Lab outcome:** Pause Meridian refunds with native **`RequestInput`**, turn on **`ResumabilityConfig(is_resumable=True)`**, resume via ADK session — **no DIY checkpoint database**

**Standard:** [docs/NATIVE-ADK.md](../docs/NATIVE-ADK.md)

---

## At a glance

Priya (CX supervisor) does not live in your `adk web` tab. Maya’s melted-dairy refund can sit overnight. ADK already knows how to pause a Workflow and continue it. You will **not** write `FileCheckpointStore`.

| Task | What you do | Who enforces it | How you prove it |
|------|-------------|-----------------|------------------|
| 1 | Verify `RequestInput` + `ResumabilityConfig` in the venv | ADK 2.6.3 | Imports print the real symbols |
| 2 | Walk `hitl_refund_gate` / `refund_finalize`; add `app` with resumability | The OrderOps package | `app.resumability_config.is_resumable is True` |
| 3 | **APPROVE** Maya’s $214.55 in `adk web` | Same session, native interrupt | Trajectory: pause → `CONFIRMED_LAB` → synthesizer |
| 4 | **DENY** the same ticket in a **new** session | `refund_finalize` is code | `DENIED`; no “refund completed” |
| 5 | Restart `adk web` against ADK **SQLite** sessions | `SqliteSessionService` | Pause, restart, resume — still no JSON folder |
| 6 | pytest the finalize helper + 72h freshness math | Your Python | Green, no Gemini |

If you get lost, scroll back to this table. Each task fills one row. The scoreboard at the end of every task repeats the same rows.

**Forbidden:** `project/meridian_ops/runtime/checkpoints/`, a homemade `resume_with_hitl()`, or “adapt `App` kwargs if your version differs.” You are on **ADK 2.6.3**.

---

## Why this matters

Maya’s organic milk arrived melted. Ticket `TCK-9004`. Order `MC-1048277`. Amount: **$214.55**. That is over Meridian’s **$75** supervisor threshold (`POL-REFUND-04`).

Priya is on the floor until tomorrow morning. If the Workflow dies when you close the laptop, Monday’s “approve” is a new chat that might skip OMS, skip the pause, and talk like money already moved.

Two failure modes, one lesson:

1. **Lost pause** — process restart, in-memory session gone, Priya’s click has nothing to attach to.
2. **Second orchestrator** — you save `{session: ...}` next to the repo. ADK’s event list and your file drift. Finance cannot reconstruct *one* story.

Today ADK owns pause and resume: `RequestInput` inside the graph, `ResumabilityConfig` on `App`, session service for the bytes.

---

## Know these

Read this table before Task 1. Every later task reuses these words.

| Term | Plain English | Meridian example |
|------|---------------|------------------|
| **HITL** | Human in the loop: a person must answer before the next node | Priya on refunds over $75 |
| **`RequestInput`** | Object a function node **yields** to pause the graph | `hitl_refund_gate` |
| **`adk_request_input`** | Function-call **name** ADK puts on the interrupt Event | What you look for in the trajectory |
| **`interrupt_id`** | Id on that function call. Resume matches it. | UUID unless you set it |
| **`payload`** | Extra JSON shown with the ask (not the decision) | Order findings string |
| **`message`** | Text Priya sees | “Reply with APPROVE or DENY…” |
| **`rerun_on_resume`** | FunctionNode flag. **False** (default): Priya’s reply **is** the node’s output. **True**: the node runs again. | Gate stays **False** so APPROVE flows to `refund_finalize` |
| **`ResumabilityConfig`** | App-level switch: pause on long-running calls; resume from the last event | `is_resumable=True` |
| **`app`** | If `agent.py` defines an `App` instance named `app`, `adk web` loads **that** (before `root_agent`) | How resumability reaches the UI |
| **Session service** | Stores session + events so a restart can continue | ADK `SqliteSessionService` / `.adk/session.db` |
| **`run_async(..., invocation_id=)`** | Runner resume of an interrupted invocation | Services; the UI does this for you |
| **Tool confirmation** | `FunctionTool(..., require_confirmation=True)` — LLM tool yes/no | **Not** the refund supervisor gate |
| **Idempotency key** | Domain money safety (Lesson 04 / 07) | Still required. Resume ≠ “refund once.” |

### Picture this: the manager key vs a sticky note

| Approach | Store 441 analogue | Survives overnight? |
|----------|--------------------|---------------------|
| `yield RequestInput` | Manager key in the register — drawer stays locked | Yes, if the **session** is stored |
| JSON file in `runtime/checkpoints/` | Sticky note on the monitor | Until someone sweeps the folder |
| `ResumabilityConfig(is_resumable=True)` | The register is allowed to pause a ticket mid-scan | Required for long-running tool pause/resume |
| `rerun_on_resume=True` on the gate | Re-asking Priya every time she types | Wrong for “APPROVE is the answer” |
| `FunctionTool(require_confirmation=True)` | “Did you mean to press this SKU button?” | Different lock. Not the cash-office gate. |

```
START → route_ticket → lookup_order  (REFUND)
                              │
                              ▼
                    hitl_refund_gate
                    yield RequestInput     ← PAUSE (adk_request_input)
                              │
                    Priya: APPROVE… / DENY…
                              │
                              ▼
                    refund_finalize        ← Python, not the model
                              │
                              ▼
                    synthesizer            ← customer-safe words
```

> **Tip:** Domain audit rows (Lesson 07) may still log business facts. That is analytics. It is not a second Workflow.

---

## What you already have (do not rebuild)

From the **repo root**, confirm these exist. Lesson 13 walked the graph. Lesson 12 made it boot.

| Path | Job |
|------|-----|
| `project/meridian_orderops/agent.py` | `hitl_refund_gate` + `refund_finalize` + routing map |
| `project/meridian_orderops/__init__.py` | `from . import agent` |
| `project/meridian_ops/fixtures/orders.json` | `MC-1048277` — `$214.55`, `melted_dairy` |
| `project/meridian_ops/fixtures/tickets.json` | `TCK-9004` text |
| `.venv/` | Already created. **Source it. Do not recreate it.** |

You will **add**:

- `app = App(..., resumability_config=ResumabilityConfig(is_resumable=True))` in `agent.py`
- `hitl_is_fresh(...)` next to `refund_finalize`
- `project/meridian_ops/tests/test_hitl_resume.py`

If `hitl_refund_gate` is missing, stop and finish Lesson 13. This lesson **resumes** that gate. It does not invent a parallel refund chat.

---

## Task 1 — Verify the native HITL symbols (venv already exists)

### Why

Wrong imports are how people invent checkpoint folders. You will print the **2.6.3** types this lesson uses before you touch `agent.py`.

`google.adk.apps` is lazy: `ResumabilityConfig` is in `__all__` and loads on access. `dir(google.adk.apps)` often **omits** it. That is not “your version is different.” That is lazy import.

### Do this

1. From the **repo root**, activate the existing venv.

```bash
cd /Users/alishaghatane/dev/agent-learn-sme
source .venv/bin/activate
python -c "import google.adk as adk; print(adk.__version__)"
```

### Expect

```
2.6.3
```

If `google.adk` is missing: `pip install "google-adk==2.6.3"` into this venv — still no `python -m venv`.

2. Run the inspection that actually sees lazy members. `dir()` alone is the trap.

```bash
python - <<'PY'
import inspect
from google.adk.apps import App, ResumabilityConfig
import google.adk.apps as a

print("dir misses lazy:", [x for x in dir(a) if "esum" in x.lower() or x == "App"])
print("__all__", a.__all__)
print("App", inspect.signature(App))
print("ResumabilityConfig", inspect.signature(ResumabilityConfig))
print("is_resumable default", ResumabilityConfig().is_resumable)

from google.adk.events.request_input import RequestInput
print("RequestInput fields", list(RequestInput.model_fields.keys()))
PY
```

### Expect

Something like:

```
dir misses lazy: []
__all__ ['App', 'ResumabilityConfig']
App (*, name: str, root_agent: ... = None, plugins: ... = <factory>, events_compaction_config: ... = None, context_cache_config: ... = None, resumability_config: google.adk.apps._configs.ResumabilityConfig | None = None) -> None
ResumabilityConfig (*, is_resumable: bool = False) -> None
is_resumable default False
RequestInput fields ['interrupt_id', 'payload', 'message', 'response_schema']
```

Walk those `App` kwargs:

| Kwarg | What it is |
|-------|------------|
| `name` | App name. Letters, digits, `_`, `-`. Not `"user"`. |
| `root_agent` | Workflow or agent. Required. |
| `plugins` | Lesson 26. Leave default today. |
| `resumability_config` | **`ResumabilityConfig`**. `None` means *not* resumable. |

Walk `ResumabilityConfig`:

| Field | Default | What `True` means |
|-------|---------|-------------------|
| `is_resumable` | `False` | Pause on long-running function calls; resume from the last event (best-effort, at-least-once) |

Walk `RequestInput`:

| Field | What you set today |
|-------|--------------------|
| `message` | Priya’s prompt |
| `payload` | Order findings (context, not the yes/no) |
| `interrupt_id` | Leave default (UUID) |
| `response_schema` | Optional stretch — skip until the recap |

3. Confirm the Workflow interrupt name (so you know what to hunt in the UI):

```bash
python -c "from google.adk.workflow.utils._workflow_hitl_utils import REQUEST_INPUT_FUNCTION_CALL_NAME; print(REQUEST_INPUT_FUNCTION_CALL_NAME)"
```

### Expect

```
adk_request_input
```

> **Tip:** ADK docs call this [Human input for workflows](https://google.github.io/adk-docs/graphs/human-input/). The class you yield is `RequestInput`. The Event’s function call is named `adk_request_input`.

> **Watch out:** Do not `try/except` around `from google.adk.apps import ResumabilityConfig`. The symbol is public on 2.6.3 (`__all__` includes it). Swallowing `ImportError` is how DIY stores come back.

### Scoreboard after Task 1

| Control | In place? |
|---------|-----------|
| Native symbols printed | **Yes** |
| `app` + `ResumabilityConfig` in OrderOps | Not yet |
| APPROVE in `adk web` | Not yet |
| DENY in `adk web` | Not yet |
| SQLite session restart | Not yet |
| pytest finalize + freshness | Not yet |

---

## Task 2 — Walk the gate, pin the model, turn resumability on

### Why

Lesson 13 paused. It did not enable app-level resumability, and `adk web` loads `root_agent` unless you export **`app`**. Without `ResumabilityConfig(is_resumable=True)`, long-running interrupts are not first-class for `Runner.run_async` resume.

Default `FunctionNode.rerun_on_resume` is **`False`**. That is what you want: Priya’s text **becomes** `hitl_refund_gate`’s output, and `refund_finalize` reads it. Do not wrap the gate in `FunctionNode(rerun_on_resume=True)` or it will ask again.

### Do this

1. Open `project/meridian_orderops/agent.py`. Confirm the model pin (Lesson 12 / 13):

```python
GEMINI = "gemini-3.5-flash"
```

   Every `LlmAgent` in this file must use `model=GEMINI` (they already do via that constant). Do not leave a stray `gemini-2.5-flash`.

2. Walk `_text_from_start` — finalize uses it on whatever resume delivered:

```python
def _text_from_start(node_input: Any) -> str:
    if isinstance(node_input, types.Content):
        parts = node_input.parts or []
        return " ".join(getattr(p, "text", "") or "" for p in parts).strip()
    return str(node_input)
```

   - If ADK hands you `Content`, join text parts.
   - If tests hand you a string, `str(...)` is fine.
   - This is **not** an LLM.

3. Walk the pause. It is an **async generator** — `yield`, not `return`:

```python
async def hitl_refund_gate(node_input: Any):
    """Native ADK HITL — RequestInput pause/resume (not a DIY checkpoint DB)."""
    yield RequestInput(
        message=(
            "Refund requires supervisor approval. "
            "Reply with APPROVE or DENY and a short note."
        ),
        payload={"order_findings": str(node_input)},
    )
```

   | Piece | Why |
   |-------|-----|
   | `async def` + `yield RequestInput(...)` | Function node pauses. ADK turns this into an Event whose function call is named `adk_request_input`. |
   | `message=...` | What Priya reads in the UI |
   | `payload=...` | Context (OMS findings). **Not** the decision. |
   | No `confirm=True` payments call | Money still waits on Lesson 07’s pipeline. This node is the **graph** gate. |

   `lookup_order` already ran on the `REFUND` route. The payload should mention `MC-1048277` when you print `node_input`.

4. Walk the code-only decision. The model does **not** set `hitl_approved`.

```python
def refund_finalize(node_input: Any) -> Event:
    """Code-only post-HITL decision."""
    text = _text_from_start(node_input).strip().upper()
    approved = text.startswith("APPROVE")
    out = {
        "hitl_approved": approved,
        "hitl_raw": _text_from_start(node_input),
        "request_status": "CONFIRMED_LAB" if approved else "DENIED",
    }
    return Event(output=out, state={"refund_decision": out})
```

   | Piece | Why |
   |-------|-----|
   | `.strip().upper()` then `startswith("APPROVE")` | `APPROVE melted dairy verified` counts. `approve` counts. `DENY …` does not. |
   | Anything that does not start with APPROVE | **DENIED** — including empty, `NOPE`, or a poem |
   | `Event(output=out, state=...)` | Next node (`synthesizer`) sees `output`. Session merges `refund_decision`. |
   | `"CONFIRMED_LAB"` | Lab status. Not a payments settlement. Synthesizer must **not** say “we refunded $214.55.” |

5. Add freshness **math** in the same file (pytest in Task 6). This is policy, not a second scheduler:

```python
def hitl_is_fresh(issued_at: float, now: float, ttl_hours: float = 72.0) -> bool:
    """True if Priya's pause is still inside the TTL. Pure math — no files."""
    return (now - issued_at) <= ttl_hours * 3600.0
```

   72 hours is Meridian’s “stale HITL” rule for this lab. You will not cron it. You will unit-test the inequality.

6. After `root_agent = Workflow(...)`, add the `App` `adk web` will prefer. Put the import with the other ADK imports at the top:

```python
from google.adk.apps import App, ResumabilityConfig
```

   At the **bottom** of `agent.py` (after `root_agent` exists):

```python
app = App(
    name="meridian_orderops",
    root_agent=root_agent,
    resumability_config=ResumabilityConfig(is_resumable=True),
)
```

   | Piece | Why |
   |-------|-----|
   | Name `app` | `AgentLoader` checks `app` **before** `root_agent` |
   | `name="meridian_orderops"` | Must match what sessions use. Same as Lesson 12’s FastAPI `App`. |
   | `root_agent=root_agent` | The Workflow. One graph. |
   | `ResumabilityConfig(is_resumable=True)` | Long-running `RequestInput` can pause/resume |

   Keep `root_agent` defined. Tests and Lesson 12’s edge import it by that name.

7. Prove construction from the repo root:

```bash
cd /Users/alishaghatane/dev/agent-learn-sme
source .venv/bin/activate
export PYTHONPATH=project
python - <<'PY'
from meridian_orderops.agent import app, root_agent, GEMINI, hitl_refund_gate, refund_finalize

print("GEMINI", GEMINI)
print("workflow", root_agent.name, type(root_agent).__name__)
print("app", app.name)
print("resumable", app.resumability_config.is_resumable)
print("gate", hitl_refund_gate.__name__)
print("finalize", refund_finalize.__name__)
assert GEMINI == "gemini-3.5-flash"
assert app.resumability_config is not None
assert app.resumability_config.is_resumable is True
print("OK")
PY
```

### Expect

```
GEMINI gemini-3.5-flash
workflow meridian_orderops Workflow
app meridian_orderops
resumable True
gate hitl_refund_gate
finalize refund_finalize
OK
```

> **Tip:** `is_resumable=True` is best-effort and **at-least-once**. That is why Lesson 07 idempotency keys still matter: a resumed confirm must not open a second refund.

> **Watch out:** `InMemoryRunner(app=app)` — pass the **App**. `InMemoryRunner(app=app, plugins=[...])` raises `ValueError` on 2.6.3 (plugins belong on `App`, Lesson 26).

### Scoreboard after Task 2

| Control | In place? |
|---------|-----------|
| Native symbols printed | Yes |
| `app` + `ResumabilityConfig` in OrderOps | **Yes** |
| APPROVE in `adk web` | Not yet |
| DENY in `adk web` | Not yet |
| SQLite session restart | Not yet |
| pytest finalize + freshness | Not yet |

---

## Task 3 — APPROVE $214.55 in `adk web` (same session)

### Why

A flag in Python is not a product until Priya can click. You will send **one** refund prompt, wait for the native interrupt, then reply **APPROVE** in that **same** session.

Do not start a new session for the approval. A new session is a new graph run — it will pause again and ignore yesterday’s click.

### Do this

1. Confirm the fixture still has Maya’s order:

```bash
cd /Users/alishaghatane/dev/agent-learn-sme
source .venv/bin/activate
python - <<'PY'
import json
from pathlib import Path
o = json.loads(Path("project/meridian_ops/fixtures/orders.json").read_text())["MC-1048277"]
print(o["order_id"], o["order_total_usd"], o.get("damage_report"), "pod=", o.get("pod_photo_present"))
PY
```

### Expect

```
MC-1048277 214.55 melted_dairy pod= True
```

   POD can be true on this order (photo of melted milk). Amount **214.55** is what trips HITL. The word **refund** is what trips the router.

2. Launch the UI from `project/` so ADK discovers packages as **children** of cwd. Pass SQLite so Task 5 can restart (create the folder first).

```bash
cd /Users/alishaghatane/dev/agent-learn-sme/project
source ../.venv/bin/activate
export PYTHONPATH=.
export GOOGLE_API_KEY="YOUR_KEY"
mkdir -p .adk
adk web --port 8000 --session_service_uri sqlite://./.adk/hitl.db
```

   | Flag / env | What it does |
   |------------|----------------|
   | `cd …/project` | Discovery root. `meridian_orderops/` must be a child of cwd. |
   | `source ../.venv/bin/activate` | Venv lives at the **repo** root. |
   | `export PYTHONPATH=.` | `from meridian_ops.tools.oms import get_order` resolves. |
   | `GOOGLE_API_KEY` | Synthesizer (and narrators) call Gemini. The gate itself does not. |
   | `mkdir -p .adk` | `-p` = create parents, no error if it exists. |
   | `adk web --port 8000` | Dev UI at `http://localhost:8000`. `--port` picks the listen port (same as Lessons 02 / 13). |
   | `--session_service_uri sqlite://./.adk/hitl.db` | ADK **`SqliteSessionService`**. Relative path `.adk/hitl.db` under cwd. **Not** `runtime/checkpoints/`. |

   Leave this process running.

3. Browser: `http://localhost:8000`. Select **`meridian_orderops`**. **New session**. Copy the session id from the UI if it shows one (you need it in Task 5).

4. Paste **exactly** this user message (substring `refund` + `MC-1048277` + `$214.55`):

```
I want a full refund of $214.55 for melted items on MC-1048277
```

   Why this text:

   | Token | What it does |
   |-------|----------------|
   | `refund` | `route_ticket` emits `REFUND` (before shortage / WISMO) |
   | `MC-1048277` | OMS lookup |
   | `$214.55` | Over $75 — Priya must see the gate |

5. **Stop when the graph pauses.** Open the trajectory / event list. You should see:

   - `route_ticket` / route `REFUND`
   - `lookup_order`
   - `hitl_refund_gate`
   - a function call named **`adk_request_input`**
   - message: `Refund requires supervisor approval. Reply with APPROVE or DENY and a short note.`
   - **no** `synthesizer` yet
   - **no** customer sentence that the refund is done

6. In the **same** session, send Priya’s approval **exactly**:

```
APPROVE melted dairy verified
```

   If the UI shows a dedicated HITL / request-input box, type it there. If it is just the chat box, send it as the next user message **without** creating a new session.

### Expect

After resume:

| Check | Pass looks like |
|-------|-----------------|
| `refund_finalize` ran | Trajectory includes that node |
| `request_status` | `CONFIRMED_LAB` (in the finalize output / state) |
| `hitl_approved` | `true` |
| `synthesizer` | Empathy → facts → next step |
| Forbidden sentence | Must **not** claim “we refunded $214.55” / “refund completed” |

`startswith("APPROVE")` is why the prefix must be APPROVE. Extra words (`melted dairy verified`) are the short note. They do not change the boolean.

If the UI never pauses, the routing map’s `REFUND` value is not `hitl_refund_gate`. Finish Lesson 13 Task 2. Do not “fix” it with a stronger synthesizer instruction.

If you send APPROVE in a **new** session, the graph starts over and pauses again. That is not resume. Same session.

> **Tip:** Function nodes are cheap. Language nodes spend money. Finalize is Python so a tired model cannot flip DENY to APPROVE.

> **Watch out:** `YES melted dairy` does **not** start with `APPROVE` → `DENIED`. Use the exact prefix.

### Scoreboard after Task 3

| Control | In place? |
|---------|-----------|
| Native symbols printed | Yes |
| `app` + `ResumabilityConfig` in OrderOps | Yes |
| APPROVE in `adk web` | **Yes** |
| DENY in `adk web` | Not yet |
| SQLite session restart | Not yet |
| pytest finalize + freshness | Not yet |

---

## Task 4 — DENY in a new session (first-class path)

### Why

If only APPROVE is tested, a bug that treats every resume as yes ships to finance. Deny must be a **full** path: pause, resume, finalize, synthesizer.

### Do this

1. Keep `adk web` running. In the UI: **New session** (different from Task 3).

2. Paste the **same** customer prompt:

```
I want a full refund of $214.55 for melted items on MC-1048277
```

3. Wait for `adk_request_input` again. Then send **exactly**:

```
DENY insufficient evidence
```

### Expect

| Check | Pass looks like |
|-------|-----------------|
| Pause | Same `RequestInput` message as Task 3 |
| `refund_finalize` | `hitl_approved: false`, `request_status: DENIED` |
| `hitl_raw` | Contains `DENY insufficient evidence` (case may be uppercased in the check, raw is preserved) |
| Synthesizer | Customer-safe. **No** “refund completed.” **No** “we issued $214.55.” |
| Payments | No `confirm=true` call — this graph never called `request_refund` |

`DENY` does not start with `APPROVE`. Empty string would also deny. You used an explicit deny so the audit note exists.

> **Tip:** Two sessions, two decisions. Do not reuse Task 3’s session or you will append a DENY onto an already-finalized APPROVE.

> **Watch out:** Do not save either decision into `project/meridian_ops/runtime/checkpoints/`. That folder is gitignored because it is the **wrong** product. ADK’s session db already has the events.

### Scoreboard after Task 4

| Control | In place? |
|---------|-----------|
| Native symbols printed | Yes |
| `app` + `ResumabilityConfig` in OrderOps | Yes |
| APPROVE in `adk web` | Yes |
| DENY in `adk web` | **Yes** |
| SQLite session restart | Not yet |
| pytest finalize + freshness | Not yet |

---

## Task 5 — Restart `adk web`; resume from ADK SQLite

### Why

`InMemoryRunner` (Lesson 12) dies with the process. Overnight HITL needs a **session service**. ADK 2.6.3 already ships `SqliteSessionService`. You pointed `adk web` at `sqlite://./.adk/hitl.db` in Task 3. Now you prove the file outlives the UI.

This is not Lesson 29 (sessions at scale). This is: restart the **same** binary, same db, same session id, finish Priya’s click.

### Do this

1. **New session** in the running UI. Paste the refund prompt again:

```
I want a full refund of $214.55 for melted items on MC-1048277
```

2. When it pauses on `adk_request_input`, **copy the session id** from the UI. Leave the ticket **unanswered**.

3. Confirm the ADK db exists (cwd is `project/`):

```bash
ls -l /Users/alishaghatane/dev/agent-learn-sme/project/.adk/hitl.db
```

### Expect

A SQLite file with a non-zero size. That file **is** the session store. Not a checkpoint JSON.

4. In the `adk web` terminal: `Ctrl+C`. Start it **again** with the **same** URI:

```bash
cd /Users/alishaghatane/dev/agent-learn-sme/project
source ../.venv/bin/activate
export PYTHONPATH=.
export GOOGLE_API_KEY="YOUR_KEY"
adk web --port 8000 --session_service_uri sqlite://./.adk/hitl.db
```

5. Browser: refresh `http://localhost:8000`. Select `meridian_orderops`. Open the **same session id**. You should still see the paused refund (events came back from SQLite).

6. Send:

```
APPROVE melted dairy verified
```

### Expect

`refund_finalize` → `CONFIRMED_LAB` → synthesizer, same as Task 3, **after a process restart**.

If the session is empty, you started without `--session_service_uri` or used a different cwd (the relative `./.adk/hitl.db` follows cwd). Always `cd project` first.

Default `adk web` also has `--use_local_storage`, which writes `meridian_orderops/.adk/session.db`. That is still ADK SQLite. The **explicit** URI is easier to point at in a review.

> **Tip:** `Runner.run_async` takes `invocation_id=` to resume an interrupted invocation when `is_resumable` is true. The web UI does that matching for you when you reply in the same session.

> **Watch out:** Relative `sqlite://./.adk/hitl.db` is **not** a DIY store. `SqliteSessionService(db_path=...)` is the class. A folder of your own JSON is the class we forbid.

### Scoreboard after Task 5

| Control | In place? |
|---------|-----------|
| Native symbols printed | Yes |
| `app` + `ResumabilityConfig` in OrderOps | Yes |
| APPROVE in `adk web` | Yes |
| DENY in `adk web` | Yes |
| SQLite session restart | **Yes** |
| pytest finalize + freshness | Not yet |

---

## Task 6 — pytest: finalize prefixes + 72h math (no Gemini)

### Why

UI demos flake. `startswith("APPROVE")` and the 72-hour inequality must not.

You will not stand up a second HITL worker. You will test the **functions** the graph already calls.

### Do this

1. Create `project/meridian_ops/tests/test_hitl_resume.py`.

```python
from google.adk.events.event import Event
from google.genai import types

from meridian_orderops.agent import hitl_is_fresh, refund_finalize


def _user(text: str) -> types.Content:
    return types.Content(role="user", parts=[types.Part.from_text(text=text)])


def test_approve_prefix_confirms_lab():
    ev = refund_finalize(_user("APPROVE melted dairy verified"))
    assert isinstance(ev, Event)
    assert ev.output["hitl_approved"] is True
    assert ev.output["request_status"] == "CONFIRMED_LAB"
    assert "APPROVE" in ev.output["hitl_raw"].upper()


def test_deny_does_not_confirm():
    ev = refund_finalize(_user("DENY insufficient evidence"))
    assert ev.output["hitl_approved"] is False
    assert ev.output["request_status"] == "DENIED"


def test_yes_without_approve_is_deny():
    ev = refund_finalize("YES melted dairy")
    assert ev.output["request_status"] == "DENIED"


def test_hitl_fresh_inside_72h():
    issued = 1_000_000.0
    now = issued + (71 * 3600)
    assert hitl_is_fresh(issued, now, ttl_hours=72.0) is True


def test_hitl_stale_after_72h():
    issued = 1_000_000.0
    now = issued + (72 * 3600) + 1
    assert hitl_is_fresh(issued, now, ttl_hours=72.0) is False
```

   Walk the cases:

   | Test | What it locks |
   |------|----------------|
   | `APPROVE melted dairy verified` | Exact Task 3 string |
   | `DENY insufficient evidence` | Exact Task 4 string |
   | `YES melted dairy` | Friendly English is not a manager key |
   | 71h | Still fresh |
   | 72h + 1s | Stale — cannot confirm |

2. Run them from the repo root:

```bash
cd /Users/alishaghatane/dev/agent-learn-sme
source .venv/bin/activate
export PYTHONPATH=project
pytest project/meridian_ops/tests/test_hitl_resume.py -v
```

   | Flag | What it does |
   |------|----------------|
   | `-v` | Verbose: one line per test name |

### Expect

```
test_hitl_resume.py::test_approve_prefix_confirms_lab PASSED
test_hitl_resume.py::test_deny_does_not_confirm PASSED
test_hitl_resume.py::test_yes_without_approve_is_deny PASSED
test_hitl_resume.py::test_hitl_fresh_inside_72h PASSED
test_hitl_resume.py::test_hitl_stale_after_72h PASSED
```

No `GOOGLE_API_KEY` required. If pytest tries to construct the Workflow and fails, the routing map is broken — fix Lesson 13, do not skip these tests.

3. Optional wiring (still native): a later node can call `hitl_is_fresh(ctx.state["hitl_issued_at"], time.time())` and `Event(route="EXPIRED")`. You do **not** need a cron. Task 2’s helper is the policy. Graph wiring can wait until you stamp `hitl_issued_at` on an `Event(state=...)` **before** `yield RequestInput` (RequestInput itself does not carry `state_delta`).

### Tool confirmation vs this gate (read, do not mix)

ADK has a **second** native pause: `FunctionTool(func, require_confirmation=True)`. On 2.6.3 that tool calls `tool_context.request_confirmation(...)` and returns an error until a `ToolConfirmation` payload arrives. `McpToolset` has the same `require_confirmation=` kwarg.

| Mechanism | Use when | Meridian |
|-----------|----------|----------|
| Graph `RequestInput` | Supervisor gate **in the Workflow** | Refund APPROVE / DENY |
| `FunctionTool(..., require_confirmation=True)` | Model is about to call a **side-effect tool** | Not the cash-office path |

Do **not** put `require_confirmation=True` on a refund tool *instead of* `hitl_refund_gate`. Priya’s gate is an edge she can point at in code review.

Prove the flag exists (no Gemini):

```bash
python - <<'PY'
from google.adk.tools.function_tool import FunctionTool

def ping(x: int) -> int:
    """Echo x."""
    return x

t = FunctionTool(ping, require_confirmation=True)
print("require_confirmation", t._require_confirmation)
assert t._require_confirmation is True
print("OK FunctionTool confirmation flag")
PY
```

### Expect

```
require_confirmation True
OK FunctionTool confirmation flag
```

> **Tip:** Lesson 13’s live runner test already asserts `adk_request_input` on the refund prompt and `synthesizer` **absent** until resume. Keep that test. Today’s tests are the **decision** function.

> **Watch out:** Do not implement `hitl_is_fresh` by reading a file. Pass two numbers. Files are how checkpoint DBs sneak back.

### Scoreboard after Task 6

| Control | In place? |
|---------|-----------|
| Native symbols printed | Yes |
| `app` + `ResumabilityConfig` in OrderOps | Yes |
| APPROVE in `adk web` | Yes |
| DENY in `adk web` | Yes |
| SQLite session restart | Yes |
| pytest finalize + freshness | **Yes** |

---

## How it works (deeper dive)

### What happens when you `yield RequestInput`

1. `FunctionNode` sees a `RequestInput` and passes it through (`_to_event`).
2. Workflow HITL helpers build an Event with `types.FunctionCall(name="adk_request_input", id=interrupt_id, args=…)`.
3. `long_running_tool_ids` includes that id — this is a **pause**, not a finished tool.
4. On resume, `rerun_on_resume=False` (default): the node is marked complete; Priya’s reply is the output; `refund_finalize` runs.

### What `ResumabilityConfig` adds

From the 2.6.3 docstring: pause on a long-running function call; resume from the last event if paused or failed midway. Tool calls to resume must be **idempotent** (at-least-once). Temporary in-memory state is lost — **session events** are the source of truth.

`Runner.run_async` on a resumable app may pass `invocation_id=` without a new user question to continue. The web UI attaches Priya’s reply as the function response for `adk_request_input`.

### What you must not build

| DIY idea | Native replacement |
|----------|-------------------|
| `FileCheckpointStore` / `runtime/checkpoints/` | Session service + `RequestInput` |
| `resume_with_hitl()` bespoke API | `adk web` same session, or `run_async` + function response |
| Parallel “approval worker” process | Lesson 17 webhook **calling** ADK Runner |

### Idempotency still sits in payments

ADK resume can run `refund_finalize` more than once. Lesson 07’s idempotency key is what stops two `RFQ-` ids. Complementary locks.

---

## Common pitfalls / troubleshooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| `dir(google.adk.apps)` has no `ResumabilityConfig` | Lazy `__getattr__` | Import it; check `__all__` |
| `ValidationError` / `'WISMO'` | 3-tuple edges | Lesson 13 routing map |
| UI never pauses | `hitl_refund_gate` not on `REFUND` | Routing map after `lookup_order` |
| APPROVE in a new session pauses again | That is a new invocation | Same session id |
| `YES` treated as deny | `startswith("APPROVE")` | Use the exact prefix |
| Lost pause after restart | In-memory sessions / wrong cwd for sqlite URI | `--session_service_uri sqlite://./.adk/hitl.db` from `project/` |
| Reintroduced checkpoint JSON | Old habit | Delete it; use ADK SQLite |
| Synthesizer claims money moved | Instruction ignored | Finalize is `CONFIRMED_LAB` only; instruction already says never claim completed — check the draft |

---

## You are done when

- [ ] `ResumabilityConfig` imported from `google.adk.apps`; `is_resumable=True` on `app`
- [ ] `GEMINI == "gemini-3.5-flash"`
- [ ] `adk web` APPROVE path: pause → `APPROVE melted dairy verified` → `CONFIRMED_LAB`
- [ ] New session DENY path: `DENY insufficient evidence` → `DENIED`, no completed-refund claim
- [ ] Restarted `adk web` against `sqlite://./.adk/hitl.db` and resumed
- [ ] `pytest project/meridian_ops/tests/test_hitl_resume.py -v` green
- [ ] No `FileCheckpointStore`, no `runtime/checkpoints/` writes

---

## Knowledge check

1. Which ADK type does a function node **yield** to pause a Workflow? What function-call **name** shows in the trajectory?  
2. What is the 2.6.3 constructor for turning resumability on?  
3. Why is `rerun_on_resume` left **False** on `hitl_refund_gate`?  
4. Where should multi-hour pause state live?  
5. Why keep payment idempotency keys even with ADK resume?  
6. When do you use `FunctionTool(require_confirmation=True)` instead of `RequestInput`?

### Answers

1. `RequestInput`. Trajectory name: `adk_request_input`.  
2. `App(..., resumability_config=ResumabilityConfig(is_resumable=True))`.  
3. False means Priya’s reply **is** the node output, which `refund_finalize` reads. True would re-run the gate and ask again.  
4. An **ADK** session service (here `SqliteSessionService` via `--session_service_uri`).  
5. Resume is at-least-once. Money retries are a different lock.  
6. When an **LLM tool** needs a yes/no before a side effect. The refund **supervisor** gate stays a graph `RequestInput`.

---

## Recap

**What you built today:** OrderOps pauses with native `RequestInput`, resumes through ADK sessions, and decides APPROVE/DENY in Python.

**What you now understand:** `app` + `ResumabilityConfig` is the switch; SQLite is the overnight bag; a JSON folder is a second orchestrator.

**What you can do next:** Lesson 16 serves the same OMS tools over **MCP** with `McpToolset` — still no DIY bus.

**Not done yet:** Lesson 29 session backends at scale; wiring `hitl_is_fresh` onto a routed `EXPIRED` edge.

---

## Stretch goal

Add `response_schema` on `RequestInput` so Priya’s reply is structured `{decision: APPROVE|DENY, note: str}` (a Pydantic model). Keep `refund_finalize` reading that schema — still no checkpoint files.

---

## Feedback

- Could you explain ADK resume to Priya without mentioning custom files?  
- What tripped you up: lazy `dir()`, same-session APPROVE, sqlite cwd, or the APPROVE prefix?  
- Note the **task number** and expected vs actual (command + first lines).

---

## Navigate

**← Prev** [Lesson 14 — Parallel, loop & custom agents](14-parallel-loop-custom-agents.md)  
**Next →** [Lesson 16 — MCP & tool ecosystems](16-mcp-tool-ecosystems.md)
