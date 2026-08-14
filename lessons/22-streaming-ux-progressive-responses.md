# Lesson 22 — Streaming UX & progressive responses

**Level:** Advanced  
**Time:** ~120 minutes  
**Prerequisites:** Lessons 12, 17, 20, 21 (FastAPI edge, Runner events, tools, multimodal optional)  
**Lab outcome:** Stream OrderOps **progress** from ADK `run_async` to Devon’s handheld via **SSE** — tool status, then tokens, then a marked final — without waiting for the whole turn as one JSON blob

**Standard:** [docs/NATIVE-ADK.md](../docs/NATIVE-ADK.md)

---

## At a glance

Lesson 12’s FastAPI edge (`project/meridian_ops/deploy/app.py`) waits for the last event, then returns `{ "final_text": ... }`. That is fine for a backend. It is painful on a store handheld.

| Layer | Job |
|-------|-----|
| ADK `Runner.run_async` | Yields native **`Event`** objects as the agent thinks, calls tools, and writes text |
| Codec | Turns one `Event` into small JSON payloads (`tool_status` / `token` / `final`) |
| FastAPI edge | Auth + **SSE** (`text/event-stream`) |
| Handheld | Shows “Checking OMS…” then words, then a finished script |

**Forbidden:** Replacing ADK with a homemade token generator.  
**Allowed:** A thin SSE adapter around native events — the same pattern as Lesson 12 (FastAPI calls `App` + `InMemoryRunner`).

You will build seven pieces, in this order:

| Task | What you add | How you prove it |
|------|----------------|------------------|
| 1 | Inspect live `run_async` events | Print loop — see FINAL vs partial |
| 2 | `encode_sse` + `adk_event_to_payloads` | `pytest` on real ADK `Event`s |
| 3 | FastAPI SSE endpoint | Server boots; 401 without a key |
| 4 | `curl` the wire format | Sample `data: ...` lines |
| 5 | Human tool status copy | Devon sees “Checking OMS…”, not `get_order` |
| 6 | Stream vs schema split | Decision note in the repo |
| 7 | Timeout / error event | No infinite spinner |

---

## Why this matters

Devon on a handheld in aisle 4, dairy case empty:

> “DC shorted SKU 884210 — what do I tell the next five pickup customers?”

If `/v1/wismo` waits **12 seconds** for one JSON blob:

1. The screen looks frozen.
2. Devon hits send again.
3. You now have two in-flight turns.
4. He invents an answer so the line moves.

Progressive UX is the radio, not the novel:

1. Immediate ack (`status/started` + `session_id`)
2. Tool status: `get_order` is running
3. Tokens of the pickup script as they arrive
4. A **final** event — only then is the script done
5. `status/done` with the same `session_id` for audit

Streaming is how ops tools feel trustworthy under latency. It is not decoration.

---

## Know these

Read this table before Task 1. Every later task reuses these words.

| Term | Plain English | Meridian example |
|------|---------------|------------------|
| **`Event`** | One ADK update from `run_async` | A function call, a text chunk, or the finished answer |
| **`run_async`** | Async iterator: `async for event in runner.run_async(...)` | The only source of tokens in this lesson |
| **Partial** | Not yet the complete answer | `event.is_final_response()` is **False** |
| **FINAL** | Safe to treat as the complete user-facing answer | `event.is_final_response()` is **True** |
| **`event.author`** | Which agent wrote this event | `meridian_order_status` |
| **`event.content.parts`** | Pieces of the payload: text and/or function calls | `"Pickup is ready…"` or `get_order(...)` |
| **SSE** | Server-Sent Events: HTTP stream of `data: …` plus a blank line | Handheld keeps the connection open |
| **Tool status** | UX signal that a function started or finished | “Checking OMS for the order…” |
| **Codec** | Your mapper: `Event` → small dicts → SSE strings | `event_codec.py` |

### Picture this: radio vs waiting for the whole story

```
Devon (handheld)              FastAPI                         ADK Runner
  │  POST /v1/orderops/stream    │                               │
  │─────────────────────────────►│  run_async(...)               │
  │                              │──────────────────────────────►│
  │  SSE: status started         │                               │
  │  SSE: tool_status get_order  │◄──── function_call event ─────│
  │  SSE: token "Order MC-…"     │◄──── partial text ────────────│
  │  SSE: final {script}         │◄──── is_final_response ───────│
  │  SSE: status done            │                               │
```

Lesson 12:

```
POST /v1/wismo  ── wait ──►  { "final_text": "…entire script…" }
```

Same runner. Different **when** Devon sees bytes.

### `Event` helpers you will call (learn once)

ADK 2.6.3 `Event` already walks `content.parts` for you:

| Method | Returns | When it is useful |
|--------|---------|-------------------|
| `event.get_function_calls()` | list of `FunctionCall` (`.name`, `.args`) | Model is **starting** a tool |
| `event.get_function_responses()` | list of `FunctionResponse` (`.name`) | Tool **finished** |
| `event.is_final_response()` | `bool` | This is the complete user-facing answer |
| `event.author` | `str` | Which agent spoke |
| `event.content.parts` | text and/or function parts | Read `.text` when present |

Call those methods. Do not copy a `getattr` scavenger hunt into the codec.

`is_final_response()` is **False** when:

- `event.partial` is true (tokens still arriving), or
- the event still has function calls or function responses

Treat **only** `is_final_response() == True` as “Devon may read this as done.”

---

## What you already have (do not rebuild)

| Path | Job |
|------|-----|
| `project/meridian_order_status/agent.py` | Lesson 03 `Agent` with `get_order` — **this** stream, so you will see tool events |
| `project/meridian_ops/deploy/app.py` | Lesson 12 JSON edge (`/v1/wismo`) — keep it |
| `project/meridian_ops/tools/oms.py` | Order fixture for `MC-1048301` (ready for pickup) |

`meridian_orderops` (Lesson 13 Workflow) looks up orders in **Python**, not as a tool, so its stream is quieter. Task 1 uses **Order Status** on purpose.

You will **add**:

```
project/meridian_ops/
  streaming/
    __init__.py
    event_codec.py       Tasks 2 + 5
  deploy/
    stream_api.py        Tasks 3 + 7
  tests/
    test_event_codec.py
  decisions/
    22-stream-vs-schema.md   Task 6
```

---

## Task 1 — Watch native events before you wrap them

### Why

You cannot stream what you have not seen.

Print every event. Label it `FINAL` or `partial`. Read `author`. If there is a function call, print the tool name. That dump is the contract the codec will wrap.

### Do this

1. Activate the venv and set `PYTHONPATH` so `meridian_order_status` imports. From the **repo root**:

```bash
cd /Users/alishaghatane/dev/agent-learn-sme
source .venv/bin/activate
export PYTHONPATH=project
```

   - `source .venv/bin/activate` — this project’s Python, not Homebrew’s.
   - `export PYTHONPATH=project` — `import meridian_order_status` means `project/meridian_order_status`.

2. Confirm `GOOGLE_API_KEY` is set (same key you use for `adk web`). Without it the runner cannot call Flash.

3. Run this print loop. It is ADK `App` + `InMemoryRunner` — not a homemade generator:

```bash
python - <<'PY'
import asyncio
from google.adk.apps import App
from google.adk.runners import InMemoryRunner
from google.genai import types
from meridian_order_status.agent import root_agent

APP = "meridian_order_status"
USER = "devon"

async def main():
    app = App(name=APP, root_agent=root_agent)
    runner = InMemoryRunner(app=app)
    session = await runner.session_service.create_session(app_name=APP, user_id=USER)
    msg = types.Content(
        role="user",
        parts=[types.Part.from_text(text="Where is order MC-1048301 for pickup?")],
    )
    async for event in runner.run_async(
        user_id=USER, session_id=session.id, new_message=msg
    ):
        kind = "FINAL" if event.is_final_response() else "partial"
        calls = [c.name for c in event.get_function_calls()]
        resps = [r.name for r in event.get_function_responses()]
        text = ""
        if event.content and event.content.parts:
            text = "".join(p.text for p in event.content.parts if p.text)
        print(kind, event.author, "calls=", calls, "resps=", resps, "text=", (text or "")[:120])

asyncio.run(main())
PY
```

   Walk the loop, line by line:

   | Line | What it means |
   |------|----------------|
   | `App(...)` / `InMemoryRunner(app=...)` | Same harness as Lessons 08 and 20 |
   | `create_session` | Mint `session.id` — you will put this on SSE start/done |
   | `runner.run_async(user_id=..., session_id=..., new_message=...)` | Yields `Event` until the turn ends |
   | `kind = "FINAL" if event.is_final_response() else "partial"` | **The** distinction for the UI |
   | `get_function_calls()` | Non-empty → model asked for a tool (usually `get_order` here) |
   | `get_function_responses()` | Non-empty → OMS came back |
   | `event.author` | Who spoke |
   | text join on `parts` | Skip parts with no `.text` (function-call parts have none) |

   **FINAL vs partial — paint this on a sticky note:**

   | Label | `is_final_response()` | What Devon’s UI should do |
   |-------|----------------------|---------------------------|
   | `partial` | False | Show progress: tool spinner, or append/replace tokens. **Do not** mark the ticket done. |
   | `FINAL` | True | Replace the buffer with this text (or confirm it). **Now** the script is complete. |

   If you treat every text event as final, Devon acts on “Order MC-1048301 is…” and never sees “ready for pickup 5–7pm.”

### Expect

Several lines, then one `FINAL`. Shape like:

```
partial meridian_order_status calls= ['get_order'] resps= [] text=
partial meridian_order_status calls= [] resps= ['get_order'] text=
partial meridian_order_status calls= [] resps= [] text= Order MC-1048301
FINAL meridian_order_status calls= [] resps= [] text= Order MC-1048301 is ready for pickup between 5pm and 7pm…
```

Exact wording and how many `partial` text lines you get will vary. What must be true:

- At least one event is `FINAL`
- `get_order` appears in `calls` and/or `resps` (the agent must look up the order)
- You do **not** invent tokens in Python — they came from `run_async`

> **Tip:** If the UI later looks like it is repeating a growing paragraph, ADK is sending **cumulative** text (each chunk is the whole string so far). Replace the buffer. If chunks are short suffixes, append. Task 1’s dump tells you which one you have. Do not guess forever.

> **Watch out:** `is_final_response()` is False while function calls or responses are on the event — even if you also see text. Do not key the UI off “there is some text.”

### Scoreboard after Task 1

| Piece | In place? |
|-------|-----------|
| Live event dump (FINAL vs partial) | **Yes** |
| Codec (`encode_sse` / payloads) | Not yet |
| FastAPI SSE | Not yet |
| curl proof | Not yet |
| Human tool copy | Not yet |
| Stream vs schema note | Not yet |
| Error / timeout event | Not yet |

---

## Task 2 — Codec: Event → small dicts → SSE `data:` lines

### Why

Raw ADK events are richer than a handheld needs. Normalize to three payload types:

| `type` | Meaning |
|--------|---------|
| `tool_status` | A tool started or finished |
| `token` | Text that is **not** final |
| `final` | Text that **is** final |

SSE is a tiny framing rule: each event is one line starting with `data: `, then a **blank line**. That blank line is how the browser knows the event ended.

### Do this

1. Create the package:

```bash
mkdir -p project/meridian_ops/streaming
```

   `mkdir -p` creates the folder and does not error if it exists.

2. Create empty `project/meridian_ops/streaming/__init__.py`.

3. Create `project/meridian_ops/streaming/event_codec.py`. Start with `encode_sse` and the mapper. You will add human copy in Task 5.

```python
from __future__ import annotations

import json
from typing import Any

from google.adk.events.event import Event


def encode_sse(payload: dict[str, Any]) -> str:
    """One SSE event: 'data: ' + JSON + blank line terminator."""
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


def adk_event_to_payloads(event: Event) -> list[dict[str, Any]]:
    """Map one ADK Event to zero or more UI payloads."""
    out: list[dict[str, Any]] = []

    for call in event.get_function_calls():
        out.append(
            {
                "type": "tool_status",
                "phase": "start",
                "tool": call.name,
                "author": event.author,
            }
        )

    for resp in event.get_function_responses():
        out.append(
            {
                "type": "tool_status",
                "phase": "end",
                "tool": resp.name,
                "author": event.author,
            }
        )

    text = ""
    if event.content and event.content.parts:
        text = "".join(part.text for part in event.content.parts if part.text)

    if text:
        if event.is_final_response():
            out.append({"type": "final", "text": text, "author": event.author})
        else:
            out.append({"type": "token", "text": text, "author": event.author})

    return out
```

   Walk `encode_sse` first — three pieces, no extras:

   ```
   data:   ← SSE field name (required)
   {…}     ← your JSON payload
   \n\n    ← one newline ends the line; the second blank line ends the event
   ```

   `ensure_ascii=False` keeps pickup words like “5–7pm” readable instead of `\u2013`.

   Walk `adk_event_to_payloads` **field by field**:

   | Input | Output payload |
   |-------|----------------|
   | `get_function_calls()` item `.name` | `{type: tool_status, phase: start, tool: that name}` |
   | `get_function_responses()` item `.name` | `{type: tool_status, phase: end, tool: that name}` |
   | `content.parts` text + **not** final | `{type: token, text: …}` |
   | `content.parts` text + **is** final | `{type: final, text: …}` |
   | `event.author` | Copied onto every payload for debugging |
   | No calls, no text | Empty list — skip (do not send junk SSE) |

   One `Event` can produce **more than one** payload (a function call plus leftover text). That is why the function returns a **list**.

4. Create `project/meridian_ops/tests/test_event_codec.py`. Tests build **real** ADK `Event`s — same class as Task 1:

```python
from google.adk.events.event import Event
from google.genai import types

from meridian_ops.streaming.event_codec import adk_event_to_payloads, encode_sse


def test_encode_sse_starts_with_data_and_ends_with_blank_line():
    raw = encode_sse({"type": "final", "text": "Pickup ready"})
    assert raw.startswith("data: ")
    assert raw.endswith("\n\n")
    assert '"type": "final"' in raw


def test_function_call_is_tool_status_start():
    event = Event(
        author="meridian_order_status",
        invocation_id="inv-call",
        content=types.Content(
            role="model",
            parts=[
                types.Part.from_function_call(
                    name="get_order", args={"order_id": "MC-1048301"}
                )
            ],
        ),
    )
    payloads = adk_event_to_payloads(event)
    assert payloads == [
        {
            "type": "tool_status",
            "phase": "start",
            "tool": "get_order",
            "author": "meridian_order_status",
        }
    ]
    assert event.is_final_response() is False


def test_function_response_is_tool_status_end():
    event = Event(
        author="meridian_order_status",
        invocation_id="inv-resp",
        content=types.Content(
            role="user",
            parts=[
                types.Part.from_function_response(
                    name="get_order", response={"status": "success"}
                )
            ],
        ),
    )
    payloads = adk_event_to_payloads(event)
    assert payloads[0]["type"] == "tool_status"
    assert payloads[0]["phase"] == "end"
    assert payloads[0]["tool"] == "get_order"


def test_partial_text_is_token_not_final():
    event = Event(
        author="meridian_order_status",
        invocation_id="inv-partial",
        content=types.Content(
            role="model",
            parts=[types.Part.from_text(text="Order MC-1048301")],
        ),
        partial=True,
    )
    payloads = adk_event_to_payloads(event)
    assert payloads[0]["type"] == "token"
    assert event.is_final_response() is False


def test_complete_text_is_final():
    event = Event(
        author="meridian_order_status",
        invocation_id="inv-final",
        content=types.Content(
            role="model",
            parts=[types.Part.from_text(text="Order MC-1048301 is ready for pickup.")],
        ),
        partial=False,
    )
    payloads = adk_event_to_payloads(event)
    assert payloads[0]["type"] == "final"
    assert event.is_final_response() is True
```

5. Run:

```bash
cd /Users/alishaghatane/dev/agent-learn-sme
source .venv/bin/activate
export PYTHONPATH=project
pytest project/meridian_ops/tests/test_event_codec.py -v
```

   `-v` prints each test name.

### Expect

Five `PASSED` lines.

Sample SSE strings (this is the wire format Task 4 will show):

```
data: {"type": "status", "phase": "started", "session_id": "abc123"}

data: {"type": "tool_status", "phase": "start", "tool": "get_order", "author": "meridian_order_status"}

data: {"type": "token", "text": "Order MC-1048301"}

data: {"type": "final", "text": "Order MC-1048301 is ready for pickup between 5pm and 7pm."}

data: {"type": "status", "phase": "done", "session_id": "abc123"}
```

Each block ends with an empty line. That empty line **is** the protocol, not pretty-print.

> **Tip:** `encode_sse` is the only place that should add `data:` and `\n\n`. The FastAPI generator just `yield encode_sse(payload)`.

> **Watch out:** Never put API keys, raw card data, or OMS dumps into these payloads. Allowlist fields: `type`, `phase`, `tool`, `text`, `author`, `session_id`, `message`.

### Scoreboard after Task 2

| Piece | In place? |
|-------|-----------|
| Live event dump | Yes |
| Codec | **Yes** |
| FastAPI SSE | Not yet |
| curl proof | Not yet |
| Human tool copy | Not yet |
| Stream vs schema note | Not yet |
| Error / timeout event | Not yet |

---

## Task 3 — FastAPI SSE around the same Runner

### Why

Store apps speak HTTP. ADK speaks async events. The edge joins them.

Lesson 12’s `app.py` already does AuthN + `InMemoryRunner` for a **JSON** body. This lesson adds a **sibling** module for the stream. Do not replace `run_async` with fake tokens.

### Do this

1. Create `project/meridian_ops/deploy/stream_api.py`:

```python
from __future__ import annotations

import asyncio
from typing import AsyncIterator

from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import StreamingResponse
from google.adk.apps import App
from google.adk.runners import InMemoryRunner
from google.genai import types
from pydantic import BaseModel, Field

from meridian_order_status.agent import root_agent
from meridian_ops.streaming.event_codec import adk_event_to_payloads, encode_sse

api = FastAPI(title="Meridian OrderOps Stream")
adk_app = App(name="meridian_order_status", root_agent=root_agent)
runner = InMemoryRunner(app=adk_app)

LAB_KEY = "dev-local-key-change-me"


class StreamAsk(BaseModel):
    text: str = Field(min_length=1, max_length=4000)
    user_id: str = "devon_store"


@api.post("/v1/orderops/stream")
async def stream_orderops(
    body: StreamAsk,
    x_api_key: str | None = Header(default=None),
):
    if x_api_key != LAB_KEY:
        raise HTTPException(status_code=401, detail="unauthorized")

    async def gen() -> AsyncIterator[str]:
        session = await runner.session_service.create_session(
            app_name="meridian_order_status", user_id=body.user_id
        )
        yield encode_sse(
            {"type": "status", "phase": "started", "session_id": session.id}
        )
        msg = types.Content(
            role="user",
            parts=[types.Part.from_text(text=body.text)],
        )
        try:
            async with asyncio.timeout(60):
                async for event in runner.run_async(
                    user_id=body.user_id,
                    session_id=session.id,
                    new_message=msg,
                ):
                    for payload in adk_event_to_payloads(event):
                        yield encode_sse(payload)
                        await asyncio.sleep(0)
        except TimeoutError:
            yield encode_sse({"type": "error", "message": "timeout"})
            return
        except Exception:
            yield encode_sse({"type": "error", "message": "agent_failed"})
            return
        yield encode_sse(
            {"type": "status", "phase": "done", "session_id": session.id}
        )

    return StreamingResponse(gen(), media_type="text/event-stream")
```

   Walk the endpoint:

   | Piece | Why it is there |
   |-------|-----------------|
   | `Header(default=None)` on `x_api_key` | FastAPI reads the `x-api-key` HTTP header (same idea as Lesson 12) |
   | `401` if the key is wrong | Handhelds are still an API. No open stream on the LAN |
   | First yield `status/started` + `session_id` | Immediate ack so Devon’s spinner has an id |
   | `run_async` | Native event source — **not** a token faker |
   | `adk_event_to_payloads` then `encode_sse` | One Event → zero or more SSE frames |
   | `await asyncio.sleep(0)` | Yield to the event loop so FastAPI can **flush** the chunk instead of buffering the whole turn |
   | `asyncio.timeout(60)` | 60 seconds, then `error` / `timeout` (Task 7 uses this) |
   | `except Exception` → `agent_failed` | Client-visible; **no** stack trace on the wire |
   | Last yield `status/done` | Same `session_id` — audit can stitch start to finish |
   | `media_type="text/event-stream"` | Tells the client this is SSE, not JSON |

2. Start the server on **8088** so it does not collide with `adk web` (8000) or Lesson 12 (8080):

```bash
cd /Users/alishaghatane/dev/agent-learn-sme
source .venv/bin/activate
export PYTHONPATH=project
uvicorn meridian_ops.deploy.stream_api:api --reload --port 8088
```

   - `uvicorn` — ASGI server that runs FastAPI.
   - `meridian_ops.deploy.stream_api:api` — module **path** : **app variable** (`api = FastAPI(...)`).
   - `--reload` — restart when you save a Python file. Handy while you edit the codec. Turn it off in any shared environment.
   - `--port 8088` — listen on 8088.

3. In a **second** terminal, prove auth fails without a key:

```bash
curl -s -o /dev/null -w "%{http_code}\n" \
  -H "Content-Type: application/json" \
  -d '{"text":"Where is order MC-1048301?"}' \
  http://127.0.0.1:8088/v1/orderops/stream
```

   - `-s` — silent: hide the progress meter.
   - `-o /dev/null` — throw away the body; we only care about the status code.
   - `-w "%{http_code}\n"` — print the HTTP status code.
   - `-d` — POST body (curl uses POST when `-d` is present).

### Expect

Uvicorn prints `Uvicorn running on http://127.0.0.1:8088`.

The curl without `x-api-key` prints `401`.

> **Tip:** Keep Lesson 12’s `/v1/wismo` for callers that want one JSON blob. This stream is for Devon’s handheld. Same `InMemoryRunner` idea, different wait model.

> **Watch out:** `InMemoryRunner` sessions die when the process dies. That is fine for the lab. Lesson 29 is durable sessions.

### Scoreboard after Task 3

| Piece | In place? |
|-------|-----------|
| Live event dump | Yes |
| Codec | Yes |
| FastAPI SSE | **Yes** |
| curl proof | Not yet (auth 401 only) |
| Human tool copy | Not yet |
| Stream vs schema note | Not yet |
| Error / timeout event | Skeleton in the endpoint |

---

## Task 4 — curl SSE like a handheld

### Why

Prove the wire format before any UI framework. If curl cannot see progressive `data:` lines, a React app will not either.

Leave uvicorn running from Task 3.

### Do this

1. In the second terminal:

```bash
curl -N -s \
  -H "x-api-key: dev-local-key-change-me" \
  -H "Content-Type: application/json" \
  -d '{"text":"Where is order MC-1048301? Give Devon a pickup script."}' \
  http://127.0.0.1:8088/v1/orderops/stream
```

   Every flag:

   | Flag / header | Intent |
   |---------------|--------|
   | `-N` (`--no-buffer`) | Print bytes **as they arrive**. Without this, curl waits until the stream ends, which hides the whole point of SSE. |
   | `-s` (`--silent`) | Hide the progress meter so you only see `data:` lines. |
   | `-H "x-api-key: …"` | Same lab key as Lesson 12 / Task 3. Wrong value → 401. |
   | `-H "Content-Type: application/json"` | Tell FastAPI the body is JSON so `StreamAsk` can parse it. |
   | `-d '{...}'` | POST JSON. The `text` is Devon’s question. |
   | URL `/v1/orderops/stream` | The SSE route, not `/v1/wismo`. |

2. Watch the terminal. Lines should appear in **time**, not as one dump after 12 seconds. If they all appear at the end, `-N` is missing or a proxy is buffering.

### Expect

A sequence of `data: {...}` lines, including:

```
data: {"type": "status", "phase": "started", "session_id": "<id>"}

data: {"type": "tool_status", "phase": "start", "tool": "get_order", "author": "meridian_order_status"}

data: {"type": "tool_status", "phase": "end", "tool": "get_order", "author": "meridian_order_status"}

data: {"type": "token", "text": "…"}

data: {"type": "final", "text": "…ready for pickup…"}

data: {"type": "status", "phase": "done", "session_id": "<id>"}
```

`started` and `done` must share the **same** `session_id`.

You may see several `token` lines, or one `final` with little `token` traffic. Both are valid. You must see `final` (or an `error`) — never a hang with only `started`.

> **Tip:** If you see nothing, check the uvicorn terminal for a Python traceback. The stream error path should still emit `{"type":"error","message":"agent_failed"}`.

> **Watch out:** Posting to `/v1/wismo` on port **8080** is the Lesson 12 JSON API. This lesson is port **8088** and `/v1/orderops/stream`.

### Scoreboard after Task 4

| Piece | In place? |
|-------|-----------|
| Live event dump | Yes |
| Codec | Yes |
| FastAPI SSE | Yes |
| curl proof | **Yes** |
| Human tool copy | Not yet |
| Stream vs schema note | Not yet |
| Error / timeout event | Skeleton |

---

## Task 5 — Speak store language, not tool names

### Why

`tool_status tool=get_order` is engineer-speak. Devon needs:

> Checking OMS for the order…

Same payload, extra `message` field. The codec stays the single place that knows both names.

### Do this

1. Append this to `project/meridian_ops/streaming/event_codec.py` (keep the functions you already wrote):

```python
TOOL_COPY = {
    "get_order": "Checking OMS for the order…",
    "retrieve_policy": "Looking up Meridian policy…",
    "get_atp": "Checking store shelf availability…",
}


def humanize_tool(payload: dict[str, Any]) -> dict[str, Any]:
    if payload.get("type") != "tool_status":
        return payload
    tool = payload.get("tool", "")
    phase = payload.get("phase")
    base = TOOL_COPY.get(tool, f"Running {tool}…")
    out = dict(payload)
    out["message"] = base if phase == "start" else f"Finished: {tool}"
    return out
```

   Walk it:

   - Unknown `type` → return unchanged (`token` / `final` stay as-is).
   - `phase == "start"` → friendly sentence from `TOOL_COPY`.
   - `phase == "end"` → `Finished: get_order` so the spinner can stop.
   - Unknown tool → `Running {tool}…` so a new tool still has a line.

2. In `adk_event_to_payloads`, wrap each payload before append — or map them at the end:

```python
    return [humanize_tool(p) for p in out]
```

   Put that as the **return** of `adk_event_to_payloads` instead of `return out`.

3. Add a test to `test_event_codec.py`:

```python
def test_humanize_get_order_start():
    event = Event(
        author="meridian_order_status",
        invocation_id="inv-human",
        content=types.Content(
            role="model",
            parts=[
                types.Part.from_function_call(
                    name="get_order", args={"order_id": "MC-1048301"}
                )
            ],
        ),
    )
    payloads = adk_event_to_payloads(event)
    assert payloads[0]["message"] == "Checking OMS for the order…"
```

4. Re-run codec tests, then curl again (uvicorn `--reload` should have picked up the change):

```bash
export PYTHONPATH=project
pytest project/meridian_ops/tests/test_event_codec.py -v
```

### Expect

Tests still pass, plus `test_humanize_get_order_start`.

curl `tool_status` lines now include `"message": "Checking OMS for the order…"`.

> **Tip:** Keep `tool` **and** `message`. Logs grep `get_order`. The screen shows the sentence.

> **Watch out:** Do not put the tool’s **return dict** (order totals, emails) into `message`. Status copy is a label, not a data dump.

### Scoreboard after Task 5

| Piece | In place? |
|-------|-----------|
| Live event dump | Yes |
| Codec | Yes |
| FastAPI SSE | Yes |
| curl proof | Yes |
| Human tool copy | **Yes** |
| Stream vs schema note | Not yet |
| Error / timeout event | Skeleton |

---

## Task 6 — Stream the script; structure the refund

### Why

Lesson 20’s `RefundDecision` is JSON fields for Priya’s HITL form. Streaming those fields as tokens looks like garbage on a handheld:

```
{"dec
ision": "esc
alate_hitl"...
```

Devon needs a **narrative** script. Priya needs **fields**. Do both — on different surfaces.

### Do this

1. Create `project/meridian_ops/decisions/` if needed:

```bash
mkdir -p project/meridian_ops/decisions
```

2. Write `project/meridian_ops/decisions/22-stream-vs-schema.md`:

```markdown
# Lesson 22 — when to stream vs when to require schema

| Path | Surface | Shape | Why |
|------|---------|-------|-----|
| WISMO / BOPIS pickup script | Devon handheld | SSE `token` + `final` **text** | Latency; he reads sentences |
| Shortage “what do I tell the next five” | Devon handheld | SSE + tool status | Progress while OMS/ATP run |
| Refund ≥ $75 / POD dispute | Priya HITL UI | Lesson 20 `output_schema` `RefundDecision` on `final` or a second POST | Buttons need fields |
| Degraded model (Lesson 20) | Both | Stream an honest sentence; still no auto money | Flag stays on the JSON/ops blob |

Rules:
- Do not stream half-built schema JSON to the handheld.
- Do not treat SSE `token` text as a refund decision object.
- Score evals on the **final** text or the structured object — not every token.
```

   This is the same kind of durable file as Lesson 04’s tool-safety table. Six months from now, someone will try to “just stream the schema.” Point at this note.

### Expect

The file has a row for Devon (stream text) and a row for Priya (Lesson 20 schema). No row that says “one endpoint that half-streams broken JSON.”

> **Watch out:** A follow-up `POST /v1/orderops/decide` that reads the session and runs `refund_decision_agent` is the clean split. Do not bolt schema parsing onto every SSE token.

### Scoreboard after Task 6

| Piece | In place? |
|-------|-----------|
| Live event dump | Yes |
| Codec | Yes |
| FastAPI SSE | Yes |
| curl proof | Yes |
| Human tool copy | Yes |
| Stream vs schema note | **Yes** |
| Error / timeout event | Skeleton |

---

## Task 7 — Failure UX: never a silent hang

### Why

A spinner with zero events is worse than a slow JSON error. Devon retries. You double-submit.

The endpoint already:

- yields `error` / `timeout` after 60s
- yields `error` / `agent_failed` on other exceptions
- does **not** put `str(exc)` on the wire

Now prove the client can see those shapes, and that a tool miss still ends the stream.

### Do this

1. Confirm the `except` blocks in `stream_api.py` match Task 3 (timeout + `agent_failed`). If you skipped them, add them now.

2. Prove a **401** is still loud (not an empty SSE):

```bash
curl -N -s -D - \
  -H "Content-Type: application/json" \
  -d '{"text":"Where is order MC-1048301?"}' \
  http://127.0.0.1:8088/v1/orderops/stream | head
```

   - `-D -` — dump response **headers** to stdout (`-` means stdout). You should see `401`.
   - `head` — first lines only.

3. Prove a missing order still **finishes**. OMS should return `ORDER_NOT_FOUND`; the agent should say so; you should still get `final` or a clear sentence, then `done`:

```bash
curl -N -s \
  -H "x-api-key: dev-local-key-change-me" \
  -H "Content-Type: application/json" \
  -d '{"text":"Where is order MC-0000000?"}' \
  http://127.0.0.1:8088/v1/orderops/stream
```

4. Optional lab: temporarily set `asyncio.timeout(0.01)` , curl once, confirm you see `"message": "timeout"`, then **put 60 back**. Do not commit a 10ms timeout.

### Expect

- Wrong key → HTTP 401, not a hanging stream.
- Unknown order → stream **ends** with `done` (or `error`). No infinite spinner.
- Timeout path (if you probed it) → `data: {"type": "error", "message": "timeout"}`.
- Customer-facing text never includes a Python traceback.

> **Tip:** Evals (Lesson 08) score the **final** text / trajectory. Do not write an eval that asserts every token.

> **Watch out:** Swallowing exceptions with no `yield encode_sse({"type":"error"...})` is how the handheld spins forever.

### Scoreboard after Task 7

| Piece | In place? |
|-------|-----------|
| Live event dump | Yes |
| Codec | Yes |
| FastAPI SSE | Yes |
| curl proof | Yes |
| Human tool copy | Yes |
| Stream vs schema note | Yes |
| Error / timeout event | **Yes** |

---

## How it works (deeper dive)

```
ADK Event  →  adk_event_to_payloads  →  humanize_tool  →  encode_sse  →  handheld
                 │
                 ├─ tool_status (progress)
                 ├─ token (partial text)
                 └─ final (complete text)
```

Streaming does **not** remove:

- API-key auth on the edge  
- `session_id` for audit  
- HITL for money (Lesson 07 / 20)  
- evals on **finals**, not tokens  

`get_function_calls` / `get_function_responses` are the supported way to see tools on an `Event`. The codec calls them once per event. You do not re-parse `parts` for function names.

---

## Common pitfalls / troubleshooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| curl prints nothing until the end | Missing `-N`, or a proxy buffering | Add `-N`; hit localhost directly |
| Duplicate growing paragraphs | Cumulative partials | Replace the UI buffer on each `token` |
| UI treats every token as done | Keyed off “has text” | Key off `type=final` / `is_final_response()` |
| 401 loop | Wrong header name or key | Header is `x-api-key`; value `dev-local-key-change-me` |
| Secrets in SSE | Logged full tool dumps | Allowlist codec fields |
| Empty stream, uvicorn traceback | Exception before first yield | Keep `started` first; always `error` on failure |
| No `get_order` in the dump | Pointed at the Workflow package | Use `meridian_order_status` for this lesson |
| Homemade token loop | Replaced `run_async` | Put ADK back; SSE is transport only |
| `ModuleNotFoundError` | `PYTHONPATH` not set | `export PYTHONPATH=project` from repo root |

---

## You are done when

- [ ] Task 1 print loop shows `partial` vs `FINAL`, and `get_order` in calls or resps  
- [ ] Codec tests pass on real ADK `Event`s; SSE strings start with `data: ` and end with a blank line  
- [ ] `adk_event_to_payloads` maps calls/responses/text field by field  
- [ ] SSE endpoint streams with API-key auth (wrong key → 401)  
- [ ] `curl -N` shows progressive `data:` lines, including `started` / `final` / `done`  
- [ ] Tool status includes “Checking OMS for the order…”  
- [ ] `22-stream-vs-schema.md` says: stream narrative to Devon; schema for Priya  
- [ ] Errors/timeouts emit a client-visible `error` event; no traceback on the wire  

---

## Knowledge check

Answer from this lab.

1. Which ADK API yields the event stream? Name the three keyword arguments you passed.  
2. What HTTP media type did you use? What two characters terminate one SSE event after the JSON?  
3. When is `is_final_response()` false even if `content.parts` has text?  
4. Why humanize `get_order` for store ops?  
5. Should you stream half-built `RefundDecision` JSON to Devon’s handheld?  
6. What must every stream start and finish include for audit?

### Answers

1. `runner.run_async`. Keywords: `user_id`, `session_id`, `new_message`.  
2. `text/event-stream`. A blank line (`\n\n` after `data: …`).  
3. When `partial` is true, or the event still has function calls / function responses.  
4. Tool names do not help aisle decisions. “Checking OMS…” does.  
5. No. Stream a sentence; attach Lesson 20 schema on a final / second call for Priya.  
6. `session_id` on `status/started` and `status/done` (same id).

---

## Recap — Pack D

| Lesson | You can now… |
|--------|----------------|
| 18 | Hybrid RAG with citations + honest misses |
| 19 | ADK memory with write policy / PII boundaries |
| 20 | Route Flash vs Pro, fall back with `degraded`, emit `RefundDecision` |
| 21 | Multimodal POD disputes with tools + evidence grades |
| 22 | Stream progressive OrderOps UX over SSE from native `run_async` |

Together: **retrieve, remember, route, see, and stream** — still on ADK, still with a FastAPI edge.

**What you built today:** a handheld-friendly stream that wraps ADK events.  
**What you now understand:** FINAL vs partial; SSE framing; tool status as product copy.  
**What you can do next:** Lesson 23 attacks this surface (injection over the same edge).

---

## Stretch goal

Add a single HTML file that uses `EventSource` **or** `fetch` + `ReadableStream` to render `message` + `token` + `final`. It must call **this** FastAPI URL with the lab API key. No second agent runtime in the browser.

---

## Feedback

- Could you sketch the SSE payload types (`status`, `tool_status`, `token`, `final`, `error`) from memory?  
- What was harder: FINAL vs partial, SSE flushing (`-N` / `sleep(0)`), or keeping schema off the handheld?  
- Note the **task number** and what you expected vs what happened (command + first lines of output).

---

## Navigate

**← Prev** [Lesson 21 — Multimodal OrderOps](21-multimodal-orderops.md)  
**Track home:** [README](../README.md)  
**Native standard:** [NATIVE-ADK.md](../docs/NATIVE-ADK.md)  
**Next →** [Lesson 23 — Red teaming & adversarial robustness](23-red-teaming-adversarial-robustness.md)
