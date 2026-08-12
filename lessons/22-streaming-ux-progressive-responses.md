# Lesson 22 — Streaming UX & progressive responses

**Level:** Advanced  
**Time:** ~120 minutes  
**Prerequisites:** Lessons 12, 17, 20, 21 (FastAPI edge, Runner events, tools, multimodal optional)  
**Lab outcome:** Stream OrderOps **token/event progress** from ADK `run_async` to a store-ops client via **SSE**, including partial tool status — without blocking Devon’s screen for the full trajectory

**Standard:** [docs/NATIVE-ADK.md](../docs/NATIVE-ADK.md)

---

## At a glance

| Layer | Job |
|-------|-----|
| ADK `Runner.run_async` | Yields **events** as the agent thinks/calls tools/writes text |
| FastAPI edge | Auth + **SSE** (`text/event-stream`) to the browser/app |
| Store-ops UI | Shows “Looking up order…” then tokens, then final answer |
| Domain rules | Never stream secrets; mark finals clearly |

**Forbidden:** Replacing ADK with a DIY token generator.  
**Allowed:** Thin SSE adapter around native events (same pattern as Lesson 12/17).

---

## Why this matters

Devon on a handheld in aisle 4:

> “DC shorted SKU 884210 — what do I tell the next five pickup customers?”

If the API waits 12 seconds for one JSON blob, Devon retries, double-submits, and invents an answer.

Progressive UX:

1. Immediate ack  
2. Tool status: `get_order` / inventory lookup running  
3. Tokens of the customer-facing script as they arrive  
4. Final event with session id for audit

Streaming is not cosmetic — it is how ops tools feel trustworthy under latency.

---

## Know these

| Term | Meaning |
|------|---------|
| **Event stream** | Sequence of ADK `Event`s from `runner.run_async` |
| **Partial text** | Incomplete model text chunks before the final response |
| **Final response** | `event.is_final_response()` — safe to treat as complete answer |
| **SSE** | Server-Sent Events: HTTP long-lived stream of `data: ...\n\n` |
| **Tool status** | UX signal when a function call starts/finishes |
| **Progressive disclosure** | Show useful mid-states without lying that work is done |

```
Client                    FastAPI                         ADK Runner
  │  POST /stream            │                               │
  │─────────────────────────►│  run_async(...)               │
  │                          │──────────────────────────────►│
  │  SSE: status tool=...    │◄──── function_call event ─────│
  │  SSE: token "Pickup..."  │◄──── partial text ────────────│
  │  SSE: final {...}        │◄──── is_final_response ───────│
```

---

## Task 1 — Observe native events (before UX)

### Why

You cannot stream what you have not inspected.

### Do this

```bash
cd /Users/alishaghatane/dev/agent-learn-sme/project
export PYTHONPATH=.
python - <<'PY'
import asyncio
from google.adk.apps import App
from google.adk.runners import InMemoryRunner
from google.genai import types
from meridian_orderops.agent import root_agent  # or your Lesson 20 routed agent

async def main():
    app = App(name="meridian_orderops", root_agent=root_agent)
    runner = InMemoryRunner(app=app)
    session = await runner.session_service.create_session(
        app_name="meridian_orderops", user_id="devon"
    )
    msg = types.Content(
        role="user",
        parts=[types.Part.from_text(text="Where is order MC-1048301 for pickup?")],
    )
    async for event in runner.run_async(
        user_id="devon", session_id=session.id, new_message=msg
    ):
        kind = "FINAL" if event.is_final_response() else "partial"
        text = None
        if event.content and event.content.parts:
            text = "".join(p.text or "" for p in event.content.parts)
        print(kind, getattr(event, "author", None), (text or "")[:120])

asyncio.run(main())
PY
```

### Expect

Multiple lines: tool-related and/or partial text, then a `FINAL` line.

> **Tip:** Print `event.model_dump()` once (redacted) in a scratch file if fields differ by ADK version — learn *your* event shape.

---

## Task 2 — Normalize events for the client

### Why

Raw ADK events are richer than a handheld UI needs. Normalize to a small contract.

### Do this

Create `project/meridian_ops/streaming/event_codec.py`:

```python
from __future__ import annotations

import json
from typing import Any


def encode_sse(payload: dict[str, Any]) -> str:
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


def adk_event_to_payloads(event: Any) -> list[dict[str, Any]]:
    """Map one ADK event to zero-or-more UI payloads."""
    out: list[dict[str, Any]] = []

    # Tool call signals (attribute names can vary — defend with getattr)
    fc = getattr(event, "get_function_calls", None)
    calls = fc() if callable(fc) else None
    if calls:
        for call in calls:
            out.append(
                {
                    "type": "tool_status",
                    "phase": "start",
                    "tool": getattr(call, "name", "tool"),
                }
            )

    fr = getattr(event, "get_function_responses", None)
    resps = fr() if callable(fr) else None
    if resps:
        for resp in resps:
            out.append(
                {
                    "type": "tool_status",
                    "phase": "end",
                    "tool": getattr(resp, "name", "tool"),
                }
            )

    text = ""
    content = getattr(event, "content", None)
    if content and getattr(content, "parts", None):
        text = "".join(p.text or "" for p in content.parts if getattr(p, "text", None))

    if text:
        if event.is_final_response():
            out.append({"type": "final", "text": text})
        else:
            out.append({"type": "token", "text": text})

    return out
```

Unit test: fake objects with `is_final_response`, `content.parts`, and ensure SSE strings start with `data: `.

### Expect

Codec turns events into `tool_status` / `token` / `final` dicts.

> **Watch out:** Some versions stream many partials that *repeat* growing text; others send deltas. Detect once and document in a comment — don’t guess forever.

---

## Task 3 — FastAPI SSE endpoint around ADK Runner

### Why

Store apps speak HTTP. ADK speaks async events. The edge joins them.

### Do this

Extend Lesson 12 app or create `project/meridian_ops/deploy/stream_api.py`:

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

from meridian_orderops.agent import root_agent
from meridian_ops.streaming.event_codec import adk_event_to_payloads, encode_sse

api = FastAPI(title="Meridian OrderOps Stream")
adk_app = App(name="meridian_orderops", root_agent=root_agent)
runner = InMemoryRunner(app=adk_app)


class StreamAsk(BaseModel):
    text: str = Field(min_length=1, max_length=4000)
    user_id: str = "devon_store"


@api.post("/v1/orderops/stream")
async def stream_orderops(
    body: StreamAsk,
    x_api_key: str | None = Header(default=None),
):
    if x_api_key != "dev-local-key-change-me":
        raise HTTPException(401, "unauthorized")

    async def gen() -> AsyncIterator[str]:
        session = await runner.session_service.create_session(
            app_name="meridian_orderops", user_id=body.user_id
        )
        yield encode_sse(
            {"type": "status", "phase": "started", "session_id": session.id}
        )
        msg = types.Content(
            role="user",
            parts=[types.Part.from_text(text=body.text)],
        )
        try:
            async for event in runner.run_async(
                user_id=body.user_id,
                session_id=session.id,
                new_message=msg,
            ):
                for payload in adk_event_to_payloads(event):
                    # Never put API keys / raw card data into payloads
                    yield encode_sse(payload)
                    await asyncio.sleep(0)  # let loop flush
        except Exception as exc:  # noqa: BLE001 — map typed errors in prod
            yield encode_sse({"type": "error", "message": "agent_failed"})
            raise exc
        yield encode_sse({"type": "status", "phase": "done", "session_id": session.id})

    return StreamingResponse(gen(), media_type="text/event-stream")
```

Run:

```bash
uvicorn meridian_ops.deploy.stream_api:api --reload --port 8088
```

### Expect

Server boots; unauthorized requests get 401.

---

## Task 4 — Client: curl SSE like a handheld

### Why

Prove the wire format before any UI framework.

### Do this

```bash
curl -N -s \
  -H "x-api-key: dev-local-key-change-me" \
  -H "Content-Type: application/json" \
  -d '{"text":"Where is order MC-1048301? Give Devon a pickup script."}' \
  http://127.0.0.1:8088/v1/orderops/stream
```

### Expect

A sequence of `data: {...}` lines including:

- `status/started` with `session_id`  
- optional `tool_status`  
- `token` and/or `final`  
- `status/done`

> **Tip:** `-N` disables curl buffering so you see progress live.

---

## Task 5 — Progressive tool status copy (ops language)

### Why

`tool_status tool=get_order` is engineer-speak. Devon needs human status.

### Do this

Add a map in `event_codec.py` or a thin UI helper:

```python
TOOL_COPY = {
    "get_order": "Checking OMS for the order…",
    "retrieve_policy_hybrid": "Looking up Meridian policy…",
    "get_inventory": "Checking store/DC availability…",
}


def humanize_tool(payload: dict) -> dict:
    if payload.get("type") != "tool_status":
        return payload
    tool = payload.get("tool", "")
    phase = payload.get("phase")
    base = TOOL_COPY.get(tool, f"Running {tool}…")
    payload = dict(payload)
    payload["message"] = base if phase == "start" else f"Finished: {tool}"
    return payload
```

Apply `humanize_tool` before `encode_sse`.

### Expect

SSE shows “Checking OMS…” during lookup.

---

## Task 6 — Streaming + structured final (best of both)

### Why

Handhelds like tokens; automation likes schemas. Do both: stream progress, finalize structured.

### Do this

After the stream completes (or on `final`), optionally run Lesson 20 `refund_decision_agent` **only** for refund intents — or have the stream’s last payload include both:

```json
{"type": "final", "text": "...", "session_id": "..."}
```

And a follow-up non-stream `POST /v1/orderops/decide` that reads session state / evidence brief into `output_schema`.

Minimum for this lesson:

1. Stream WISMO script for Devon  
2. Separate structured path for refund tickets (reuse Lesson 20)  
3. Document in `project/meridian_ops/decisions/22-stream-vs-schema.md` when you stream vs when you require schema-first

### Expect

A short decision note — not one endpoint that half-streams broken JSON.

> **Watch out:** Streaming raw `output_schema` JSON tokens to humans looks like garbage. Stream narrative; attach schema on `final` or a second call.

---

## Task 7 — Failure UX (timeouts, tool errors)

### Why

Silent SSE death is worse than a slow JSON error.

### Do this

Add:

1. Client-visible `{"type":"error","message":"agent_failed"}` (already sketched)  
2. A lab timeout wrapper (e.g., `asyncio.wait_for(..., timeout=60)`) that emits `error` with `message=timeout`  
3. Verify tool failure surfaces as status + honest final (“OMS unavailable — try again / call lead”) via agent instructions — not empty stream end

Simulate by pointing `get_order` at a broken fixture briefly, run curl, confirm you still get an `error` or a clear final.

### Expect

No infinite spinner with zero events.

---

## How it works (deeper dive)

```
ADK events  →  codec  →  SSE  →  store UI
                 │
                 ├─ tool_status (progress)
                 ├─ token (partial text)
                 └─ final (complete text)
```

Streaming does not remove the need for:

- auth on the edge  
- session ids for audit  
- HITL for money  
- evals on finals (score the final text/trajectory, not every token)

---

## Common pitfalls / troubleshooting

| Symptom | Fix |
|---------|-----|
| curl shows nothing until end | Use `curl -N`; disable proxy buffering |
| Duplicate growing paragraphs | Your ADK sends cumulative partials — send deltas or replace UI buffer |
| Secrets in SSE | Codec allowlist fields; never echo headers/tools raw dumps |
| 401 loops | Check `x-api-key` |
| UI treats every token as final | Key off `type=final` / `is_final_response` |
| DIY websocket agent runtime | Keep ADK Runner; WS/SSE is transport only |

---

## You are done when

- [ ] You can describe your ADK event shapes from a live dump  
- [ ] Codec maps to `tool_status` / `token` / `final`  
- [ ] SSE endpoint streams with API key auth  
- [ ] curl `-N` shows progressive lines  
- [ ] Tool status uses human copy for Devon  
- [ ] Errors/timeouts emit a client-visible event  
- [ ] Note written on stream vs structured-final split  

---

## Knowledge check

1. Which ADK API yields the event stream?  
2. What HTTP media type did you use for progressive updates?  
3. Why humanize tool names for store ops?  
4. Should you stream half-built JSON schema objects to Devon’s handheld?  
5. What must every stream start/finish include for audit?

### Answers

1. `Runner.run_async` (async iterator of events).  
2. `text/event-stream` (SSE).  
3. Engineers’ tool names don’t help aisle decisions — status copy does.  
4. No — stream narrative; attach structured decisions at final / second call.  
5. `session_id` (and ideally correlation id) on start/done.

---

## Recap — Pack D

| Lesson | You can now… |
|--------|----------------|
| 18 | Hybrid RAG with citations + honest misses |
| 19 | ADK memory with write policy / PII boundaries |
| 20 | Route models, fall back, emit structured decisions |
| 21 | Multimodal POD disputes with tools + evidence grades |
| 22 | Stream progressive OrderOps UX over SSE |

Together: **retrieve, remember, route, see, and stream** — the knowledge/model surface of a world-class Meridian agent engineer.

---

## Stretch goal

Add a tiny browser page (single HTML file) that listens to SSE and renders tool status + tokens — still calling your FastAPI edge, still ADK underneath.

---

## Feedback

- Could you sketch the SSE payload types from memory?  
- What was harder: event shape discovery, SSE flushing, or final vs partial?  
- Note task number + expected vs actual.

---

## Navigate

**← Prev** [Lesson 21 — Multimodal OrderOps](21-multimodal-orderops.md)  
**Track home:** [README](../README.md)  
**Native standard:** [NATIVE-ADK.md](../docs/NATIVE-ADK.md)  
**Next:** [Lesson 23 — Red teaming & adversarial robustness](23-red-teaming-adversarial-robustness.md)
