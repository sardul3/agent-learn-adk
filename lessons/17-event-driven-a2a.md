# Lesson 17 — Event-driven agents & A2A (native ADK)

**Level:** Advanced  
**Time:** ~120–150 minutes  
**Prerequisites:** Lessons 12–16 (FastAPI edge, OrderOps `Workflow`, MCP). Lesson 13’s routing-map graph must load.  
**Lab outcome:** OMS webhooks invoke **ADK `App` + `InMemoryRunner.run_async`**. Policy is exposed with **`to_a2a`** and consumed with **`RemoteA2aAgent`**. No `FakePubSub`. No DIY A2A stack.

**Standard:** [docs/NATIVE-ADK.md](../docs/NATIVE-ADK.md)

---

## At a glance

Chat is how you demo. Events and remote agents are how Meridian scales past one browser tab.

Two native seams, one lesson:

| Seam | Native ADK / allowed edge | Forbidden stand-in |
|------|---------------------------|--------------------|
| Ticket arrives as HTTP | FastAPI → `App` → `InMemoryRunner.run_async` | A second agent loop inside the handler |
| Policy lives in another process | `to_a2a(root_agent)` server + `RemoteA2aAgent` client | `LocalPolicyRemote`, hand-rolled JSON-RPC, “lab doubles” |
| Queue (Pub/Sub, Redis) | **Infra**. Worker body is the same handler: auth → idempotency → `run_async` | A teaching `FakePubSub` class as the lab |

You will **not** invent an event bus that *is* the orchestrator. ADK remains the engine. FastAPI is the door.

| Task | What you do | Who enforces it | How you prove it |
|------|-------------|-----------------|------------------|
| 1 | Walk Lesson 12’s FastAPI edge: API key, session, `run_async` | Existing `deploy/app.py` | `uvicorn` + `curl` `/v1/wismo` |
| 2 | Add `/v1/events/oms` with **idempotency** | Your Python, before the Runner | `pytest` — duplicate never calls Gemini |
| 3 | Hit the webhook with the OMS fixture | Same app | `curl` twice: `ok` then `duplicate` |
| 4 | Expose Policy with **`to_a2a`** | ADK Starlette app | Agent card GET |
| 5 | Consume it with **`RemoteA2aAgent`** | ADK agent node | Construction pytest + one live policy question |

If you get lost, scroll back to this table. Each task fills one row. The scoreboard at the end of every task repeats the same rows.

---

## Why this matters

Maya’s order `MC-1048292` flips to **delivered** in OMS. There is **no POD photo**. She has not opened the app yet.

If OrderOps only runs when someone types in `adk web`, that lifecycle change sits on a shelf until Monday. If a webhook *reimplements* the agent (“call Gemini, parse JSON, if refund then…”), you now have two orchestrators and Lesson 13’s graph is decoration.

Same afternoon, Store 441’s policy wiki is owned by **another team**, another deploy, another SLO. Lesson 05’s in-process `policy_agent` cannot cross that boundary. Agent-to-agent (**A2A**) is the native protocol ADK already speaks: one process **serves** an agent card, another process has a `RemoteA2aAgent` node that calls it.

Two failure modes, one lesson:

1. **The event path** — OMS fires twice (at-least-once delivery). Without an idempotency key, you run the Workflow twice and Priya sees two “we’re looking into it” texts.
2. **The remote path** — you copy Policy’s tools into OrderOps “just for the demo.” Six months later nobody knows which process owns `POL-REFUND-04`.

---

## Know these

Read this table before Task 1. Every later task reuses these words.

| Term | Plain English | Meridian example |
|------|---------------|------------------|
| **Edge / façade** | HTTP API in front of the agent. Auth and shape live here. Orchestration does not. | FastAPI in `deploy/app.py` |
| **Webhook** | HTTP POST some other system sends when something happened | OMS `oms.lifecycle_changed` for `MC-1048292` |
| **`App`** | ADK container: a name plus `root_agent` (agent **or** Workflow) | `App(name="meridian_orderops", root_agent=root_agent)` |
| **`InMemoryRunner`** | ADK runner with in-memory session / memory / artifacts | Lab and pytest. Stage needs a durable session service (Lesson 29). |
| **`run_async`** | Native event stream: one user message in, ADK events out | The webhook’s only way to “run the agent” |
| **API key header** | Shared secret on `X-Api-Key`. Not end-user login. | `require_api_key` → 401 if missing/wrong |
| **Idempotency** | Same event id twice → same recorded result, **no second run** | `oms-evt-10001` replayed by OMS |
| **At-least-once** | Brokers retry. Duplicates are normal. | OMS webhook timeout → retry |
| **A2A** | Agent-to-agent protocol. Process boundary with a card and RPC. | Policy service ↔ OrderOps |
| **`to_a2a`** | ADK helper: `LlmAgent` or `Workflow` → Starlette A2A app | Policy provider |
| **Agent card** | Discovery JSON: name, skills, RPC URL | `/.well-known/agent-card.json` |
| **`rpc_path`** | Prefix so two agents on one port do not collide | `/meridian_policy_a2a/` |
| **`RemoteA2aAgent`** | ADK node that **calls** a card URL. Looks like an agent in a graph. | Policy consumer |
| **Sub-agent transfer** | Lesson 05 — **in-process** specialist | Not A2A. Same Python process. |

### Picture this: the loading dock vs a second store

| Approach | Store 441 analogue | What goes wrong |
|----------|--------------------|-----------------|
| FastAPI → `run_async` | Dock scanner that starts the **existing** floor map (Lesson 13 graph) | Auth lives at the door. Path law stays in `Workflow`. |
| Handler that calls Gemini itself | Building a second store in the parking lot | Two orchestrators. Evals lie. |
| `to_a2a` + `RemoteA2aAgent` | Phone the policy office; they have their own binder | Ownership boundary is a URL + a card |
| DIY `LocalPolicyRemote` | Writing your own phone company | You now maintain a protocol |
| `FakePubSub` as the lab | A cardboard conveyor you pretend is the dock | You learned the cardboard, not the scanner |

```
OMS / curl / Pub/Sub worker
        │  POST /v1/events/oms
        │  X-Api-Key + event id
        ▼
FastAPI edge  ── 401 if key wrong
        │
        ├── event id seen? ──yes──► return duplicate (no Runner)
        │
        no
        ▼
  create_session + Runner.run_async
        ▼
  OrderOps Workflow (Lesson 13)
        │
        └── POLICY hop (Task 5) ──► RemoteA2aAgent ──HTTP──► to_a2a(Policy)
```

> **Tip:** Lesson 05 `transfer_to_agent` is a coworker at the **same** desk. A2A is a coworker in **another building**. Both are native. They are not interchangeable.

---

## What you already have (do not rebuild)

From the **repo root**, confirm these exist. Lesson 12 shipped the edge. Lesson 13 shipped the graph. Lesson 06 shipped `retrieve_policy`.

| Path | Job |
|------|-----|
| `project/meridian_ops/deploy/app.py` | FastAPI → `App` + `InMemoryRunner`. You **walk and extend** this file. |
| `project/meridian_ops/deploy/requirements.txt` | `fastapi`, `uvicorn`, `pydantic-settings` |
| `project/meridian_orderops/agent.py` | Native `Workflow` (routing map from Lesson 13) |
| `project/meridian_ops/fixtures/events/oms_delivered.json` | OMS envelope for `MC-1048292` |
| `project/meridian_policy_a2a/agent.py` | Policy `LlmAgent` + `retrieve_policy` — A2A **provider** root |
| `project/meridian_ops/a2a/__init__.py` | Empty-ish package. You will turn it into a **consumer**, not a protocol double. |
| `.venv/` | Already exists. Source it. |

You will **add / change**:

```
project/meridian_ops/deploy/app.py              Task 1–2 (webhook + idempotency; drop fallback)
project/meridian_ops/tests/test_oms_webhook.py  Task 2
project/meridian_policy_a2a/agent.py            Task 4 (model bump)
project/meridian_policy_a2a/a2a_app.py          Task 4 (to_a2a Starlette app)
project/meridian_ops/a2a/consumer.py            Task 5 (RemoteA2aAgent)
project/meridian_policy_remote/                 Task 5 (adk web doorbell)
project/meridian_ops/tests/test_a2a_consumer.py Task 5
```

If `deploy/app.py` is missing, stop and finish Lesson 12. If the OrderOps graph still uses 3-tuple `"WISMO"` edges, stop and finish Lesson 13 Task 2 — the webhook will fail the moment it imports `root_agent`.

---

## Task 1 — Walk the FastAPI edge (API key → session → `run_async`)

### Why

A webhook that does not call ADK is a stub. A webhook that *is* an agent loop is a second framework. Lesson 12 already wrote the honest shape. You will read it line by line **before** you add events, so the new route copies a known-good `run_async` — it does not invent one.

### Do this

1. Activate the **existing** venv. Do not recreate it.

```bash
cd /Users/alishaghatane/dev/agent-learn-sme
source .venv/bin/activate
python -c "import google.adk as adk; print(adk.__version__)"
```

   Expect `2.6.3`. If `google.adk` is missing: `pip install "google-adk==2.6.3"` into this venv — still no `python -m venv`.

2. Open `project/meridian_ops/deploy/app.py`. The file **as shipped** still has a try/except fallback `LlmAgent` when OrderOps fails to import. That was a Lesson 12 safety net. It is version hedging. **Delete the fallback.** Production (and this lab) must fail loud if the Workflow cannot load.

   Replace the import block at the top (keep the other imports) so the agent line is:

```python
from meridian_orderops.agent import root_agent
```

   Remove the `try` / `except ImportError` that builds `meridian_order_status_fallback`. If `root_agent` cannot import, you want that traceback — it usually means Lesson 13’s routing map is not in place.

3. Walk the settings and the ADK objects that already exist:

```python
class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="MERIDIAN_", extra="ignore")

    api_key: str = "dev-local-key-change-me"
    env: str = "local"
    model_name: str = "gemini-2.5-flash"
    git_sha: str = "unknown"
    image_tag: str = "dev"


settings = Settings()

api = FastAPI(title="Meridian OrderOps API", version="0.1.0")
adk_app = App(name="meridian_orderops", root_agent=root_agent)
runner = InMemoryRunner(app=adk_app)
```

   | Piece | Why it is here |
   |-------|----------------|
   | `env_prefix="MERIDIAN_"` | `MERIDIAN_API_KEY` binds to `api_key`. Secrets stay in the environment. |
   | `api = FastAPI(...)` | The Starlette/FastAPI **edge**. This is what uvicorn loads (`meridian_ops.deploy.app:api`). |
   | `App(name="meridian_orderops", root_agent=root_agent)` | Same container Lesson 13 used in pytest. `root_agent` is the **Workflow**. |
   | `InMemoryRunner(app=adk_app)` | Lab runner. Lesson 29 replaces the session service in stage. |

   Leave `model_name` on Settings if you want — the Workflow’s `GEMINI` constant (Lesson 13: `gemini-3.5-flash`) is what the graph actually calls. Settings.model_name is leftover from the fallback you just deleted. You may set it to `gemini-3.5-flash` so `/readyz` operators are not lied to, or ignore it. Do not wire a second model picker here.

4. Walk the API-key dependency. This is the lock on the door:

```python
def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    if not x_api_key or x_api_key != settings.api_key:
        raise HTTPException(status_code=401, detail="unauthorized")
```

   FastAPI turns the argument `x_api_key` into the HTTP header **`X-Api-Key`**. Missing or wrong → **401**. The Workflow never runs. That is the point: auth is not an instruction.

5. Walk `/v1/wismo`. This is the pattern the webhook will copy:

```python
@api.post("/v1/wismo", dependencies=[Depends(require_api_key)])
async def wismo(
    body: WismoRequest,
    x_correlation_id: str | None = Header(default=None),
) -> dict:
    ...
    session = await runner.session_service.create_session(
        app_name="meridian_orderops", user_id="api"
    )
    session_id = body.session_id or session.id
    final_text = ""
    try:
        async for event in runner.run_async(
            user_id="api",
            session_id=session_id,
            new_message=types.Content(
                role="user",
                parts=[types.Part.from_text(text=body.message)],
            ),
        ):
            content = getattr(event, "content", None)
            if content and getattr(content, "parts", None):
                for part in content.parts:
                    if getattr(part, "text", None):
                        final_text = part.text
    except Exception as exc:
        ...
        raise HTTPException(status_code=500, detail="agent_error") from exc
```

   | Line | What it does |
   |------|----------------|
   | `Depends(require_api_key)` | Run the lock before the handler body |
   | `create_session(app_name=..., user_id=...)` | Keyword-only ADK 2.6.3 session. `user_id="api"` is the **service** identity, not Maya. |
   | `body.session_id or session.id` | Optional continue-this-thread. Brand-new OMS events should omit it. |
   | `runner.run_async(...)` | Native invoke. Same stream as Lesson 08 / 13. |
   | `types.Content` / `Part.from_text` | Same message shape the Workflow’s `START` already expects |
   | Last `part.text` | Coarse “final text” for JSON. The graph’s truth is still the event stream. |

6. Install the edge extras if needed, then serve. From the **repo root**:

```bash
cd /Users/alishaghatane/dev/agent-learn-sme
source .venv/bin/activate
pip install -r project/meridian_ops/deploy/requirements.txt
export PYTHONPATH=project
export MERIDIAN_API_KEY=dev-local-key-change-me
export GOOGLE_API_KEY="YOUR_KEY"
uvicorn meridian_ops.deploy.app:api --app-dir project --host 127.0.0.1 --port 8080
```

   | Flag / env | What it does |
   |------------|----------------|
   | `uvicorn …:api` | Load the FastAPI object named `api` (not `app` — that name is the ADK `App`). |
   | `--app-dir project` | Look for `meridian_ops` under `project/`. Also puts that directory on `sys.path`. |
   | `--host 127.0.0.1` | Bind **this machine only**. `0.0.0.0` would listen on every interface — skip that on a laptop lab. |
   | `--port 8080` | Edge port. `adk web` stays on **8000**. A2A will use **9000**. Three ports, no collisions. |
   | `MERIDIAN_API_KEY` | Must match the `X-Api-Key` you send. Default in code is `dev-local-key-change-me`. |
   | `GOOGLE_API_KEY` | Language nodes inside the Workflow. |

7. In a **second** terminal, prove the door and the Runner:

```bash
cd /Users/alishaghatane/dev/agent-learn-sme
source .venv/bin/activate

curl -sS http://127.0.0.1:8080/healthz
echo
curl -sS http://127.0.0.1:8080/readyz
echo

curl -sS -o /tmp/wismo401.txt -w "%{http_code}\n" \
  -X POST http://127.0.0.1:8080/v1/wismo \
  -H "Content-Type: application/json" \
  -d '{"message":"Status for MC-1048292"}'

curl -sS http://127.0.0.1:8080/v1/wismo \
  -H "Content-Type: application/json" \
  -H "X-Api-Key: dev-local-key-change-me" \
  -d '{"message":"Status for MC-1048292? nothing at the door"}' \
  | python -m json.tool
```

   | Flag | What it does |
   |------|----------------|
   | `-sS` | Silent progress bar (`-s`) but **still show errors** (`-S`). You want failures visible. |
   | `-X POST` | HTTP method. `curl` without `-X` + `-d` often POSTs anyway; being explicit is safer. |
   | `-H "Content-Type: application/json"` | Tell FastAPI the body is JSON. Wrong type → 422. |
   | `-H "X-Api-Key: ..."` | The header `require_api_key` reads. Skip it → 401. |
   | `-d '{...}'` | Request **body**. |
   | `-o /tmp/wismo401.txt` | Write body to a file (we only care about the status here). |
   | `-w "%{http_code}\n"` | Print the HTTP status code after the transfer. |
   | `python -m json.tool` | Pretty-print JSON so `engine` / `final_text` are readable. |

   You do **not** need `curl -N` (`--no-buffer`) on this route. `-N` disables output buffering so **streaming** responses (SSE, Lesson 22) appear token-by-token. `/v1/wismo` returns one JSON object when the Workflow finishes.

### Expect

- `/healthz` → `{"status":"ok"}`
- `/readyz` → `status` ready, plus `env` / `git_sha`
- Missing API key → **`401`**
- Happy path JSON includes `"engine": "google-adk"`, a `session_id`, a `correlation_id`, and non-empty `final_text` about `MC-1048292` (delivered, no POD)

If import dies on `ValidationError` / `'WISMO'`, finish Lesson 13 Task 2 (routing map) and restart uvicorn.

If `final_text` is empty but HTTP 200, the graph paused or produced no text parts — WISMO should not pause. Check the uvicorn traceback.

> **Tip:** Keep uvicorn running. Tasks 2–3 add a route; you will restart once after the edit.

> **Watch out:** `InMemoryRunner` sessions die when the process dies. That is correct for this lab. Do not write a pickle file of sessions and call it production.

### Scoreboard after Task 1

| Control | In place? |
|---------|-----------|
| Walked FastAPI → `run_async` (no fallback agent) | **Yes** |
| OMS webhook + idempotency | Not yet |
| Fixture `curl` (ok + duplicate) | Not yet |
| `to_a2a` Policy server + agent card | Not yet |
| `RemoteA2aAgent` consumer | Not yet |

---

## Task 2 — OMS webhook with domain idempotency

### Why

OMS will retry. That is not a bug. If `run_async` runs twice for `oms-evt-10001`, Maya gets two WISMO replies and your evals count two trajectories for one delivery.

ADK does not dedupe **broker** ids. That is domain logic at the edge — allowed by [NATIVE-ADK.md](../docs/NATIVE-ADK.md), same family as FastAPI HMAC. It is **not** an agent framework.

The check must run **before** `run_async`. A “dedupe” that happens after Gemini has already spent money is a log line, not a lock.

### Do this

1. Open the fixture you will POST. `project/meridian_ops/fixtures/events/oms_delivered.json`:

```json
{
  "id": "oms-evt-10001",
  "type": "oms.lifecycle_changed",
  "occurred_at": "2026-08-10T17:12:00Z",
  "data": {
    "order_id": "MC-1048292",
    "lifecycle": "delivered",
    "pod_photo_present": false
  }
}
```

   `id` is the idempotency key. `data.order_id` is what the Workflow already knows how to look up.

2. In `project/meridian_ops/deploy/app.py`, add a processed-event store next to the other lab counters (module-level dict is enough for **one process**; Redis belongs in stage, not as a FakePubSub):

```python
_PROCESSED_EVENTS: dict[str, dict] = {}
```

3. Add request models and the handler **below** `wismo`. Keep using `require_api_key` and the same `runner`:

```python
class OmsEventData(BaseModel):
    order_id: str = Field(min_length=1, max_length=32)
    lifecycle: str | None = None
    pod_photo_present: bool | None = None


class OmsEvent(BaseModel):
    id: str = Field(min_length=1, max_length=128)
    type: str = "oms.lifecycle_changed"
    occurred_at: str | None = None
    data: OmsEventData


@api.post("/v1/events/oms", dependencies=[Depends(require_api_key)])
async def oms_event(
    body: OmsEvent,
    x_correlation_id: str | None = Header(default=None),
) -> dict:
    """OMS lifecycle webhook → ADK Runner. Duplicates short-circuit."""
    correlation_id = x_correlation_id or f"corr-{uuid.uuid4().hex[:12]}"
    if body.id in _PROCESSED_EVENTS:
        prior = _PROCESSED_EVENTS[body.id]
        return {
            "status": "duplicate",
            "event_id": body.id,
            "correlation_id": correlation_id,
            "session_id": prior.get("session_id"),
            "engine": "google-adk",
        }

    order_id = body.data.order_id
    text = (
        f"OMS event {body.id}: order {order_id} lifecycle "
        f"{body.data.lifecycle}, pod_photo_present={body.data.pod_photo_present}. "
        "What's the status?"
    )
    session = await runner.session_service.create_session(
        app_name="meridian_orderops", user_id="oms_webhook"
    )
    final_text = ""
    async for event in runner.run_async(
        user_id="oms_webhook",
        session_id=session.id,
        new_message=types.Content(
            role="user",
            parts=[types.Part.from_text(text=text)],
        ),
    ):
        content = getattr(event, "content", None)
        if content and getattr(content, "parts", None):
            for part in content.parts:
                if getattr(part, "text", None):
                    final_text = part.text

    record = {"session_id": session.id, "final_text": final_text}
    _PROCESSED_EVENTS[body.id] = record
    return {
        "status": "ok",
        "event_id": body.id,
        "correlation_id": correlation_id,
        "session_id": session.id,
        "final_text": final_text,
        "engine": "google-adk",
    }
```

   Walk the control flow:

   | Step | Native / allowed? |
   |------|-------------------|
   | Header API key | Edge — FastAPI |
   | `body.id in _PROCESSED_EVENTS` | Domain idempotency — **before** Runner |
   | `create_session` | ADK session service |
   | `run_async` | ADK |
   | Store `session_id` under `body.id` | So a duplicate can return the **same** session, not a new one |

   The message text includes `MC-1048292` and no `refund` / `sku` keywords, so Lesson 13’s `route_ticket` emits **WISMO**. You did not add a second classifier in the webhook.

4. Create `project/meridian_ops/tests/test_oms_webhook.py`. These tests must **not** call Gemini:

```python
from fastapi.testclient import TestClient

from meridian_ops.deploy import app as deploy_app


def test_oms_event_requires_api_key():
    client = TestClient(deploy_app.api)
    response = client.post(
        "/v1/events/oms",
        json={
            "id": "oms-evt-unauthorized",
            "data": {"order_id": "MC-1048292"},
        },
    )
    assert response.status_code == 401


def test_oms_event_duplicate_does_not_create_session(monkeypatch):
    deploy_app._PROCESSED_EVENTS.clear()
    deploy_app._PROCESSED_EVENTS["oms-evt-10001"] = {
        "session_id": "sess-already-ran",
        "final_text": "already handled",
    }

    def _boom(*_a, **_k):
        raise AssertionError("create_session must not run on a duplicate")

    monkeypatch.setattr(
        deploy_app.runner.session_service, "create_session", _boom
    )

    client = TestClient(deploy_app.api)
    response = client.post(
        "/v1/events/oms",
        headers={"X-Api-Key": "dev-local-key-change-me"},
        json={
            "id": "oms-evt-10001",
            "type": "oms.lifecycle_changed",
            "data": {
                "order_id": "MC-1048292",
                "lifecycle": "delivered",
                "pod_photo_present": False,
            },
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "duplicate"
    assert body["session_id"] == "sess-already-ran"
    assert body["engine"] == "google-adk"
```

   | Test | If it failed, you would have… |
   |------|-------------------------------|
   | `test_oms_event_requires_api_key` | …left the route unlocked |
   | `test_oms_event_duplicate_does_not_create_session` | …deduped *after* `run_async`, or forgotten the dict check |

   `monkeypatch` on `create_session` is the proof: a duplicate never reaches ADK. That is not a stub planner. It is a fence around the real runner.

5. Run pytest. From the **repo root**:

```bash
cd /Users/alishaghatane/dev/agent-learn-sme
source .venv/bin/activate
export PYTHONPATH=project
pytest project/meridian_ops/tests/test_oms_webhook.py -v
```

   `-v` — print each test name.

### Expect

```
test_oms_webhook.py::test_oms_event_requires_api_key PASSED
test_oms_webhook.py::test_oms_event_duplicate_does_not_create_session PASSED
```

No API key required for this file.

> **Tip:** `_PROCESSED_EVENTS` is per process. Two uvicorn workers would each have their own dict — that is why stage uses Redis / the broker’s native dedupe. The **shape** (check id, then Runner) stays.

> **Watch out:** Do not build a class named `FakePubSub` to “practice messaging.” Task 3 is a real HTTP POST. A queue worker in production is this same function with a different trigger.

### Scoreboard after Task 2

| Control | In place? |
|---------|-----------|
| Walked FastAPI → `run_async` (no fallback agent) | Yes |
| OMS webhook + idempotency | **Yes** |
| Fixture `curl` (ok + duplicate) | Not yet |
| `to_a2a` Policy server + agent card | Not yet |
| `RemoteA2aAgent` consumer | Not yet |

---

## Task 3 — `curl` the OMS fixture (ok, then duplicate)

### Why

Pytest proved the fence. You still need to see a **first** delivery run the Workflow, then a retry return `duplicate`. That is the incident timeline Priya will ask for: “did we text Maya twice?”

### Do this

1. Restart uvicorn so it loads the new route (Ctrl+C the Task 1 process, then the same command):

```bash
cd /Users/alishaghatane/dev/agent-learn-sme
source .venv/bin/activate
export PYTHONPATH=project
export MERIDIAN_API_KEY=dev-local-key-change-me
export GOOGLE_API_KEY="YOUR_KEY"
uvicorn meridian_ops.deploy.app:api --app-dir project --host 127.0.0.1 --port 8080
```

   Same flags as Task 1. `--port 8080` still avoids `adk web` on 8000.

2. First delivery — POST the **file** so you cannot typo the id:

```bash
cd /Users/alishaghatane/dev/agent-learn-sme
source .venv/bin/activate

curl -sS -X POST http://127.0.0.1:8080/v1/events/oms \
  -H "Content-Type: application/json" \
  -H "X-Api-Key: dev-local-key-change-me" \
  -H "X-Correlation-Id: corr-oms-10001" \
  -d @project/meridian_ops/fixtures/events/oms_delivered.json \
  | python -m json.tool
```

   | Flag | What it does |
   |------|----------------|
   | `-d @path` | Read the body **from a file**. The `@` is what tells curl “this is a filename,” not a literal JSON string. |
   | `-H "X-Correlation-Id: corr-oms-10001"` | Optional. The handler uses it if present; otherwise it mints `corr-…`. Priya stitches logs with this. |
   | `-N` | **Not used.** This response is one JSON document, not an SSE stream. |

3. Immediate retry — same file, same id:

```bash
curl -sS -X POST http://127.0.0.1:8080/v1/events/oms \
  -H "Content-Type: application/json" \
  -H "X-Api-Key: dev-local-key-change-me" \
  -d @project/meridian_ops/fixtures/events/oms_delivered.json \
  | python -m json.tool
```

4. Wrong key, just to keep the lock honest:

```bash
curl -sS -o /dev/null -w "%{http_code}\n" \
  -X POST http://127.0.0.1:8080/v1/events/oms \
  -H "Content-Type: application/json" \
  -H "X-Api-Key: definitely-not-the-key" \
  -d @project/meridian_ops/fixtures/events/oms_delivered.json
```

   `-o /dev/null` — discard the body. `-w "%{http_code}\n"` — print **only** the status code.

### Expect

First POST:

```json
{
  "status": "ok",
  "event_id": "oms-evt-10001",
  "engine": "google-adk",
  "session_id": "<uuid>",
  "final_text": "<WISMO reply mentioning MC-1048292 / no POD>"
}
```

Second POST:

```json
{
  "status": "duplicate",
  "event_id": "oms-evt-10001",
  "session_id": "<the same uuid>",
  "engine": "google-adk"
}
```

Wrong key: `401`.

Uvicorn logs on the first call should show ADK work. The second call should be boring — no second Gemini spend.

If both return `ok` with **different** `session_id`s, `_PROCESSED_EVENTS` is not assigned, or you restarted uvicorn between curls (in-memory dict cleared). That restart behavior is expected; say it out loud so nobody “fixes” it with a homemade checkpoint file.

> **Tip:** A real Pub/Sub worker is this handler with `message_id` instead of `body.id`, then `ack` after `status=ok`. Same `run_async`. No third library named MeridianBus.

> **Watch out:** Do not POST `/v1/wismo` and call it the event lab. WISMO is a chat façade. The event lab is `/v1/events/oms` plus the fixture id.

### Scoreboard after Task 3

| Control | In place? |
|---------|-----------|
| Walked FastAPI → `run_async` (no fallback agent) | Yes |
| OMS webhook + idempotency | Yes |
| Fixture `curl` (ok + duplicate) | **Yes** |
| `to_a2a` Policy server + agent card | Not yet |
| `RemoteA2aAgent` consumer | Not yet |

---

## Task 4 — Expose Policy with `to_a2a` (exact 2.6.3 import)

### Why

Policy is a **product** with its own tools (`retrieve_policy`) and its own instruction (“never invent credits”). Another process should call it through ADK’s A2A helper — not by copying `policy_rag.py` into OrderOps.

On ADK 2.6.3 the helper lives at:

```python
from google.adk.a2a.utils.agent_to_a2a import to_a2a
```

`google.adk.a2a.__init__` does **not** re-export `to_a2a`. `from google.adk.a2a import to_a2a` fails. Use the path above.

`to_a2a` returns a **Starlette** app. You serve it with uvicorn. It builds an **agent card** on startup (lifespan) and mounts:

| Route | Purpose |
|-------|---------|
| `{prefix}/` | JSON-RPC (A2A) |
| `{prefix}/.well-known/agent-card.json` | Discovery document `RemoteA2aAgent` fetches |

`a2a-sdk` is an **extra**: `google-adk[a2a]`. Without it, `to_a2a` raises `ModuleNotFoundError: a2a`.

### Do this

1. Install the extra into the **existing** venv:

```bash
cd /Users/alishaghatane/dev/agent-learn-sme
source .venv/bin/activate
pip install "google-adk[a2a]==2.6.3"
```

   `==2.6.3` — same ADK you already run. `[a2a]` pulls `a2a-sdk`.

2. Prove the provider import (this is the check people skip, then they invent `LocalPolicyRemote`):

```bash
python - <<'PY'
from google.adk.a2a.utils.agent_to_a2a import to_a2a
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent
print("to_a2a", to_a2a.__module__)
print("RemoteA2aAgent", RemoteA2aAgent.__module__)
PY
```

   Expect:

```
to_a2a google.adk.a2a.utils.agent_to_a2a
RemoteA2aAgent google.adk.agents.remote_a2a_agent
```

3. Open `project/meridian_policy_a2a/agent.py`. Bump the model. The file ships `gemini-2.5-flash`. This lab uses **`gemini-3.5-flash`**:

```python
"""Policy specialist — expose via ADK to_a2a() / consume via RemoteA2aAgent."""

from google.adk.agents import LlmAgent

from meridian_ops.tools.policy_rag import retrieve_policy

root_agent = LlmAgent(
    name="meridian_policy_a2a",
    model="gemini-3.5-flash",
    description="Meridian policy QA with retrieve_policy tool.",
    instruction="""
You are Meridian Policy.
Always call retrieve_policy before stating rules.
Cite policy ids when present. Never invent credits.
""".strip(),
    tools=[retrieve_policy],
)
```

   This is still one `LlmAgent`. `to_a2a` accepts `BaseAgent | Workflow`. You are **not** wrapping it in a homemade RPC class.

4. Create `project/meridian_policy_a2a/a2a_app.py`:

```python
"""A2A Starlette app for Meridian Policy — native to_a2a()."""

from google.adk.a2a.utils.agent_to_a2a import to_a2a

from meridian_policy_a2a.agent import root_agent

# host/port/protocol are advertised on the agent card's RPC URL.
# uvicorn --host/--port must match, or RemoteA2aAgent will dial the wrong place.
a2a_app = to_a2a(
    root_agent,
    host="127.0.0.1",
    port=9000,
    protocol="http",
    rpc_path="meridian_policy_a2a",
)
```

   Walk the 2.6.3 kwargs:

   | Kwarg | What it does |
   |-------|----------------|
   | `agent` (positional) | The `LlmAgent` (or `Workflow`) to serve |
   | `host="127.0.0.1"` | Hostname **written on the card** |
   | `port=9000` | Port **written on the card** (not `adk web`’s 8000, not the edge’s 8080) |
   | `protocol="http"` | Lab is local HTTP. TLS is a deploy concern. |
   | `rpc_path="meridian_policy_a2a"` | Mount prefix. Card lives at `/meridian_policy_a2a/.well-known/agent-card.json`. RPC at `/meridian_policy_a2a/`. |

   Advertised RPC URL becomes `http://127.0.0.1:9000/meridian_policy_a2a/`.

5. Serve it. **New terminal** — leave the OMS edge on 8080 if you still need it:

```bash
cd /Users/alishaghatane/dev/agent-learn-sme
source .venv/bin/activate
export PYTHONPATH=project
export GOOGLE_API_KEY="YOUR_KEY"
uvicorn meridian_policy_a2a.a2a_app:a2a_app --app-dir project --host 127.0.0.1 --port 9000
```

   | Flag | What it does |
   |------|----------------|
   | `…:a2a_app` | The Starlette object `to_a2a(...)` returned |
   | `--host 127.0.0.1` | Listen locally — must match `to_a2a(host=...)` |
   | `--port 9000` | Listen port — must match `to_a2a(port=...)` |

   The card is built in Starlette **lifespan**. Importing the module is not enough; uvicorn must **start**.

6. Fetch the card (third terminal is fine):

```bash
curl -sS http://127.0.0.1:9000/meridian_policy_a2a/.well-known/agent-card.json \
  | python -m json.tool
```

   You may see an experimental-A2A warning on stderr when Python first imports `to_a2a`. That is ADK telling you the **ADK wrapper** is experimental; the A2A protocol itself is not. Do not switch to a DIY stack because of the warning. Optional: `export ADK_SUPPRESS_A2A_EXPERIMENTAL_FEATURE_WARNINGS=1` to silence it.

### Expect

HTTP 200. JSON with at least:

- a `name` derived from `meridian_policy_a2a`
- a `url` (or equivalent RPC field) pointing at `http://127.0.0.1:9000/meridian_policy_a2a/`
- skills / description mentioning policy

Exact field names follow the A2A agent-card schema the installed `a2a-sdk` serializes. You care that the **URL** is this lab’s card URL:

```
http://127.0.0.1:9000/meridian_policy_a2a/.well-known/agent-card.json
```

Copy that string. Task 5 pastes it into `RemoteA2aAgent(agent_card=...)`.

If GET 404s:

- uvicorn not running, or still starting (lifespan)
- `rpc_path` omitted → card is at `http://127.0.0.1:9000/.well-known/agent-card.json` instead
- `--port` ≠ `to_a2a(port=...)`

If `ModuleNotFoundError: a2a`, the extra did not install. Rerun `pip install "google-adk[a2a]==2.6.3"`.

> **Tip:** `to_a2a(JoinNode)` is the wrong root. Expose a `Workflow` or an `LlmAgent`. Policy here is an `LlmAgent`. OrderOps, if you ever serve it over A2A, is the `Workflow`.

> **Watch out:** Do not hand-write `agent-card.json` and skip `to_a2a`. The helper keeps skills and RPC URL aligned. A stale file is how consumers dial `/` while you mounted `/meridian_policy_a2a/`.

### Scoreboard after Task 4

| Control | In place? |
|---------|-----------|
| Walked FastAPI → `run_async` (no fallback agent) | Yes |
| OMS webhook + idempotency | Yes |
| Fixture `curl` (ok + duplicate) | Yes |
| `to_a2a` Policy server + agent card | **Yes** |
| `RemoteA2aAgent` consumer | Not yet |

---

## Task 5 — Consume with `RemoteA2aAgent` (exact 2.6.3 import)

### Why

Serving a card nobody calls is a demo. OrderOps (or a tiny consumer package) must use ADK’s client node:

```python
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent
```

`from google.adk.agents import RemoteA2aAgent` **fails** — 2.6.3 does not put it in `google.adk.agents.__all__`. Use the module path.

`RemoteA2aAgent(name=..., agent_card=...)` accepts:

1. An `AgentCard` object  
2. A **URL string** (what you have)  
3. A **file path** to JSON  

You will pass the URL from Task 4.

`project/meridian_ops/a2a/` currently says “lab doubles.” That wording is the DIY trap. You will replace it with a consumer that **is** `RemoteA2aAgent`.

### Do this

1. Replace `project/meridian_ops/a2a/__init__.py` so it is not a doubles package:

```python
"""Native ADK A2A consumer helpers — RemoteA2aAgent, not a protocol double."""

from meridian_ops.a2a.consumer import POLICY_CARD_URL, policy_remote

__all__ = ["POLICY_CARD_URL", "policy_remote"]
```

2. Create `project/meridian_ops/a2a/consumer.py`:

```python
"""Policy consumer — ADK RemoteA2aAgent pointed at the to_a2a card."""

from google.adk.agents.remote_a2a_agent import RemoteA2aAgent

POLICY_CARD_URL = (
    "http://127.0.0.1:9000/meridian_policy_a2a/.well-known/agent-card.json"
)


def policy_remote() -> RemoteA2aAgent:
    return RemoteA2aAgent(
        name="policy_remote",
        agent_card=POLICY_CARD_URL,
        description="Meridian Policy over A2A (to_a2a provider).",
    )
```

   | Constructor arg (2.6.3) | Why |
   |-------------------------|-----|
   | `name="policy_remote"` | Graph / session identity. Unique in the app. |
   | `agent_card=POLICY_CARD_URL` | URL string. The node fetches the card, then RPCs the advertised url. |
   | `description=...` | Shown in UIs / cards. If empty, ADK can fill from the remote card. |

3. Add a tiny package so `adk web` can load the consumer the same way it loads OrderOps. Create `project/meridian_policy_remote/__init__.py`:

```python
from . import agent

__all__ = ["agent"]
```

   Create `project/meridian_policy_remote/agent.py`:

```python
"""adk web entry — RemoteA2aAgent as root_agent."""

from meridian_ops.a2a.consumer import policy_remote

root_agent = policy_remote()
```

   You did **not** copy Policy’s tools. This process has no `retrieve_policy`. The remote does.

4. Construction test — no live server required. Create `project/meridian_ops/tests/test_a2a_consumer.py`:

```python
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent

from meridian_ops.a2a.consumer import POLICY_CARD_URL, policy_remote
from meridian_policy_remote.agent import root_agent


def test_policy_remote_is_native_remote_a2a_agent():
    agent = policy_remote()
    assert isinstance(agent, RemoteA2aAgent)
    assert agent.name == "policy_remote"
    assert isinstance(root_agent, RemoteA2aAgent)
    assert POLICY_CARD_URL.endswith("/.well-known/agent-card.json")
    assert "meridian_policy_a2a" in POLICY_CARD_URL
```

```bash
cd /Users/alishaghatane/dev/agent-learn-sme
source .venv/bin/activate
export PYTHONPATH=project
pytest project/meridian_ops/tests/test_a2a_consumer.py -v
```

5. Live call. Keep **Task 4’s uvicorn** running on port 9000. Then:

```bash
cd /Users/alishaghatane/dev/agent-learn-sme/project
source ../.venv/bin/activate
export PYTHONPATH=.
export GOOGLE_API_KEY="YOUR_KEY"
adk web --port 8000
```

   | Flag | What it does |
   |------|----------------|
   | `cd project` | Discovery root. `meridian_policy_remote/` must be a child of cwd. |
   | `--port 8000` | UI. Policy A2A stays on **9000**. Do not point `adk web` at 9000 — that would collide with `to_a2a`. |

   Select **`meridian_policy_remote`**. Send:

```
What's Meridian's policy on melted dairy and full-order refunds over $75?
```

   The remote agent must call `retrieve_policy` **on the server** (Task 4 process). The consumer has no copy of the markdown.

### Expect

Pytest:

```
test_a2a_consumer.py::test_policy_remote_is_native_remote_a2a_agent PASSED
```

In `adk web`:

- Trajectory on the **consumer** shows a remote A2A turn (not a local `retrieve_policy` tool on `meridian_policy_remote`)
- Answer cites **POL-REFUND-04** (HITL over $75 / melted items) — or honestly says it cannot cite, if retrieval missed. It must **not** invent a `$100` folklore rule
- Task 4’s uvicorn logs the inbound A2A request

If the UI errors with connection refused, `to_a2a` uvicorn is down. Start Task 4 first.

If the consumer grows a `tools=[retrieve_policy]` list, you defeated A2A. Delete the local tool. The card is the ownership boundary.

Optional (stretch, not required): on the OrderOps Workflow, set the `POLICY` routing-map value to `policy_remote()` instead of the in-process `policy_agent`. Same `RemoteA2aAgent`. Do not write a second graph package to try it.

> **Tip:** Lesson 05 transfer = in-process. This node = HTTP to another ADK. When on-call asks “which deploy owns policy citations?”, the answer is the **Policy** service behind the card URL.

> **Watch out:** A class in `meridian_ops/a2a/` that implements `send` / `receive` with `httpx` and parsed JSON-RPC is DIY A2A. `RemoteA2aAgent` already does that.

### Scoreboard after Task 5

| Control | In place? |
|---------|-----------|
| Walked FastAPI → `run_async` (no fallback agent) | Yes |
| OMS webhook + idempotency | Yes |
| Fixture `curl` (ok + duplicate) | Yes |
| `to_a2a` Policy server + agent card | Yes |
| `RemoteA2aAgent` consumer | **Yes** |

---

## How it works (deeper dive)

### Webhook vs chat vs queue

| Trigger | Entry | Then |
|---------|-------|------|
| Human in `adk web` | Dev UI | `Runner` inside ADK web |
| Human / app via `/v1/wismo` | FastAPI | `create_session` + `run_async` |
| OMS `/v1/events/oms` | FastAPI + idempotency | **same** `run_async` |
| Cloud Pub/Sub / Redis | Subscriber process | **same** handler body, then ack |

The queue is plumbing. If you can only explain Meridian events by opening `FakePubSub`, you learned the fake.

### `to_a2a` vs `RemoteA2aAgent`

```
Policy process                         OrderOps / consumer process
─────────────────                      ───────────────────────────
LlmAgent root_agent                    RemoteA2aAgent(agent_card=URL)
        │                                        │
        ▼                                        │ GET card
to_a2a(...) → Starlette                          │ POST JSON-RPC
        │                                        │
        └── /.well-known/agent-card.json  ◄──────┘
            /meridian_policy_a2a/     RPC
```

`host` / `port` / `protocol` / `rpc_path` on `to_a2a` write the **card**. uvicorn `--host` / `--port` bind the **socket**. They must agree.

### Why the imports are long

ADK 2.6.3:

```python
from google.adk.a2a.utils.agent_to_a2a import to_a2a
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent
```

Shorter re-exports are not there. Pin these two lines in review so nobody “simplifies” them into a missing symbol and then a DIY client.

---

## Common pitfalls / troubleshooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| Webhook imports fallback `LlmAgent` | Lesson 12 try/except still present | Delete it; import `meridian_orderops.agent.root_agent` |
| `ValidationError` `'WISMO'` on startup | OrderOps still has 3-tuple edges | Lesson 13 Task 2 routing map |
| 401 on curl | Missing/wrong `X-Api-Key` | Header name is `X-Api-Key`; value matches `MERIDIAN_API_KEY` |
| Duplicate still returns `ok` | New process (uvicorn restart) or id typo | In-memory dict; same process + same `id` |
| `ModuleNotFoundError: a2a` | Extra not installed | `pip install "google-adk[a2a]==2.6.3"` |
| `cannot import name 'to_a2a'` | Imported from `google.adk.a2a` | `from google.adk.a2a.utils.agent_to_a2a import to_a2a` |
| `cannot import name 'RemoteA2aAgent'` | Imported from `google.adk.agents` | `from google.adk.agents.remote_a2a_agent import RemoteA2aAgent` |
| Card 404 | Lifespan not run, or prefix mismatch | uvicorn must be up; GET the `rpc_path` URL |
| Remote agent connection refused | Policy uvicorn down, or card URL port ≠ listen port | Align `to_a2a(port=9000)` with `--port 9000` |
| Consumer calls `retrieve_policy` locally | You added tools on the remote node | Tools stay on the **provider** |
| Tempted to write `FakePubSub` | Wanted a queue lab | Worker = Task 2 handler + ack. Use a real emulator later if you need one. |

---

## You are done when

- [ ] `deploy/app.py` imports the OrderOps `Workflow` (no fallback agent)
- [ ] `/v1/wismo` still returns `engine: google-adk` with an API key
- [ ] `/v1/events/oms` runs `run_async` after idempotency
- [ ] pytest: 401 + duplicate never calls `create_session`
- [ ] `curl -d @oms_delivered.json` twice → `ok` then `duplicate`
- [ ] `to_a2a` served; card GET at `http://127.0.0.1:9000/meridian_policy_a2a/.well-known/agent-card.json`
- [ ] `RemoteA2aAgent` consumer uses that URL; pytest proves the type
- [ ] One policy question in `adk web` against `meridian_policy_remote`
- [ ] Zero `FakePubSub`, zero DIY A2A clients

---

## Knowledge check

1. What ADK API runs OrderOps for a webhook body?  
2. Where must event-id dedupe run — before or after `run_async`?  
3. What exact import exposes an agent over A2A on 2.6.3?  
4. What exact import calls a remote agent on 2.6.3?  
5. What URL does this lab’s Policy card live at?  
6. Why is `curl -N` omitted on `/v1/events/oms`?  
7. When do you use Lesson 05 transfer instead of `RemoteA2aAgent`?

### Answers

1. `runner.run_async` on an `InMemoryRunner` (or `Runner`) wrapped around `App(name=..., root_agent=Workflow)`.  
2. **Before.** After is a bill, not a lock.  
3. `from google.adk.a2a.utils.agent_to_a2a import to_a2a`  
4. `from google.adk.agents.remote_a2a_agent import RemoteA2aAgent`  
5. `http://127.0.0.1:9000/meridian_policy_a2a/.well-known/agent-card.json`  
6. The handler returns one JSON object. `-N` is for unbuffered streaming (SSE).  
7. Same process, same deploy, same memory. Cross-process ownership → A2A.

---

## Recap — Pack C (native)

| Lesson | Native focus |
|--------|----------------|
| 13 | `Workflow` + routing maps + `Event(route=...)` |
| 14 | `JoinNode` + routed loops |
| 15 | `RequestInput` resume |
| 16 | `McpToolset` |
| 17 | FastAPI → `Runner.run_async`; `to_a2a` / `RemoteA2aAgent` |

**What you built today:** an OMS door that calls the OrderOps graph once per event id, and a Policy service that other agents call through a real agent card.

**What you now understand:** events are messages into ADK, not a second orchestrator; A2A is a process boundary ADK already implements.

**What you can do next:** Lesson 18 deepens policy **retrieval** (chunk / embed / cite). The A2A seam you just opened still points at that same Policy agent.

---

## Stretch goal

Point OrderOps `POLICY` at `policy_remote()` (Lesson 13 routing map value). Keep WISMO / SHORTAGE / REFUND local. Run TCK-9006 (“late grocery delivery credits”) through `adk web` on `meridian_orderops` with Policy uvicorn up. Citations must still come from the **remote** `retrieve_policy`. Extra — Tasks 1–5 already prove the webhook and the card.

A second stretch: a Pub/Sub **emulator** subscriber whose callback is `oms_event`’s body (dedupe + `run_async` + ack). Not a `FakePubSub` class in `meridian_ops`.

---

## Feedback

- Could you add `/v1/events/atp` for a shortage payload without a new orchestrator — same key header, same processed dict, different message text so `route_ticket` emits `SHORTAGE`?  
- What tripped you up: API key header, idempotency vs restart, `to_a2a` import path, card URL prefix, or `RemoteA2aAgent` vs in-process tools?  
- Note the **task number** and what you expected vs what happened (command + first lines of output). That is the signal that improves this lesson — “it was confusing” is not.

---

## Navigate

**← Prev** [Lesson 16 — MCP & tool ecosystems](16-mcp-tool-ecosystems.md)  
**Next →** [Lesson 18 — Advanced RAG for retail policy](18-advanced-rag-retail-policy.md)  
**Track home:** [README](../README.md)  
**Native standard:** [NATIVE-ADK.md](../docs/NATIVE-ADK.md)
