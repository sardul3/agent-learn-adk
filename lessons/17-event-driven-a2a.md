# Lesson 17 — Event-driven agents & A2A (native ADK)

**Level:** Advanced  
**Time:** ~120 minutes  
**Prerequisites:** Lessons 12–16  
**Lab outcome:** Webhooks invoke **ADK `Runner`/`App`**; A2A uses **`to_a2a` / `RemoteA2aAgent`** — no fake PubSub framework or DIY A2A protocol

**Standard:** [docs/NATIVE-ADK.md](../docs/NATIVE-ADK.md)

---

## At a glance

| Concern | Native / allowed |
|---------|------------------|
| Run agent on event | `App` + `Runner.run_async` (or `InMemoryRunner`) |
| HTTP webhook edge | FastAPI/Flask **thin** adapter → Runner |
| Idempotency | Domain processed-event store (OK) + money keys |
| A2A provider | ADK `to_a2a(root_agent|Workflow)` |
| A2A consumer | `RemoteA2aAgent` in a Workflow/agent tree |
| Queues | Cloud Pub/Sub / etc. **infra**; handler still calls Runner |

**Forbidden:** `FakePubSub` as a teaching substitute for learning ADK; DIY `LocalPolicyRemote` A2A stacks.

---

## Why this matters

Events and remote agents are how Meridian scales beyond chat. The orchestration engine remains ADK.

---

## Know these

| Term | Meaning |
|------|---------|
| **Runner** | ADK entrypoint that executes an app/agent on a message |
| **to_a2a** | Expose an ADK agent/Workflow as an A2A server |
| **RemoteA2aAgent** | ADK agent node that calls a remote A2A agent card/URL |
| **Agent card** | Discovery metadata for A2A |

---

## Task 1 — Webhook → native Runner

### Why

Webhooks should not reimplement agent loops.

### Do this

Create `project/meridian_ops/deploy/events_api.py` (or extend Lesson 12 app):

```python
from fastapi import FastAPI, Header, HTTPException, Request
from google.adk.apps import App
from google.adk.runners import InMemoryRunner
from google.genai import types

from meridian_orderops.agent import root_agent

app = FastAPI()
adk_app = App(name="meridian_orderops", root_agent=root_agent)
runner = InMemoryRunner(app=adk_app)

# Use a durable session service in real stage/prod (Lesson 29).


@app.post("/v1/events/oms")
async def oms_event(request: Request, x_api_key: str | None = Header(default=None)):
    if x_api_key != "dev-local-key-change-me":
        raise HTTPException(401, "unauthorized")
    body = await request.json()
    event_id = str(body.get("id") or "")
    # Domain idempotency (allowed): skip if event_id already processed.
    order_id = (body.get("data") or {}).get("order_id")
    text = f"OMS event for {order_id}: {body}"
    session = await runner.session_service.create_session(
        app_name="meridian_orderops", user_id="oms_webhook"
    )
    finals = []
    async for event in runner.run_async(
        user_id="oms_webhook",
        session_id=session.id,
        new_message=types.Content(
            role="user",
            parts=[types.Part.from_text(text=text)],
        ),
    ):
        if getattr(event, "content", None):
            finals.append(event)
    return {"status": "ok", "event_id": event_id, "session_id": session.id}
```

Use fixture `project/meridian_ops/fixtures/events/oms_delivered.json` (create if missing).

### Expect

`curl` webhook returns `ok` and ADK ran OrderOps — no custom graph invoke API.

---

## Task 2 — Idempotent event handling (domain, thin)

### Why

At-least-once delivery is real; ADK doesn’t replace event dedupe.

### Do this

Keep a **small** processed-id set/store for webhook `event_id`s. This is messaging hygiene, not an agent framework.

Test: same OMS event twice → second short-circuits before `run_async`.

### Expect

Duplicate suppressed; still no DIY agent runtime.

---

## Task 3 — Expose Policy agent with `to_a2a`

### Why

A2A provider should be ADK’s helper.

### Do this

```bash
python - <<'PY'
import pkgutil, google.adk as adk
print([n.name for n in pkgutil.walk_packages(adk.__path__, adk.__name__+'.') if 'a2a' in n.name.lower()][:40])
PY
```

Follow your install’s docs for `to_a2a` (often `google.adk.a2a.to_a2a` or similar).

Expose `project/meridian_policy_a2a` agent:

```python
# pattern — adapt import path to your ADK version
from google.adk.a2a import to_a2a  # verify path via inspect
from meridian_policy_a2a.agent import root_agent

a2a_app = to_a2a(root_agent)
# serve via ADK/uvicorn as documented
```

Record the exact import + serve command in `project/meridian_ops/decisions/17-a2a.md`.

### Expect

Agent card URL reachable (localhost). No hand-written A2A JSON-RPC stack.

---

## Task 4 — Consume with `RemoteA2aAgent`

### Why

OrderOps should call Policy over A2A natively.

### Do this

```python
from google.adk.agents import RemoteA2aAgent  # confirm path
from google.adk.workflow import Workflow

policy_remote = RemoteA2aAgent(
    name="policy_remote",
    agent_card="http://127.0.0.1:8000/a2a/meridian_policy_a2a/.well-known/agent-card.json",
    # URL path per your to_a2a serving layout
)

# Example: POLICY route points to RemoteA2aAgent instead of in-process policy LlmAgent
```

Wire into a Workflow edge (or temporary consumer package) and run one policy question.

If `RemoteA2aAgent` constructor differs, adapt to docs — **do not** invent `LocalPolicyRemote`.

### Expect

Trajectory shows remote A2A call; citation comes from policy agent tools.

---

## Task 5 — Queue workers: infra + Runner (no FakePubSub curriculum)

### Why

Pub/Sub is infrastructure. The worker body is still `runner.run_async`.

### Do this

In `17-a2a.md`, write a worker pseudocode that uses **real** client libs you choose (Google Pub/Sub or Redis Streams), where each message:

1. Dedupes by message id  
2. Calls ADK `Runner`  
3. Acks on success  

Optional stretch: implement against a real emulator — not a teaching `FakePubSub` class as the main lab.

### Expect

Design review can say “queue → Runner” without a third orchestration library.

---

## How it works (deeper dive)

```
Webhook/Queue → Auth + idempotency → ADK Runner/App → Workflow/LlmAgent
                                                      └─ RemoteA2aAgent → Policy service
```

Sub-agent `transfer` (Lesson 05) = in-process.  
A2A = cross-process/deployable ownership boundary.

---

## Common pitfalls / troubleshooting

| Symptom | Fix |
|---------|-----|
| Rebuilt LocalPolicyRemote | Use `RemoteA2aAgent` |
| Webhook embeds MeridianGraph | Call `Runner` only |
| A2A import path differs | Inspect installed package; don’t invent protocol |
| `to_a2a(JoinNode)` errors | Expose `Workflow` or `LlmAgent` roots only |

---

## You are done when

- [ ] Webhook uses ADK Runner  
- [ ] Event dedupe is thin domain logic  
- [ ] Policy exposed via `to_a2a` (or documented exact ADK API)  
- [ ] Consumer uses `RemoteA2aAgent`  
- [ ] Queue design doc says Runner — no FakePubSub core lab  

---

## Knowledge check

1. What ADK API runs an agent for a webhook message?  
2. What ADK type calls a remote agent?  
3. What ADK helper exposes an agent over A2A?  
4. Why is event idempotency still needed?

### Answers

1. `Runner.run_async` (via `App`)  
2. `RemoteA2aAgent`  
3. `to_a2a(...)`  
4. At-least-once delivery duplicates messages  

---

## Recap — Pack C (native)

| Lesson | Native focus |
|--------|----------------|
| 13 | `Workflow` + routes |
| 14 | `JoinNode` + routed loops |
| 15 | `RequestInput` resume |
| 16 | `McpToolset` |
| 17 | `Runner` + `RemoteA2aAgent` / `to_a2a` |

---

## Stretch goal

Put `RemoteA2aAgent` on the POLICY edge of `meridian_orderops` Workflow.

---

## Feedback

- Could you add a second event type without a new orchestrator?  
- Note task number + expected vs actual.

---

## Navigate

**← Prev** [Lesson 16 — MCP & tool ecosystems](16-mcp-tool-ecosystems.md)  
**Track home:** [README](../README.md)  
**Native standard:** [NATIVE-ADK.md](../docs/NATIVE-ADK.md)  
**Next pack:** Lesson 18 — Advanced RAG