# Lesson 02 — ADK environment & developer loop

**Level:** Beginner  
**Time:** ~60–75 minutes  
**Prerequisites:** Lesson 01; Python 3.10+; a Gemini API key from Google AI Studio  
**Lab outcome:** A running Meridian **Order Status** agent you can inspect in `adk web` — including a visible `get_order` tool call for `MC-1048292`

---

## At a glance

You install **Google ADK** (Agent Development Kit), create an agent package, wire a tiny OMS lookup tool, and learn the daily loop: edit → run → inspect the trajectory → tighten the instruction.

| Task | What you prove | How |
|------|----------------|-----|
| 1 | ADK lives in a project virtualenv | `pip show` + `adk --help` |
| 2 | A package ADK can discover | `adk create meridian_order_status` |
| 3 | The API key is not in source | `.env` + `.gitignore` |
| 4 | `root_agent` calls a real OMS stub | You paste and walk `agent.py` |
| 5 | The UI lists the agent and calls `get_order` | `adk web --port 8000` |
| 6 | Missing ids and refunds fail out loud | Two more chats in the same UI |

If you get lost, scroll back to this table. The scoreboard at the end of every task repeats the same rows.

---

## Why this matters

At Store 441, Devon from store ops pastes into chat:

> “Customer on MC-1048292 says delivered — what does OMS show?”

Maya (customer `C-44102`) is waiting. OMS = order management system: the system of record for lifecycle, timestamps, and proof-of-delivery (POD).

If your agent platform cannot answer that in a **local** UI with a **visible tool call**, you are not ready for multi-agent graphs. Pretty sentences are not evidence. A `get_order` row for `MC-1048292` is evidence.

Today you build that loop. Lesson 03 will move the stub into a shared module and add session state. Do not skip the inspect habit.

---

## Know these

Read this table before Task 1. Every later task reuses these words.

| Term | Plain English | Meridian example |
|------|---------------|------------------|
| **ADK** | Google’s code-first toolkit to build, run, evaluate, and deploy agents | The `adk` command you install in Task 1 |
| **Virtualenv (`.venv`)** | A private Python for this repo | Stops Homebrew Python from fighting ADK |
| **`root_agent`** | The variable ADK loads from `agent.py` | Your Order Status `Agent(...)` |
| **`adk create`** | CLI scaffolder: writes a starter package | `meridian_order_status/` |
| **`adk web`** | Local browser UI for development | `http://localhost:8000` — not production |
| **`adk run`** | Terminal chat against the same agent | Quick smoke test without a browser |
| **Trajectory** | The trace of what happened in a turn | Did `get_order` run? With which `order_id`? |
| **Tool** | A Python function the model is allowed to call | `get_order` |
| **Instruction** | Product policy for this agent | Scope, refusals, “MUST call get_order” |
| **Gemini API** | Dev API keyed with `GOOGLE_API_KEY` (AI Studio) | What this lab uses |
| **Vertex AI** | Google Cloud model serving (project + region + cloud credentials) | Common in GKE shops; not this lesson’s setup |
| **Flash vs Pro** | Model tiers | Flash = cheaper/faster. Pro = heavier reasoning, usually slower and costlier |
| **WISMO** | “Where is my order?” | Maya asking about `MC-1048292` |
| **OMS stub** | Fake OMS in a dict, same *shape* as a real lookup | `_ORDERS["MC-1048292"]` in `agent.py` |
| **POD** | Proof of delivery (photo, scan) | `pod_photo_present: false` on Maya’s order |

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
 tighten instruction / tool return / tests
```

When the answer is wrong, do not start by rewriting the whole prompt. First ask:

1. Did the tool run?
2. Were the arguments right (`order_id=MC-1048292`)?
3. Did the model ignore the tool result?

---

## Task 1 — Create a virtualenv and install ADK

### Why

ADK pulls model and runtime libraries. A **virtualenv** keeps those versions in `.venv/` so they do not fight Meridian’s later FastAPI or pytest packages, and so you do not install into system Python.

You will install **`google-adk` 2.6.3** (or newer in the 2.6 line). That is the ADK this curriculum uses. Get a working install first. A constraints file is an optional extra *after* `adk --help` works — not the first command.

### Do this

1. Open a terminal. Go to the **repo root** (the folder that contains `project/` and `lessons/`):

```bash
cd /Users/alishaghatane/dev/agent-learn-sme
```

2. Create the virtualenv:

```bash
python3 -m venv .venv
```

   - `python3` — the Python 3 binary on your Mac.
   - `-m venv` — run the standard-library **`venv` module** (do not look for a separate `virtualenv` command).
   - `.venv` — folder name for this environment. The leading dot hides it in some file listings. This repo already gitignores `.venv/`.

   If `.venv` already exists from an earlier attempt, skip this command. Recreating it is safe only if you are willing to reinstall packages.

3. Activate it:

```bash
source .venv/bin/activate
```

   `source` runs the activate script in *this* shell. After it works, your prompt usually shows `(.venv)`, and `which python` points inside `.venv/bin/python`.

   New terminal tabs do **not** stay activated. Run `source` again in each tab you use for this project.

4. Upgrade pip inside the venv, then install ADK:

```bash
python -m pip install -U pip
pip install "google-adk>=2.6.3"
```

   - `python -m pip` — run pip *as a module of this venv’s Python*, so you cannot accidentally call a different pip.
   - `-U` (same as `--upgrade`) — upgrade pip itself. A newer pip has a better dependency resolver.
   - `"google-adk>=2.6.3"` — install ADK **2.6.3 or newer**. The quotes stop the shell from treating `>` as a file redirect. Without quotes, `pip install google-adk>=2.6.3` can write a file named `=2.6.3`.

5. Prove the CLI exists:

```bash
adk --help
pip show google-adk
```

   `adk --help` — print the command list (`create`, `run`, `web`, …). `--help` is the standard “explain this command” flag.

### Expect

- `adk --help` lists subcommands including **`create`**, **`run`**, and **`web`**.
- `pip show google-adk` includes a line like:

```
Name: google-adk
Version: 2.6.3
```

Your prompt still shows `(.venv)`.

> **Tip:** If `adk: command not found`, the venv is not active, or the install wrote scripts to a different environment. Run `source .venv/bin/activate` and `which adk` — it should be `.../agent-learn-sme/.venv/bin/adk`.

> **Watch out:** Installing into system Python (`pip3 install` with no venv) is how teams get “works on my laptop.” Stay in `.venv`.

### Optional extra — pin transitive deps *after* ADK already works

Only do this if a later `pip install` fights ADK’s dependencies. This is **not** required to finish Task 1.

```bash
PYVER=$(python -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
curl -fsSL -o "constraints-${PYVER}.txt" \
  "https://raw.githubusercontent.com/google/adk-python/main/constraints-${PYVER}.txt"
pip install "google-adk>=2.6.3" -c "constraints-${PYVER}.txt"
```

What those flags mean:

| Flag | Intent |
|------|--------|
| `curl -f` | Fail if the URL returns an HTTP error (do not save an HTML 404 page as a constraints file) |
| `-s` | Silent progress |
| `-S` | Still *show* errors when used with `-s` |
| `-L` | Follow redirects |
| `-o file` | Write to that filename |
| `pip ... -c file` | **Constrain** every package version to the ADK team’s known-good set for your Python minor version (for example 3.11 or 3.12) |

This repo gitignores `constraints-*.txt`. You do not commit the downloaded file.

### Scoreboard after Task 1

| Proof | In place? |
|-------|-----------|
| Virtualenv + `google-adk` | **Yes** |
| `meridian_order_status` package | Not yet |
| API key in `.env` only | Not yet |
| `get_order` wired on `root_agent` | Not yet |
| `adk web` lists the agent and calls `get_order` | Not yet |
| Missing id / refund refuse | Not yet |

---

## Task 2 — Scaffold the Order Status package

### Why

ADK discovers agents as **folders** under the directory you pass to `adk web`. Each folder needs `agent.py` (with `root_agent`) and `__init__.py`.

`adk create` writes that shape so you do not invent a layout ADK cannot see. You will **replace** the toy demo tool in Task 4. Read the generated files first so you know what you are replacing.

### Do this

1. Change into `project/` — the parent folder that will hold every Meridian agent package:

```bash
cd /Users/alishaghatane/dev/agent-learn-sme/project
source ../.venv/bin/activate
```

   You activate from here with `../.venv` because the venv lives in the **repo root**, not inside `project/`.

2. Create the package:

```bash
adk create meridian_order_status --model gemini-3.5-flash
```

   - `meridian_order_status` — **positional** app name. It becomes the folder name. ADK’s help calls this `APP_NAME`.
   - `--model gemini-3.5-flash` — put that model id on the generated root agent. This lab’s model is **gemini-3.5-flash** (Flash-class: fast enough for WISMO lookups).

   Do **not** pass `--api_key` on the command line. Keys in shell history are an incident. Task 3 puts the key in `.env`.

   Other `adk create` flags you are **not** using today:

   | Flag | What it would do | Why we skip it |
   |------|------------------|----------------|
   | `--api_key` | Write the key into generated env | Shell history + files; use `.env` instead |
   | `--project` | Vertex AI Google Cloud project | This lab uses the Gemini API, not Vertex |
   | `--region` | Vertex region | Same reason |

   If the folder already exists, skip `adk create`. Task 4 will overwrite `agent.py`.

3. List what was generated:

```bash
ls -la meridian_order_status
```

   `ls -la` — long listing (`-l`) including hidden files (`-a`), so you can see `.env` and `.gitignore`.

4. Read the generated agent (you will replace it; you still need to see the shape):

```bash
cat meridian_order_status/agent.py
cat meridian_order_status/__init__.py
```

### Expect

A folder shaped like:

```
meridian_order_status/
  agent.py          ← will define root_agent
  __init__.py       ← usually: from . import agent
  .env              ← secrets go here in Task 3
  .gitignore        ← should ignore .env
```

`__init__.py` should import the agent module so ADK can load the package. Keep the scaffold’s one-liner (typically `from . import agent`). Do not delete this file.

The generated `agent.py` may still contain a toy example (current time, hello world). That is expected. Task 4 replaces it with `get_order`.

> **Tip:** Run `adk web` later from **`project/`**, the parent of `meridian_order_status`. If you run it from inside the package, the agent list is often empty.

> **Watch out:** The folder name (`meridian_order_status`) is how the UI lists the app. The `name=` field inside `Agent(...)` is the agent’s identity. Keep them aligned so logs match what you click.

### Scoreboard after Task 2

| Proof | In place? |
|-------|-----------|
| Virtualenv + `google-adk` | Yes |
| `meridian_order_status` package | **Yes** |
| API key in `.env` only | Not yet |
| `get_order` wired on `root_agent` | Not yet |
| `adk web` lists the agent and calls `get_order` | Not yet |
| Missing id / refund refuse | Not yet |

---

## Task 3 — Put the API key in `.env`, never in source

### Why

A leaked Gemini key in git is a security incident. Meridian security will fail the PR. The model backend reads `GOOGLE_API_KEY` from the environment. ADK loads the agent folder’s `.env` for that.

### Do this

1. Create an API key in [Google AI Studio](https://aistudio.google.com/app/apikey) if you do not already have one.

2. Open `project/meridian_order_status/.env`. Put **only** your key (no quotes required; quotes are fine if you keep them consistent):

```bash
GOOGLE_API_KEY=YOUR_API_KEY
```

   Replace `YOUR_API_KEY` with the real key. This file stays on your machine.

3. Confirm the package gitignore lists `.env`. The scaffold usually already has it. Check:

```bash
cat meridian_order_status/.gitignore
```

   You want a line that is `.env`.

4. Confirm the **repo** gitignore also ignores env files and the venv. From the repo root:

```bash
cd /Users/alishaghatane/dev/agent-learn-sme
grep -n '\.env' .gitignore
```

   `grep -n` — print matching lines with line numbers (`-n`). This repo already contains `.env` and `**/.env`. You should not need to append anything. If those lines are missing, add them:

```bash
printf '%s\n' '.env' '**/.env' '.venv/' >> .gitignore
```

   `>>` **appends**. A single `>` would overwrite the whole gitignore. Do not use `>` here.

5. Confirm git does not see the key as a new tracked file:

```bash
git check-ignore -v project/meridian_order_status/.env
```

   `git check-ignore -v` — show *which* ignore rule hides the path (`-v` = verbose).

### Expect

- `project/meridian_order_status/.env` exists locally and contains `GOOGLE_API_KEY=...`
- `git check-ignore` prints a rule (from `.gitignore` or the package `.gitignore`)
- No API key appears in `agent.py`

> **Tip:** Gemini API = `GOOGLE_API_KEY`. Vertex uses a Google Cloud project, a region, and application default credentials — different env vars. Do not mix the two setups in this lesson.

> **Watch out:** Never paste the key into `instruction=` or into a lesson note you might commit. If you already pasted it into `agent.py`, remove it, rotate the key in AI Studio, and put the new key only in `.env`.

### Scoreboard after Task 3

| Proof | In place? |
|-------|-----------|
| Virtualenv + `google-adk` | Yes |
| `meridian_order_status` package | Yes |
| API key in `.env` only | **Yes** |
| `get_order` wired on `root_agent` | Not yet |
| `adk web` lists the agent and calls `get_order` | Not yet |
| Missing id / refund refuse | Not yet |

---

## Task 4 — Replace the scaffold with Order Status + `get_order`

### Why

A generated “get current time” tool teaches nothing about OMS. Devon needs a lookup the model **must** call before it claims Maya’s order is delivered.

Lesson 03 will move this dict into `oms.py` + `orders.json`. Today the stub lives in `agent.py` so you can see the whole agent in one file: identity, model, instruction, tools.

### Do this

1. Replace **all** of `project/meridian_order_status/agent.py` with:

```python
from __future__ import annotations

from typing import Any

from google.adk.agents.llm_agent import Agent

# In-memory OMS stub — Lesson 03 replaces this with a real module + tests.
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
    model="gemini-3.5-flash",
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

2. Walk the file top to bottom. Do not skip this. The scaffold is a starter file, not a finished product — if you cannot explain a line, you cannot debug it at 2 a.m.

   **Imports**

   - `from __future__ import annotations` — treat type hints as strings so `dict[str, Any]` works on older Python 3.10.
   - `from google.adk.agents.llm_agent import Agent` — the ADK 2.6.3 class this repo uses. Same import as later lessons.
   - No API key import. The key stays in `.env`.

   **`_ORDERS`**

   Two tickets so you can see a hit and (in Task 6) a miss:

   | Order id | Customer | Lifecycle | Why it is here |
   |----------|----------|-----------|----------------|
   | `MC-1048292` | Maya `C-44102` | `delivered` at 17:12, **no POD photo** | Today’s WISMO prompt |
   | `MC-1048301` | `C-11887` | `ready_for_pickup` | A second lifecycle so the model cannot assume “everything is delivered” |

   `pod_photo_present: False` on Maya’s row is the investigation signal. If the agent never mentions it, the instruction’s last bullet is not landing.

   **`get_order`**

   ```
   strip the id → look up _ORDERS
        ├─ missing ──▶ status=error, error_code=ORDER_NOT_FOUND
        └─ found   ──▶ status=success, order=the dict
   ```

   | Piece | Why it is there |
   |-------|-----------------|
   | Type hints `order_id: str` → `dict` | ADK builds the tool schema from these |
   | Docstring + `Args:` | The model reads this to know *when* to call the tool |
   | `.strip()` | Trailing spaces in a paste should not become `ORDER_NOT_FOUND` |
   | Error **dict**, not `raise` | Exceptions become stack traces in the trajectory. Dicts become something Devon can quote |
   | `error_code` | Stable string for tests and for the instruction (“if status=error…”) |

   This function is **read-only**. It does not change OMS. Lesson 04 will add write tools with dry-run.

   **`root_agent = Agent(...)`** — every field:

   | Field | Value | What ADK uses it for |
   |-------|-------|----------------------|
   | `name` | `meridian_order_status` | Identity in logs, later routers, the UI |
   | `model` | `gemini-3.5-flash` | Who reasons. Pin an id you can grep. |
   | `description` | one sentence | UI / later routers: “what does this specialist do?” |
   | `instruction` | the triple-quoted block | Product policy for *this* agent |
   | `tools` | `[get_order]` | The only function the model may call |

   **`instruction` layers** (same shape Lesson 03 will deepen):

   ```
   WHO you are
     → SCOPE (in / out)
       → TOOL RULES (must / must not)
         → STYLE
   ```

   - **Scope in:** status, ETA, lifecycle.
   - **Scope out:** refunds, cancellations, passwords, medical advice. There is no refund tool anyway. The instruction still says refuse — defense in depth.
   - **MUST call `get_order`** — the line you will check in the trajectory.
   - **Never invent scans** — if the tool did not return a timestamp, the bubble must not grow one.
   - **Missing POD** — Maya’s row is delivered *without* a photo. The agent should say so.

   `.strip()` on the instruction removes the accidental leading newline from the triple quotes so the first line the model sees is “You are Meridian…”

3. From the **repo root**, confirm `__init__.py` still loads the module:

```bash
cd /Users/alishaghatane/dev/agent-learn-sme
cat project/meridian_order_status/__init__.py
```

   Keep `from . import agent` (or the scaffold’s equivalent). ADK imports the package; the package must import `agent.py` so `root_agent` exists.

4. Confirm no key leaked into the agent file:

```bash
grep -n 'API_KEY\|AIza' project/meridian_order_status/agent.py || echo "no key in agent.py"
```

### Expect

- File saves cleanly.
- `root_agent` is defined once, at the bottom.
- `tools=[get_order]` — one tool, read-only.
- `model="gemini-3.5-flash"`.
- `grep` prints `no key in agent.py`.

> **Tip:** You can call `get_order` from a normal Python shell without Gemini. That is the Lesson 04 habit, started small:

```bash
cd /Users/alishaghatane/dev/agent-learn-sme/project
source ../.venv/bin/activate
python -c "from meridian_order_status.agent import get_order; print(get_order('MC-1048292'))"
```

   You should see `"lifecycle": "delivered"` and `"pod_photo_present": false`.

> **Watch out:** If you keep the scaffold’s toy tool *and* `get_order`, the model may call the clock instead of OMS. Delete the toy function. One tool.

### Scoreboard after Task 4

| Proof | In place? |
|-------|-----------|
| Virtualenv + `google-adk` | Yes |
| `meridian_order_status` package | Yes |
| API key in `.env` only | Yes |
| `get_order` wired on `root_agent` | **Yes** |
| `adk web` lists the agent and calls `get_order` | Not yet |
| Missing id / refund refuse | Not yet |

---

## Task 5 — Inspect with `adk web` (the daily loop)

### Why

`adk run` is a fast chat in the terminal. `adk web` is where you **see** tool calls. SME work is the inspect habit, not a prettier final sentence.

Today’s proof: the agent list includes `meridian_order_status`, and sending Maya’s WISMO line calls `get_order`.

### Do this

1. From `project/`, start the UI. Press `Ctrl+C` first if an old `adk web` is still running.

```bash
cd /Users/alishaghatane/dev/agent-learn-sme/project
source ../.venv/bin/activate
adk web --port 8000
```

   - `adk web` — start the local FastAPI + browser UI. Discovers agent **subfolders** of the current directory (or of an optional path argument).
   - `--port 8000` — bind to port **8000**. Open `http://localhost:8000`. Pinning the port means you never guess whether it chose 8000 or 8080.
   - Default `--host` is `127.0.0.1` (this machine only). Do not pass `--host 0.0.0.0` to “share with the team.” That would expose a **dev** UI on the network.

   You do not need `PYTHONPATH` yet. `get_order` lives inside the agent package.

2. Open `http://localhost:8000` in your browser.

3. Look at the **agent list**. Select **`meridian_order_status`**.

4. Send this exact user message:

```
Status for MC-1048292?
```

5. Open the turn’s **events / trajectory / tool** panel (the debug trace next to the chat bubble — the Events tab in the ADK web UI). Find the `get_order` call.

### Expect

**Agent list:** `meridian_order_status` appears as a selectable app. If the list is empty, you started `adk web` from the wrong directory (see troubleshooting).

**Tool call:** sending `Status for MC-1048292?` produces a `get_order` call **before** factual claims.

| What to read in the trace | What it should be |
|---------------------------|-------------------|
| Tool name | `get_order` |
| Argument `order_id` | `MC-1048292` |
| Result `status` | `success` |
| Result `order.lifecycle` | `delivered` |
| Result `order.pod_photo_present` | `false` |
| Result `order.delivered_at_local` | `2026-08-10T17:12:00` |

**Chat bubble:** bullets with those facts. It should mention the **missing POD** as an investigation signal. It must not invent a porch photo.

The terminal that launched `adk web` may print request logs. The **tool result** lives in the UI trace.

Optional smoke in another terminal (venv on, still from `project/`) if you want a no-browser check:

```bash
cd /Users/alishaghatane/dev/agent-learn-sme/project
source ../.venv/bin/activate
adk run meridian_order_status "Status for MC-1048292?"
```

- `adk run AGENT` — run that package.
- The quoted string is an optional **one-shot QUERY**. Without it, `adk run` enters interactive chat. With it, you get one turn and a reply.

You still need `adk web` for the inspect habit. The CLI is a backup, not a replacement.

> **Tip:** Wrong answer → check the three questions in Know these (tool ran? args right? result ignored?). Then change **one** thing: instruction, or the tool return, not both.

> **Watch out:** `adk web` is for development. It is not the production OrderOps API. Lesson 12 covers deploy. Do not tunnel this port to the public internet.

> **Watch out:** After you edit `agent.py`, restart `adk web` (Ctrl+C, then the same command). Reload in the browser is not enough if the process still holds the old module.

### Scoreboard after Task 5

| Proof | In place? |
|-------|-----------|
| Virtualenv + `google-adk` | Yes |
| `meridian_order_status` package | Yes |
| API key in `.env` only | Yes |
| `get_order` wired on `root_agent` | Yes |
| `adk web` lists the agent and calls `get_order` | **Yes** |
| Missing id / refund refuse | Not yet |

---

## Task 6 — Missing order, refund refuse, same UI

### Why

A demo that only works on `MC-1048292` is a happy-path screenshot. Devon will paste typos. Maya will ask for a refund in the same box.

You already wrote the error dict and the scope rules. Now watch them fire.

### Do this

Stay in `adk web` on **meridian_order_status**. Use a **new session** for each prompt so the first success does not confuse the miss (click new session in the UI).

1. Send:

```
Status for MC-0000000?
```

   Open the trajectory. You want `get_order` with `order_id=MC-0000000` and `error_code=ORDER_NOT_FOUND`.

2. New session. Send:

```
Refund MC-1048292 please.
```

   There is no refund tool. The instruction says refuse. The trajectory should **not** show a money tool (you did not add one). The bubble should refuse and may still call `get_order` if it wants facts first — that is allowed. It must not say “refund completed.”

3. Optional third prompt, same agent: `Status for MC-1048301?` Confirm lifecycle is `ready_for_pickup`, not delivered. That proves the stub has more than Maya’s row.

### Expect

**Missing id**

- Tool: `get_order`
- Args: `MC-0000000`
- Result: `"status": "error"`, `"error_code": "ORDER_NOT_FOUND"`
- Bubble: cannot find the order; asks for a correct `MC-` id. No invented delivery time.

**Refund**

- No `request_refund` (that tool does not exist until Lesson 04).
- Customer-facing text is a **refusal** (out of scope).
- If `get_order` ran, that is lookup, not a payout.

**Pickup order (optional)**

- `lifecycle` is `ready_for_pickup`.
- `delivered_at_local` is `null` / `None`.

> **Tip:** Flash is the right default for this WISMO loop: short lookup, tight instruction, one tool. Reach for Pro later when a *measured* eval says Flash mis-routes messy disputes — not because Pro sounds fancier. Lesson 20 covers routing in depth.

> **Watch out:** If the miss prompt never calls `get_order` and the model still says “not found,” you got a lucky sentence. Tighten “MUST call get_order” and retry. The trajectory is the proof, not the vibe.

### Scoreboard after Task 6

| Proof | In place? |
|-------|-----------|
| Virtualenv + `google-adk` | Yes |
| `meridian_order_status` package | Yes |
| API key in `.env` only | Yes |
| `get_order` wired on `root_agent` | Yes |
| `adk web` lists the agent and calls `get_order` | Yes |
| Missing id / refund refuse | **Yes** |

---

## How it works (deeper dive)

### What `Agent` / `LlmAgent` is packaging

Your `root_agent` is a bundle:

```
identity (name, description)
    → model (gemini-3.5-flash)
        → instruction (product policy)
            → tools (Python callables + docstrings)
```

ADK turns the **docstring + type hints** on `get_order` into a schema the model can call. That is why Lesson 01 pushed structured returns (`status`, `error_code`). The model is filling in `order_id`; your function is the cash register.

### Why the scaffold exists

| Keep | Replace in this lesson |
|------|------------------------|
| Package layout, `root_agent`, `__init__.py`, `.env` | Toy tools (current time, hello world) |
| `adk web` inspect habit | Copy-pasted mega-prompts from blogs |
| Explicit model id `gemini-3.5-flash` | Vague “latest” aliases you cannot grep in a PR |

Read every line you paste. If `tools=[get_order]` is missing, the model will invent OMS.

### Flash vs Pro (judgment, not a homework file)

| | Flash (`gemini-3.5-flash`) | Pro |
|--|----------------------------|-----|
| This WISMO agent | **Use this** — one lookup, tight schema | Usually wasted cost |
| Later refund narratives for Priya | Start Flash; bump if evals fail | Stronger long reasoning, slower |
| What you pin in code | The string in `model=` | A different string, same `Agent` shape |

### Gemini API vs Vertex

| | This lab (Gemini API) | Typical Meridian prod (Vertex) |
|--|----------------------|--------------------------------|
| Auth | `GOOGLE_API_KEY` in `.env` | Cloud project + region + IAM / ADC |
| `adk create` | `--model` only | Would add `--project` and `--region` |
| Why Vertex later | — | GKE + IAM already exist; keys in a file do not |

You are not mixing them today. One backend, one env var.

---

## Common pitfalls / troubleshooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| `adk: command not found` | Venv not active | `source .venv/bin/activate` from repo root; from `project/` use `source ../.venv/bin/activate` |
| `zsh: no such file or directory: google-adk>=2.6.3` or a mystery file `=2.6.3` | Forgot quotes around the pip spec | `pip install "google-adk>=2.6.3"` |
| Auth / API key errors in the UI | Missing `.env` or wrong var name | `GOOGLE_API_KEY` in `project/meridian_order_status/.env` |
| Web UI shows **no agents** | Ran `adk web` from the wrong directory | Run from `project/` (parent of `meridian_order_status/`) |
| List has the agent, tool never runs | Toy tool still on `tools=`, or instruction too weak | Task 4 file only; restart `adk web` |
| Model invents delivery fields | Tool not called, or result ignored | Confirm `get_order` + `MC-1048292` in Events |
| `ORDER_NOT_FOUND` for Maya’s id | Typo (`MC-104829` / letter O) | Use `MC-1048292` from the stub |
| `ModuleNotFoundError: google.adk` | Different Python than the venv | `which python` must show `.venv/bin/python` |
| Port already in use | Old `adk web` still running | Ctrl+C in that terminal, or pick another `--port` and use that URL |
| Key committed | `.env` not ignored | `git check-ignore -v`; rotate the key |

---

## You are done when

- [ ] `pip show google-adk` reports **2.6.3** (or newer) inside `.venv`
- [ ] `adk --help` lists `create`, `run`, `web`
- [ ] `project/meridian_order_status/agent.py` defines `root_agent` with `model="gemini-3.5-flash"` and `tools=[get_order]`
- [ ] Secrets are only in `.env`, which git ignores
- [ ] `adk web --port 8000` from `project/`: agent list includes **meridian_order_status**
- [ ] Prompt `Status for MC-1048292?` shows a `get_order` call with that id; lifecycle `delivered`; missing POD mentioned
- [ ] `MC-0000000` returns `ORDER_NOT_FOUND`; refund prompt is refused

---

## Knowledge check

Answer from this lab, not from generic “how to use an LLM” advice.

1. Why run `adk web` from `project/` rather than from inside `meridian_order_status/`?  
2. What is the difference between Gemini API auth and Vertex auth at a high level?  
3. Name two signals in a trajectory that matter more than the final sentence.  
4. When would you bump Order Status from Flash to Pro?  
5. What should happen if a user asks this Lesson 02 agent for a refund?  
6. What do `-m`, `-U`, `--port`, and `--model` mean on the commands you ran?

### Answers

1. ADK discovers agent packages as subfolders of the working directory (or of the path you pass). Inside the package, the selector is often empty.  
2. Gemini API uses an AI Studio key (`GOOGLE_API_KEY`). Vertex uses a Google Cloud project, region, and cloud credentials / IAM.  
3. Whether `get_order` ran; the `order_id` argument; tool `status` vs `ORDER_NOT_FOUND`; whether POD came from the tool.  
4. When Flash repeatedly mishandles messy multi-constraint disputes **and** evals show Pro wins enough to justify cost — not because Pro sounds fancier.  
5. Refuse (out of scope). No refund tool should run.  
6. `-m` = run a library module (`venv`, `pip`). `-U` = upgrade. `--port 8000` = bind the UI to port 8000. `--model gemini-3.5-flash` = set the generated agent’s model id.

---

## Recap

**What you built:** a venv, ADK 2.6.3, `meridian_order_status` with an in-memory `get_order`, running in `adk web`.

**What you now understand:** `root_agent` fields (`name`, `model`, `instruction`, `tools`); inspect the trajectory before you rewrite the prompt; keys never belong in source.

**What you can do next:** Lesson 03 promotes the stub into `oms.py`, adds session state for “that order,” and stamps a callback so Priya can see a turn start in the logs.

---

## Stretch goal

Add `get_delivery_events(order_id: str)` that returns a short list of scan events for `MC-1048292` (include a gap that explains missing POD). Put it on `tools=` next to `get_order`. Update the instruction: when `lifecycle == delivered`, the agent must call `get_delivery_events` as well. Restart `adk web` and confirm **two** tool names in the trajectory for `Status for MC-1048292?`.

---

## Feedback

- Could you recreate the package from memory with a different name (`meridian_wismo`) and still get `get_order` to show up in Events?  
- What tripped you up: venv / pip quotes, `.env`, `adk web` discovery, or the `Agent(...)` fields?  
- Note the **task number** and what you expected vs what happened (command + first lines of output).

---

## Navigate

**← Prev** [Lesson 01 — Agentic foundations](01-agentic-foundations.md)  
**Next →** [Lesson 03 — Core ADK building blocks](03-core-building-blocks.md)
