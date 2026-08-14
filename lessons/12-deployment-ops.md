# Lesson 12 — Deployment & first-line ops

**Level:** Advanced  
**Time:** ~150–180 minutes  
**Prerequisites:** Pack A + Lessons 08–11; Docker Desktop (or Engine) running  
**Lab outcome:** Ship Meridian OrderOps as **one** container: FastAPI edge → **ADK `App` + `InMemoryRunner`**, with `/healthz`, `/readyz`, Docker layers you can explain, Compose, and `smoke.sh`

**Standard:** [docs/NATIVE-ADK.md](../docs/NATIVE-ADK.md)  
**Goes next:** [Lesson 41 — CI/CD, canary, rollback drills & on-call](41-cicd-sre-deployment-ops.md)

---

## At a glance

Lesson 12 answers: *“How do we run this in a place that is not my laptop?”*

You will **not** put `adk web` on the public internet. You will **not** add a second host (no extra Cloud Run lab, no homemade orchestrator). The stack in this repo is already the product shape:

```
CX toolkit / curl
        │  X-Api-Key
        ▼
┌───────────────────────────────────┐
│  FastAPI  meridian_ops.deploy.app │
│   /healthz  /readyz  /metrics     │
│   POST /v1/wismo                  │
│        │                          │
│        ▼                          │
│   App + InMemoryRunner            │
│        │                          │
│        ▼                          │
│   OrderOps Workflow (ADK 2.6.3)   │
└───────────────────────────────────┘
        │  docker build / compose
        ▼
   smoke.sh  →  stage later (Lesson 41)
```

| Task | What you do | Who enforces it | How you prove it |
|------|-------------|-----------------|------------------|
| 1 | Make OrderOps **load**, then walk `deploy/app.py` | ADK `App` + FastAPI | Import prints `google-adk`; pytest 401 / `/healthz` |
| 2 | Run uvicorn and curl the real routes | The edge | JSON with `"engine": "google-adk"` |
| 3 | Walk every Dockerfile layer, then `docker build` / `docker run` | The image | Same curls against port 8080 |
| 4 | Compose + `.env` (secrets at **runtime**) | `docker-compose.yml` healthcheck | `docker compose ps` shows healthy |
| 5 | Run the repo’s `smoke.sh` | The script’s asserts | `SMOKE OK` |
| 6 | Hit `/metrics` and **run** the local rollback in `ROLLBACK.md` | Existing runbooks | Smoke still green on `0.1.0` |

If you get lost, scroll back to this table. Each task fills one row. The scoreboard at the end of every task repeats the same rows.

**Forbidden:** a second agent loop inside FastAPI, baking `GOOGLE_API_KEY` into the image, exposing `adk web` as “prod,” or a `FileCheckpointStore`.

---

## Why this matters

Maya’s WISMO traffic does not hit Priya’s laptop. It hits an internal URL the platform team owns.

If you only ever demo in `adk web`:

- Security cannot review who is allowed to call the agent
- On-call cannot roll back a bad prompt by swapping an image tag
- Lesson 08 evals do not map to a running `image_tag`

Priya’s Monday: a Friday prompt tweak ships. Order Status invents a POD photo. Without this lesson you cannot answer “which image, which git sha, which smoke?” in the first 15 minutes.

Two failure modes, one lesson:

1. **The door is missing** — Gemini is reachable, but there is no API key, no liveness probe, no smoke. Kubernetes (or Compose) cannot tell “process up” from “safe to send Maya.”
2. **The door is a second brain** — the FastAPI handler calls Gemini itself. Lesson 13’s graph becomes decoration. Evals lie.

Today the door is FastAPI. The brain stays ADK.

---

## Know these

Read this table before Task 1. Every later task reuses these words.

| Term | Plain English | Meridian example |
|------|---------------|------------------|
| **Edge / façade** | HTTP API in front of the agent. Auth and JSON shape live here. Orchestration does not. | FastAPI in `deploy/app.py` |
| **`App`** | ADK container: a name plus `root_agent` (an agent **or** a Workflow) | `App(name="meridian_orderops", root_agent=root_agent)` |
| **`InMemoryRunner`** | ADK runner with in-memory session / memory / artifacts | Lab. Stage needs a durable session service (Lesson 29). |
| **`run_async`** | Native event stream: one user message in, ADK events out | The only way `/v1/wismo` “runs the agent” |
| **Image** | Immutable runnable package: OS + Python + your code | `meridian-orderops:0.1.0` |
| **Layer** | One `Dockerfile` instruction’s snapshot. Cached if the instruction and its inputs did not change. | `COPY …/requirements.txt` then `RUN pip install` |
| **Liveness (`/healthz`)** | “Is the process up?” | Restart the container if this fails |
| **Readiness (`/readyz`)** | “Safe to send traffic?” | Stop sending Maya here if this fails |
| **Smoke test** | Tiny post-start check a human will skip under pressure | `smoke.sh` |
| **Secret** | Credential that must not live in git or in an image layer | `MERIDIAN_API_KEY`, `GOOGLE_API_KEY` |
| **WISMO** | Where-is-my-order | Maya: delivered, **no** POD photo, order `MC-1048292` |
| **Non-root user** | Container process is not uid 0 | Dockerfile `USER 10001` |

### Picture this: the loading dock vs a second store

| Approach | Store 441 analogue | What goes wrong |
|----------|--------------------|-----------------|
| FastAPI → `run_async` | Dock scanner that starts the **existing** floor map | Auth lives at the door. Path law stays in ADK. |
| Handler that calls Gemini itself | Building a second store in the parking lot | Two orchestrators. Evals lie. |
| `adk web` on the public internet | Leaving the break-room demo TV on the sales floor | No AuthZ, no probes, no rollback tag |
| Secrets in `Dockerfile` `ENV GOOGLE_API_KEY=…` | Taping the safe combination to the box | Anyone who pulls the image has the key |

```
curl /healthz     →  process alive
curl /readyz      →  env + git_sha (still no secrets)
curl /v1/wismo    →  API key → session → runner.run_async → final_text
smoke.sh          →  all three, plus engine == google-adk
```

> **Tip:** `/healthz` is allowed to be dumb. `/v1/wismo` is not. If you put Gemini inside `/healthz`, a model outage looks like a dead process and the orchestrator restart-loops you.

---

## What you already have (do not rebuild)

From the **repo root**, these files **already exist**. This lesson teaches them. It does not invent a second `k8s/` folder.

| Path | Job |
|------|-----|
| `project/meridian_ops/deploy/app.py` | FastAPI edge → `App` + `InMemoryRunner` |
| `project/meridian_ops/deploy/Dockerfile` | Image: copy code, pip, non-root, uvicorn |
| `project/meridian_ops/deploy/docker-compose.yml` | One service, healthcheck, env |
| `project/meridian_ops/deploy/smoke.sh` | healthz + readyz + WISMO assert |
| `project/meridian_ops/deploy/requirements.txt` | FastAPI / uvicorn / pydantic / httpx |
| `project/meridian_ops/deploy/.env.example` | Names of env vars — **not** real keys |
| `project/meridian_ops/deploy/runbooks/DEPLOY.md` | Stage/prod checklist (read it) |
| `project/meridian_ops/deploy/runbooks/ROLLBACK.md` | First 15 minutes, including **local compose** |
| `project/meridian_orderops/agent.py` | The Workflow the edge imports |
| `project/meridian_ops/tools/oms.py` | `get_order` — fixture OMS |
| `.venv/` | Lesson 02. **Source it. Do not recreate it.** |

You will **edit** (not replace):

- `meridian_orderops/agent.py` — routing map so ADK 2.6.3 can construct the Workflow (Lesson 13 walks *why*; today you need it to **boot**)
- `deploy/app.py` — drop the `ImportError` fallback; pin `gemini-3.5-flash`
- `Dockerfile` — pin `google-adk==2.6.3`
- `.env.example` / compose default model — same pin

If `deploy/app.py` is missing, stop. This lesson does not sketch a new API.

---

## Task 1 — Make the edge import ADK (then walk every line)

### Why

Deploy ops only matter if production calls **ADK**. A FastAPI that returns canned JSON is a stub. A FastAPI that calls Gemini itself is a second framework.

The shipped OrderOps graph still uses 3-tuple edges like `(route_ticket, lookup_order, "WISMO")`. On **ADK 2.6.3** that is illegal: Pydantic treats `"WISMO"` as a node. `from meridian_orderops.agent import root_agent` raises `ValidationError`. The `try/except ImportError` in `app.py` does **not** catch that — so uvicorn dies before `/healthz` exists.

You will paste the **routing-map** `edges=` list (the legal 2.6.3 spelling). Lesson 13 is the deep walk of those edges. Today you need the process to start.

### Do this

1. From the **repo root**, activate the existing venv. Do **not** run `python3 -m venv .venv`.

```bash
cd /Users/alishaghatane/dev/agent-learn-sme
source .venv/bin/activate
python -c "import google.adk as adk; print(adk.__version__, adk.__file__)"
```

   - `source .venv/bin/activate` — use **this** project’s Python, not Homebrew’s.
   - If the prompt shows `(.venv)`, you are in the right interpreter.

### Expect

```
2.6.3 /Users/alishaghatane/dev/agent-learn-sme/.venv/lib/python3.14/site-packages/google/adk/__init__.py
```

The patch after `site-packages` can differ. The version must be **`2.6.3`**. If `google.adk` is missing: `pip install "google-adk==2.6.3"` into this venv — still no new venv.

2. Prove the current import **fails** (so you know why we edit). `PYTHONPATH=project` means `import meridian_orderops` looks in `project/`.

```bash
cd /Users/alishaghatane/dev/agent-learn-sme
source .venv/bin/activate
export PYTHONPATH=project
python -c "from meridian_orderops.agent import root_agent"
```

### Expect

A long `ValidationError`. The useful bit is `input_value='WISMO'` (or `'SHORTAGE'` / `'REFUND'`). That string is not a node.

> **Watch out:** If this import **succeeds**, you (or Lesson 13) already applied the routing map. Skip step 3 and jump to step 4. Do not paste a second graph.

3. Open `project/meridian_orderops/agent.py`. Set the model pin the rest of this curriculum uses:

```python
GEMINI = "gemini-3.5-flash"
```

   Then replace the `root_agent = Workflow( ... edges=[...] )` block with this **same graph**, legal spelling:

```python
join_shortage = JoinNode(name="join_shortage")

root_agent = Workflow(
    name="meridian_orderops",
    description="Native ADK OrderOps graph with HITL refund branch.",
    edges=[
        ("START", route_ticket),
        (
            route_ticket,
            {
                "WISMO": lookup_order,
                "SHORTAGE": lookup_order,
                "REFUND": lookup_order,
                "POLICY": policy_agent,
                "UNSUPPORTED": unsupported_msg,
            },
        ),
        (
            lookup_order,
            {
                "WISMO": order_narrator,
                "SHORTAGE": (order_narrator_shortage, inventory_agent),
                "REFUND": hitl_refund_gate,
            },
        ),
        (order_narrator, synthesizer),
        ((order_narrator_shortage, inventory_agent), join_shortage),
        (join_shortage, synthesizer),
        (hitl_refund_gate, refund_finalize),
        (refund_finalize, synthesizer),
        (policy_agent, synthesizer),
    ],
)
```

   A dict on an edge is a **routing map**: keys are `Event(route=...)` values; values are the next node. Lesson 13 explains every branch. Today: the file must construct.

   Re-run the import:

```bash
python -c "from meridian_orderops.agent import root_agent; print(root_agent.name, type(root_agent).__name__)"
```

### Expect

```
meridian_orderops Workflow
```

4. Open `project/meridian_ops/deploy/app.py`. Delete the `try` / `except ImportError` that builds `meridian_order_status_fallback`. It never caught `ValidationError`, and it is a second agent. Production must fail loud if OrderOps cannot load.

   The top of the file after the stdlib / third-party imports should be:

```python
from meridian_orderops.agent import root_agent
```

   Pin the leftover settings field so on-call is not told a model the graph does not use:

```python
class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="MERIDIAN_", extra="ignore")

    api_key: str = "dev-local-key-change-me"
    env: str = "local"
    model_name: str = "gemini-3.5-flash"
    git_sha: str = "unknown"
    image_tag: str = "dev"
```

   `env_prefix="MERIDIAN_"` means the **environment** names are `MERIDIAN_API_KEY`, `MERIDIAN_ENV`, `MERIDIAN_MODEL_NAME`, `MERIDIAN_GIT_SHA`, `MERIDIAN_IMAGE_TAG`. Pydantic-settings maps `MERIDIAN_API_KEY` → `api_key`. `GOOGLE_API_KEY` is **not** in this class — Gemini’s client reads it on its own.

5. Walk the ADK objects that wrap the Workflow:

```python
settings = Settings()

api = FastAPI(title="Meridian OrderOps API", version="0.1.0")
adk_app = App(name="meridian_orderops", root_agent=root_agent)
runner = InMemoryRunner(app=adk_app)
```

   | Piece | Why it is here |
   |-------|----------------|
   | `api = FastAPI(...)` | The Starlette app uvicorn loads: `meridian_ops.deploy.app:api` |
   | `App(name="meridian_orderops", root_agent=root_agent)` | ADK 2.6.3 container. `root_agent` may be a Workflow. |
   | `InMemoryRunner(app=adk_app)` | Pass **`app=`**. Do not also pass `plugins=` — that raises `ValueError` on 2.6.3. |
   | `_REQUESTS` / `_ERRORS` | Lab counters for `/metrics`. Not a second Prometheus stack. |

6. Walk the lock on the door:

```python
def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    if not x_api_key or x_api_key != settings.api_key:
        raise HTTPException(status_code=401, detail="unauthorized")
```

   FastAPI turns the argument `x_api_key` into the HTTP header **`X-Api-Key`**. Missing or wrong → **401**. The Workflow never runs. Auth is not an instruction.

7. Walk the three probes. They do **not** call Gemini.

```python
@api.get("/healthz")
def healthz() -> dict[str, str]:
    """Liveness — process is up."""
    return {"status": "ok"}


@api.get("/readyz")
def readyz() -> dict[str, str]:
    """Readiness — safe to receive traffic (extend with session/deps checks in stage)."""
    return {"status": "ready", "env": settings.env, "git_sha": settings.git_sha}
```

   | Route | Returns | Orchestrator meaning |
   |-------|---------|----------------------|
   | `/healthz` | `{"status": "ok"}` | Restart if this fails |
   | `/readyz` | `status`, `env`, `git_sha` | Stop sending traffic if this fails |
   | `/metrics` | Prometheus **text** counters | First-line “did WISMO get hit?” |

   `/readyz` includes `git_sha` so Priya can paste a version without opening Docker. It must **never** include `api_key`.

8. Walk `/v1/wismo` — this is the whole product path:

```python
@api.post("/v1/wismo", dependencies=[Depends(require_api_key)])
async def wismo(
    body: WismoRequest,
    x_correlation_id: str | None = Header(default=None),
) -> dict:
```

   Then, in order:

   ```
   bump _REQUESTS
     → mint or accept X-Correlation-Id
       → create_session (or reuse body.session_id)
         → runner.run_async(...)
           → last text part becomes final_text
             → JSON: session_id, correlation_id, engine=google-adk, latency_ms
   ```

   | Piece | Why |
   |-------|-----|
   | `Depends(require_api_key)` | Runs before the handler. 401 never touches ADK. |
   | `WismoRequest.message` | `min_length=1`, `max_length=4000` — empty body is 422, not a model call |
   | `X-Correlation-Id` | Same idea as Lesson 04’s tool corr id, now at the **HTTP** edge |
   | `runner.session_service.create_session(app_name="meridian_orderops", user_id="api")` | ADK session, not a DIY dict |
   | `types.Content(role="user", parts=[types.Part.from_text(text=body.message)])` | Same message shape `adk web` uses |
   | `"engine": "google-adk"` | Smoke asserts this. A stub cannot fake it and pass `smoke.sh` honestly |
   | `except Exception` → 500 `agent_error` | Do not leak stack traces to CX |

9. Install the edge deps into the **existing** venv (the image will install them again later). Then prove `/healthz` and 401 **without** Gemini.

```bash
cd /Users/alishaghatane/dev/agent-learn-sme
source .venv/bin/activate
pip install -r project/meridian_ops/deploy/requirements.txt
export PYTHONPATH=project
python - <<'PY'
from fastapi.testclient import TestClient
from meridian_ops.deploy.app import api

c = TestClient(api)
h = c.get("/healthz")
print("healthz", h.status_code, h.json())
z = c.get("/readyz")
print("readyz", z.status_code, z.json())
u = c.post("/v1/wismo", json={"message": "Status for MC-1048292"})
print("no key", u.status_code, u.json())
w = c.post(
    "/v1/wismo",
    json={"message": "Status for MC-1048292"},
    headers={"X-Api-Key": "wrong-key"},
)
print("wrong key", w.status_code)
PY
```

   - `pip install -r …` — install **from the file** (`-r` = requirements file). Matches the image.
   - `TestClient(api)` — in-process HTTP. No port. `/healthz` does not need Docker.

### Expect

```
healthz 200 {'status': 'ok'}
readyz 200 {'status': 'ready', 'env': 'local', 'git_sha': 'unknown'}
no key 401 {'detail': 'unauthorized'}
wrong key 401
```

You did **not** call `/v1/wismo` with a good key yet. That needs `GOOGLE_API_KEY` and uvicorn (Task 2).

> **Tip:** `git_sha: unknown` is correct until you pass `MERIDIAN_GIT_SHA`. Task 3 injects it at `docker run`.

> **Watch out:** Do not “fix” 401 by removing `require_api_key`. An open WISMO route on a laptop demo becomes an open WISMO route in Compose.

### Scoreboard after Task 1

| Control | In place? |
|---------|-----------|
| OrderOps Workflow loads; fallback gone | **Yes** |
| uvicorn + live `/v1/wismo` | Not yet |
| Docker image / `docker run` | Not yet |
| Compose healthcheck | Not yet |
| `smoke.sh` | Not yet |
| Rollback drill from the runbook | Not yet |

---

## Task 2 — uvicorn + curl (the same process Compose will run)

### Why

`TestClient` proved the door. uvicorn is what the **Dockerfile `CMD`** runs. If you skip this, Docker will be the first time you see bind-address bugs.

### Do this

1. Keep the venv active. Start the API on loopback only. Leave this terminal running.

```bash
cd /Users/alishaghatane/dev/agent-learn-sme
source .venv/bin/activate
export PYTHONPATH=project
export MERIDIAN_API_KEY=dev-local-key-change-me
export MERIDIAN_ENV=local
export MERIDIAN_GIT_SHA="$(git rev-parse --short HEAD)"
export GOOGLE_API_KEY="YOUR_KEY"
uvicorn meridian_ops.deploy.app:api --host 127.0.0.1 --port 8080
```

   | Flag / env | What it does |
   |------------|----------------|
   | `PYTHONPATH=project` | `import meridian_ops` and `import meridian_orderops` resolve |
   | `MERIDIAN_API_KEY` | Must match the `X-Api-Key` you send. Default in Settings is this same string. |
   | `MERIDIAN_ENV=local` | Shows up on `/readyz` and in WISMO JSON |
   | `MERIDIAN_GIT_SHA=…` | `git rev-parse --short HEAD` prints the short commit. `--short` is the abbreviated sha. |
   | `GOOGLE_API_KEY` | Gemini for language nodes. Function nodes do not need it; this graph still has narrators. |
   | `uvicorn …:api` | Load the **`api`** object (the FastAPI app), not a random `app` name |
   | `--host 127.0.0.1` | Bind **loopback only**. Your laptop, not the LAN. Docker will use `0.0.0.0`. |
   | `--port 8080` | Listen port. Must match the curls and the Dockerfile `EXPOSE`. |

   Expect a line like `Uvicorn running on http://127.0.0.1:8080`. Leave it there.

2. **New terminal.** Same venv. Probe in this order: liveness, readiness, missing key, happy path.

```bash
cd /Users/alishaghatane/dev/agent-learn-sme
source .venv/bin/activate

curl -fsS http://127.0.0.1:8080/healthz
echo
curl -fsS http://127.0.0.1:8080/readyz
echo

curl -sS -o /tmp/wismo401.txt -w "%{http_code}\n" \
  http://127.0.0.1:8080/v1/wismo \
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
   | `-f` | Fail the command on HTTP 4xx/5xx (so a 500 is not silent) |
   | `-s` | Silent progress bar (no `#` meter) |
   | `-S` | Still **show errors** if `-s` would hide them. Pair as `-fsS` or `-sS`. |
   | `-o /tmp/wismo401.txt` | Write body to a file |
   | `-w "%{http_code}\n"` | After the transfer, print the status code |
   | `-H "Content-Type: application/json"` | FastAPI parses JSON. Wrong type → 422 |
   | `-H "X-Api-Key: …"` | The header `require_api_key` reads |
   | `-d '{...}'` | Request **body**. `curl` POSTs when `-d` is present |
   | `python -m json.tool` | Pretty-print so `engine` / `final_text` are readable |

   You do **not** need `curl -N` here. `-N` (`--no-buffer`) is for streaming (Lesson 22). `/v1/wismo` returns one JSON object when the Workflow finishes.

### Expect

- `/healthz` → `{"status":"ok"}`
- `/readyz` → `"status":"ready"` plus your `env` and short `git_sha`
- Missing API key → **`401`** printed by `-w`
- Happy path JSON includes:

```json
{
  "session_id": "...",
  "correlation_id": "corr-...",
  "final_text": "...",
  "engine": "google-adk",
  "env": "local",
  "git_sha": "...",
  "image_tag": "dev",
  "latency_ms": 1234.56
}
```

   `final_text` should talk about `MC-1048292`: **delivered**, **no POD photo**, a next step. It must not invent a porch photo. It must not claim a refund.

If uvicorn died on import, the routing map in Task 1 did not stick — fix that before Docker.

If `final_text` is empty but HTTP 200, the graph paused or produced no text parts. WISMO should not pause. Check the uvicorn traceback.

> **Tip:** Keep this uvicorn until you are ready for Docker. Then `Ctrl+C` so port 8080 is free.

> **Watch out:** `InMemoryRunner` sessions die when the process dies. That is correct for this lab. Do not pickle sessions next to the repo. Lesson 29 is durable sessions. Lesson 15 is HITL resume inside ADK.

### Scoreboard after Task 2

| Control | In place? |
|---------|-----------|
| OrderOps Workflow loads; fallback gone | Yes |
| uvicorn + live `/v1/wismo` | **Yes** |
| Docker image / `docker run` | Not yet |
| Compose healthcheck | Not yet |
| `smoke.sh` | Not yet |
| Rollback drill from the runbook | Not yet |

---

## Task 3 — Walk the Dockerfile, then build and run it

### Why

Images are what you promote. A working uvicorn on your laptop does not prove the container has `PYTHONPATH`, a non-root user, and **no baked secrets**.

Stop the Task 2 uvicorn (`Ctrl+C`) so port 8080 is free.

### Do this

1. Open `project/meridian_ops/deploy/Dockerfile`. Read it **top to bottom**. Each line is a layer.

```dockerfile
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

RUN useradd -u 10001 -m appuser

COPY project/meridian_ops /app/meridian_ops
COPY project/meridian_orderops /app/meridian_orderops
COPY project/meridian_ops/deploy/requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir -r /app/requirements.txt \
    && pip install --no-cache-dir "google-adk>=2.0.0" mcp

USER 10001:10001
EXPOSE 8080

# Secrets via env at runtime — never bake GOOGLE_API_KEY / MERIDIAN_API_KEY into the image.
CMD ["uvicorn", "meridian_ops.deploy.app:api", "--host", "0.0.0.0", "--port", "8080"]
```

   | Instruction | What it does | Why this order |
   |-------------|----------------|----------------|
   | `FROM python:3.12-slim` | Base image: Python 3.12, small Debian | First layer. Everything else stacks on it. |
   | `PYTHONDONTWRITEBYTECODE=1` | Do not write `.pyc` files | Keeps the image smaller and avoids root-owned cache later |
   | `PYTHONUNBUFFERED=1` | Print logs immediately | `docker logs` shows uvicorn lines as they happen |
   | `PYTHONPATH=/app` | `import meridian_ops` finds `/app/meridian_ops` | Same idea as `export PYTHONPATH=project`, inside the box |
   | `WORKDIR /app` | Default directory for later `COPY` / `CMD` | Paths below are relative to `/app` unless absolute |
   | `useradd -u 10001 -m appuser` | Create uid **10001** with a home (`-m`) | You will `USER` to this. `-u` pins the id so it is stable |
   | `COPY project/meridian_ops …` | Copy **only** the ops package | Build **context** is the repo root (see `docker build` below) |
   | `COPY project/meridian_orderops …` | The Workflow the edge imports | Without this, `from meridian_orderops.agent import root_agent` fails in the image |
   | `COPY …/requirements.txt` | Deps file as its own layer | Changing app code does not bust the pip cache if this file is unchanged |
   | `pip install --no-cache-dir` | Install; `--no-cache-dir` drops pip’s download cache | Smaller image. `-r` reads the requirements file. |
   | `USER 10001:10001` | Drop root. group 10001 too | A breakout as root is worse than as `appuser` |
   | `EXPOSE 8080` | Documents the port | Does **not** publish it. `docker run -p` does. |
   | `CMD ["uvicorn", …]` | Default process | Exec form (JSON array) — no shell, so signals reach uvicorn |

   Walk the **CMD** flags (different from Task 2 on purpose):

   | Flag | What it does inside the container |
   |------|-----------------------------------|
   | `--host 0.0.0.0` | Bind **all** interfaces. `127.0.0.1` inside Docker is only the container, so `-p 8080:8080` would look dead from your Mac. |
   | `--port 8080` | Same port `EXPOSE` and Compose publish |

2. Pin ADK in the image to the curriculum version. Change the pip line to:

```dockerfile
RUN pip install --no-cache-dir -r /app/requirements.txt \
    && pip install --no-cache-dir "google-adk==2.6.3" "mcp>=1.24,<2"
```

   `==2.6.3` is the pin. `mcp>=1.24,<2` is the extra ADK 2.6.3’s `[mcp]` extra uses (Lesson 16). You are not installing a second framework.

   There is **no** `ENV GOOGLE_API_KEY=` in this file. That is the point of the comment above `CMD`.

3. Build from the **repo root**. The Dockerfile `COPY project/...` paths are relative to the context, not relative to the Dockerfile’s folder.

```bash
cd /Users/alishaghatane/dev/agent-learn-sme
docker build -f project/meridian_ops/deploy/Dockerfile -t meridian-orderops:0.1.0 .
```

   | Flag | What it does |
   |------|----------------|
   | `-f project/meridian_ops/deploy/Dockerfile` | Path to the Dockerfile (`-f` = file). Required because it is not `./Dockerfile`. |
   | `-t meridian-orderops:0.1.0` | Name:tag. `0.1.0` is what Compose and the rollback runbook expect. |
   | `.` | Build **context** = repo root. `COPY project/meridian_ops` needs this. |

### Expect

Last lines like `naming to docker.io/library/meridian-orderops:0.1.0`. First build downloads `python:3.12-slim` and pip packages. Later builds reuse layers.

4. Run the image. Secrets enter as **`-e`**, not as files copied in.

```bash
docker run --rm -p 8080:8080 \
  -e MERIDIAN_API_KEY=dev-local-key-change-me \
  -e MERIDIAN_ENV=local-docker \
  -e MERIDIAN_GIT_SHA="$(git rev-parse --short HEAD 2>/dev/null || echo local)" \
  -e MERIDIAN_IMAGE_TAG=0.1.0 \
  -e GOOGLE_API_KEY="$GOOGLE_API_KEY" \
  meridian-orderops:0.1.0
```

   | Flag | What it does |
   |------|----------------|
   | `--rm` | Delete the container when it exits. Keeps `docker ps -a` clean. |
   | `-p 8080:8080` | Publish `host:container`. Left is your Mac; right is `EXPOSE`. |
   | `-e NAME=value` | Runtime env. Settings and Gemini read these. **Not** baked in the image. |
   | `"$GOOGLE_API_KEY"` | Your **shell’s** key, passed through. If this is empty, `final_text` will be empty or 500. |

   `2>/dev/null` on `git rev-parse` hides git errors; `|| echo local` is the fallback label if you are not in a repo. You are.

5. **Another terminal.** Repeat the Task 2 curls (healthz, readyz, 401, WISMO). Expect `"env": "local-docker"` and `"image_tag": "0.1.0"`.

6. Prove the process is **not** root. In a third terminal while the container runs:

```bash
docker ps --format '{{.ID}} {{.Image}} {{.Ports}}'
# copy the container id, then:
docker exec <CONTAINER_ID> id
```

   | Flag | What it does |
   |------|----------------|
   | `docker ps` | List running containers |
   | `--format '…'` | Go template. Only id, image, ports — not a wall of columns |
   | `docker exec` | Run one command **inside** the running container |
   | `id` | Print uid/gid |

### Expect

```
uid=10001(appuser) gid=10001(appuser) groups=10001(appuser)
```

If you see `uid=0(root)`, the `USER` line is missing or an entrypoint switched back. Fix the Dockerfile; do not “just run as root for the lab.”

> **Tip:** Copy only what the edge needs. This Dockerfile does **not** `COPY` your home `.env`. If you add `COPY . /app`, you will bake secrets and `.venv` into the image.

> **Watch out:** Building with `-f Dockerfile` from `deploy/` and context `.` **there** fails: there is no `project/meridian_ops` inside `deploy/`. Always context = repo root.

### Scoreboard after Task 3

| Control | In place? |
|---------|-----------|
| OrderOps Workflow loads; fallback gone | Yes |
| uvicorn + live `/v1/wismo` | Yes |
| Docker image / `docker run` | **Yes** |
| Compose healthcheck | Not yet |
| `smoke.sh` | Not yet |
| Rollback drill from the runbook | Not yet |

---

## Task 4 — Compose: the shared “stage-like” story

### Why

`docker run` with six `-e` flags is easy to mistype in a huddle. Compose is the file the team shares. Healthcheck is how Compose (and later Kubernetes) decides **ready**.

Stop the Task 3 `docker run` (`Ctrl+C` in that terminal).

### Do this

1. Open `project/meridian_ops/deploy/docker-compose.yml` and walk it.

```yaml
services:
  orderops-api:
    build:
      context: ../../..
      dockerfile: project/meridian_ops/deploy/Dockerfile
    image: meridian-orderops:${MERIDIAN_IMAGE_TAG:-0.1.0}
    ports:
      - "8080:8080"
    environment:
      MERIDIAN_API_KEY: ${MERIDIAN_API_KEY:-dev-local-key-change-me}
      MERIDIAN_ENV: compose
      MERIDIAN_MODEL_NAME: ${MERIDIAN_MODEL_NAME:-gemini-2.5-flash}
      MERIDIAN_GIT_SHA: ${MERIDIAN_GIT_SHA:-local}
      MERIDIAN_IMAGE_TAG: ${MERIDIAN_IMAGE_TAG:-0.1.0}
      GOOGLE_API_KEY: ${GOOGLE_API_KEY:-}
    healthcheck:
      test:
        [
          "CMD",
          "python",
          "-c",
          "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/healthz')",
        ]
      interval: 10s
      timeout: 3s
      retries: 5
```

   | Key | What it does |
   |-----|----------------|
   | `context: ../../..` | From `deploy/`, three levels up is the **repo root** — same context as Task 3 |
   | `dockerfile: project/meridian_ops/deploy/Dockerfile` | Path **inside that context** |
   | `image: meridian-orderops:${MERIDIAN_IMAGE_TAG:-0.1.0}` | Tag the build. `${VAR:-default}` uses `0.1.0` if the var is unset |
   | `ports: "8080:8080"` | Same publish as `docker run -p` |
   | `MERIDIAN_ENV: compose` | Hard-coded so `/readyz` says you are on Compose, not local uvicorn |
   | `${GOOGLE_API_KEY:-}` | Empty default. You must provide the key via `.env` or the shell |
   | `healthcheck.test` | Inside the container, GET `/healthz`. `CMD` form = exec, no shell |
   | `interval: 10s` | Probe every 10 seconds |
   | `timeout: 3s` | One probe may take at most 3s |
   | `retries: 5` | Unhealthy only after 5 failures (~50s) |

   Pin the compose default model. Change the `MERIDIAN_MODEL_NAME` line to:

```yaml
      MERIDIAN_MODEL_NAME: ${MERIDIAN_MODEL_NAME:-gemini-3.5-flash}
```

   Same pin in `project/meridian_ops/deploy/.env.example`:

```
MERIDIAN_API_KEY=replace-me
MERIDIAN_ENV=local
MERIDIAN_MODEL_NAME=gemini-3.5-flash
MERIDIAN_IMAGE_TAG=0.1.0
MERIDIAN_GIT_SHA=unknown
GOOGLE_API_KEY=replace-me
```

2. Create a **local** `.env` next to the compose file. Compose auto-loads `.env` from that directory. The repo gitignores `**/.env`.

```bash
cd /Users/alishaghatane/dev/agent-learn-sme/project/meridian_ops/deploy
cp -n .env.example .env
```

   | Flag | What it does |
   |------|----------------|
   | `cp -n` | `--no-clobber`: do **not** overwrite an existing `.env`. Safe if you already filled keys. |

   Edit `.env`: set `GOOGLE_API_KEY` to your real key, and `MERIDIAN_API_KEY` to `dev-local-key-change-me` (or another value you will send on `X-Api-Key`). Never commit `.env`.

3. Start Compose from that directory so it finds `docker-compose.yml` and `.env`.

```bash
cd /Users/alishaghatane/dev/agent-learn-sme/project/meridian_ops/deploy
docker compose up --build -d
docker compose ps
```

   | Flag | What it does |
   |------|----------------|
   | `up` | Create and start |
   | `--build` | Rebuild the image first (picks up Task 3 Dockerfile pin) |
   | `-d` | Detached — returns your terminal |
   | `ps` | Show name, status, **health** |

### Expect

`docker compose ps` shows `orderops-api` as **healthy** (or `health: starting` then healthy within ~50s).

```bash
curl -fsS http://127.0.0.1:8080/readyz
```

   includes `"env": "compose"`.

> **Tip:** `docker compose logs -f orderops-api` follows (`-f`) uvicorn. `Ctrl+C` only stops the follow, not the container.

> **Watch out:** If `.env` still has `GOOGLE_API_KEY=replace-me`, WISMO 500s or returns empty `final_text`. Healthcheck can still be green — it only hits `/healthz`. That is why Task 5 exists.

### Scoreboard after Task 4

| Control | In place? |
|---------|-----------|
| OrderOps Workflow loads; fallback gone | Yes |
| uvicorn + live `/v1/wismo` | Yes |
| Docker image / `docker run` | Yes |
| Compose healthcheck | **Yes** |
| `smoke.sh` | Not yet |
| Rollback drill from the runbook | Not yet |

---

## Task 5 — `smoke.sh` (the gate before “we’re up”)

### Why

Humans forget a curl under pressure. The repo already has the script. You will walk every line, then run it.

### Do this

1. Open `project/meridian_ops/deploy/smoke.sh`.

```bash
#!/usr/bin/env bash
set -euo pipefail

BASE="${1:-http://127.0.0.1:8080}"
KEY="${MERIDIAN_API_KEY:-dev-local-key-change-me}"

echo "==> healthz"
curl -fsS "$BASE/healthz" >/dev/null

echo "==> readyz"
curl -fsS "$BASE/readyz" >/dev/null

echo "==> wismo"
curl -fsS "$BASE/v1/wismo" \
  -H "Content-Type: application/json" \
  -H "X-Api-Key: $KEY" \
  -H "X-Correlation-Id: smoke-$(date +%s)" \
  -d '{"message":"Status for MC-1048292 — nothing at the door"}' \
  | tee /tmp/meridian_wismo_smoke.json >/dev/null

python3 - <<'PY'
import json
from pathlib import Path

data = json.loads(Path("/tmp/meridian_wismo_smoke.json").read_text())
assert data.get("engine") == "google-adk", data
assert data.get("final_text"), "expected final_text from ADK"
assert data.get("correlation_id"), "expected correlation_id"
print("SMOKE OK", data.get("correlation_id"), "latency_ms=", data.get("latency_ms"))
PY
```

   | Piece | What it does |
   |-------|----------------|
   | `#!/usr/bin/env bash` | Find `bash` on `PATH` (works on more laptops than `/bin/bash`) |
   | `set -euo pipefail` | `-e` exit on error; `-u` unset vars are errors; `-o pipefail` a failing `curl` in a pipe fails the script |
   | `BASE="${1:-http://127.0.0.1:8080}"` | First argument, or localhost. Stage will pass a real URL. |
   | `KEY="${MERIDIAN_API_KEY:-…}"` | Same default as Settings / Compose |
   | `curl … >/dev/null` | Body discarded; `-f` still fails the script on 4xx/5xx |
   | `-H "X-Correlation-Id: smoke-$(date +%s)"` | Unique-ish id. `date +%s` is epoch seconds. |
   | `tee /tmp/meridian_wismo_smoke.json >/dev/null` | `tee` writes the file; stdout is discarded so the script stays quiet until the assert |
   | `assert engine == "google-adk"` | A stub that returns `"engine": "mock"` **fails smoke** |
   | `assert final_text` | Empty string is a failed deploy, even if HTTP 200 |

2. Make it executable and run it against Compose.

```bash
chmod +x /Users/alishaghatane/dev/agent-learn-sme/project/meridian_ops/deploy/smoke.sh
export MERIDIAN_API_KEY=dev-local-key-change-me
/Users/alishaghatane/dev/agent-learn-sme/project/meridian_ops/deploy/smoke.sh http://127.0.0.1:8080
```

   | Flag | What it does |
   |------|----------------|
   | `chmod +x` | Set the executable bit so you can invoke the file by path |
   | First argument `http://127.0.0.1:8080` | Becomes `BASE`. No trailing slash — the script adds `/healthz`. |

### Expect

```
==> healthz
==> readyz
==> wismo
SMOKE OK corr-... latency_ms= ...
```

If smoke fails, **do not** share the URL. Fix logs (`docker compose logs orderops-api`), then re-run smoke.

> **Tip:** Lesson 41 will make this script a CI gate. Today you are the gate.

> **Watch out:** `MERIDIAN_API_KEY` in the **shell** must match Compose. If Compose used the default and you export a different key, smoke 401s and `-e` exits before the Python assert.

### Scoreboard after Task 5

| Control | In place? |
|---------|-----------|
| OrderOps Workflow loads; fallback gone | Yes |
| uvicorn + live `/v1/wismo` | Yes |
| Docker image / `docker run` | Yes |
| Compose healthcheck | Yes |
| `smoke.sh` | **Yes** |
| Rollback drill from the runbook | Not yet |

---

## Task 6 — `/metrics` and the rollback you can run today

### Why

Deploy without a first move is a trap for future-you. This repo already has `ROLLBACK.md`. You will **execute** the local Compose path — not write a new Cloud Run stack. Lesson 41 is canary % and `gcloud run services update-traffic`. Today is: tag `0.1.0`, smoke, know the command.

### Do this

1. Hit metrics while Compose is up:

```bash
curl -fsS http://127.0.0.1:8080/metrics
```

### Expect

Prometheus text (not JSON):

```
# HELP meridian_wismo_requests_total WISMO requests
# TYPE meridian_wismo_requests_total counter
meridian_wismo_requests_total 1
# HELP meridian_wismo_errors_total WISMO errors
# TYPE meridian_wismo_errors_total counter
meridian_wismo_errors_total 0
```

   The numbers match how many times you hit `/v1/wismo` **in this process** (Compose). They reset when the container restarts. That is enough for a lab counter.

2. Read `project/meridian_ops/deploy/runbooks/DEPLOY.md` (SHIP checklist: eval card, smoke, stage first). Read `ROLLBACK.md` through the **Local compose / lab** section.

3. Run that local rollback **as written** — retag / recreate on `0.1.0` and smoke. From the **repo root**:

```bash
cd /Users/alishaghatane/dev/agent-learn-sme
export MERIDIAN_IMAGE_TAG=0.1.0
export MERIDIAN_API_KEY=dev-local-key-change-me
docker compose -f project/meridian_ops/deploy/docker-compose.yml up -d --build
./project/meridian_ops/deploy/smoke.sh
```

   | Flag | What it does |
   |------|----------------|
   | `-f project/meridian_ops/deploy/docker-compose.yml` | Compose file path so you can stay at the repo root (same as the runbook) |
   | `up -d --build` | Recreate detached, rebuild if needed |
   | `./project/meridian_ops/deploy/smoke.sh` | Default BASE is localhost:8080 |

### Expect

`SMOKE OK` again. You just practiced the first rollback move: **go back to the last good tag**, then smoke. You did not hot-fix a prompt during a SEV.

4. Optional but useful: curl `/readyz` and paste `git_sha` / `image_tag` as if you were in the incident channel. Those fields exist so you do not SSH into a box to ask “which version?”

Leave Compose up if you want, or:

```bash
docker compose -f project/meridian_ops/deploy/docker-compose.yml down
```

   `down` stops and removes the Compose containers (not the image). `--rm` on Task 3 already cleaned one-off runs.

> **Tip:** `DEPLOY.md` mentions Cloud Run revisions and canary 10% → 50% → 100%. That is Lesson 41. The **engine** stays this FastAPI → ADK Runner. You are not required to run `gcloud` today.

> **Watch out:** Do not add `project/meridian_ops/runtime/checkpoints/` (that path is gitignored for a reason). Sessions belong to ADK (Lesson 15 / 29), not a folder next to the image.

### Scoreboard after Task 6

| Control | In place? |
|---------|-----------|
| OrderOps Workflow loads; fallback gone | Yes |
| uvicorn + live `/v1/wismo` | Yes |
| Docker image / `docker run` | Yes |
| Compose healthcheck | Yes |
| `smoke.sh` | Yes |
| Rollback drill from the runbook | **Yes** |

---

## How it works (deeper dive)

### Probe split

| Probe | Fails when | Orchestrator action |
|-------|------------|---------------------|
| Liveness `/healthz` | Process deadlocked or crashed | Restart the container |
| Readiness `/readyz` | You later add a real dep check (session service, etc.) | Stop sending traffic; do **not** necessarily restart |
| Smoke | Engine missing, empty `final_text`, 401, timeout | **You** abort the release |

A green healthcheck + a red smoke is a common lie: Gemini key missing, graph paused, empty narrator. Smoke is the WISMO truth.

### Why FastAPI in front of ADK

| Need | FastAPI | `adk web` |
|------|---------|-----------|
| API key / future OIDC | Yes | Demo UI, not a product AuthZ story |
| Stable JSON contract | `/v1/wismo` | Chat bubbles |
| Probes | `/healthz` `/readyz` | No |
| Multi-instance | Image + Compose / Cloud Run | One developer browser |
| Eval mapping | `git_sha` + `image_tag` on the response | Easy to forget which prompt |

NATIVE-ADK.md allows this edge: AuthN/Z and webhooks are product API. They still call `Runner`.

### Cost and safety still apply

- Language nodes use `gemini-3.5-flash` (the Workflow’s `GEMINI` constant).
- Lesson 07 kill switches still run **inside** a turn.
- Compose `ports` on a laptop is not “prod public.” Do not `--allow-unauthenticated` later without AuthZ.

### What Lesson 41 adds

CI/CD, env promotion, canary %, automated rollback drills, pager expectations — the **release train**. Same image, same `smoke.sh`.

---

## Common pitfalls / troubleshooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| `ValidationError` / `input_value='WISMO'` | 3-tuple edges | Task 1 routing map |
| uvicorn import dies | `PYTHONPATH` unset | `export PYTHONPATH=project` from repo root |
| 401 loops | Key mismatch | Same `MERIDIAN_API_KEY` in Compose `.env` and smoke shell |
| 422 on WISMO | Missing `Content-Type: application/json` or empty `message` | Add the header; message `min_length=1` |
| Image build: `COPY project/meridian_ops` not found | Context is `deploy/` | Build from repo root; Compose `context: ../../..` |
| `docker run` + empty WISMO / 500 | Empty `GOOGLE_API_KEY` | `-e GOOGLE_API_KEY="$GOOGLE_API_KEY"` after exporting it |
| Healthy Compose, failed smoke | Healthcheck only hits `/healthz` | Logs + smoke; fix key or graph |
| `uid=0(root)` | No `USER` | Restore `USER 10001:10001` |
| Secrets in git | Committed `.env` | Rotate keys; `**/.env` is already gitignored — keep it that way |
| `InMemoryRunner(..., plugins=)` | 2.6.3 forbids `app=` plus `plugins=` | Plugins go on `App` (Lesson 26) |

---

## You are done when

- [ ] Existing `.venv` sourced; ADK prints `2.6.3`
- [ ] OrderOps `Workflow` imports; `ImportError` fallback **removed**
- [ ] `TestClient` `/healthz` 200 and `/v1/wismo` without key **401**
- [ ] uvicorn curls return `"engine": "google-adk"` and a WISMO `final_text` for `MC-1048292`
- [ ] You can explain every Dockerfile line; image runs as uid `10001`
- [ ] Compose is healthy; `.env` is local-only
- [ ] `smoke.sh` prints `SMOKE OK`
- [ ] You ran the **local** rollback commands from `ROLLBACK.md` and smoked again
- [ ] No second deploy folder, no `adk web` as the product URL

---

## Knowledge check

Answer from this lab, not from generic “how to Docker” lore.

1. Why is `/readyz` separate from `/healthz`?  
2. What must never be a `Dockerfile` `ENV` or a `COPY`’d `.env`?  
3. Why does `docker build` use context `.` at the **repo root**?  
4. Why `--host 0.0.0.0` in the image and `--host 127.0.0.1` on your laptop uvicorn?  
5. What three asserts does `smoke.sh` run on the WISMO JSON?  
6. Why keep ADK behind FastAPI instead of exposing `adk web`?

### Answers

1. Alive ≠ safe for traffic. Liveness restarts; readiness stops sending Maya.  
2. `GOOGLE_API_KEY`, `MERIDIAN_API_KEY`, and any other secret. Runtime `-e` / Compose `.env` only.  
3. `COPY project/meridian_ops` is relative to context. Context `deploy/` does not contain `project/`.  
4. Inside Docker, `127.0.0.1` is the container. Publish (`-p`) needs the process on `0.0.0.0`. On a laptop, loopback keeps the port off the LAN.  
5. `engine == "google-adk"`; `final_text` non-empty; `correlation_id` present.  
6. AuthZ, stable contract, probes, metrics, an image you can roll back. `adk web` is the flashlight, not the storefront.

---

## Recap

**What you built today:** the real Meridian OrderOps container — FastAPI → `App` → `InMemoryRunner` → Workflow — with health, Docker layers, Compose, smoke, and a rollback you actually ran.

**What you now understand:** the edge is the door; ADK is the engine; health ≠ smoke; secrets are runtime env.

**What you can do next:** Lesson 13 walks the same Workflow’s routes in `adk web` and pytest. Lesson 41 puts `smoke.sh` on the release train.

**Not done yet:** Cloud Run traffic splitting, durable sessions (Lesson 29), HITL overnight resume (Lesson 15).

---

## Stretch goal

Add `GET /v1/version` that returns `git_sha`, `image_tag`, and `env` only (no secrets). Hit it from smoke or a one-line curl so on-call can paste one URL. Keep `/readyz` as the probe; version is for humans.

---

## Feedback

- Could you explain the Dockerfile from `FROM` to `CMD` without opening the file?  
- What tripped you up: routing-map import, bind address, Compose `.env`, or smoke 401?  
- Note the **task number** and what you expected vs what happened (command + first lines of output). That is the signal that improves this lesson — “it was confusing” is not.

---

## Navigate

**← Prev** [Lesson 11 — Tracing & observability](11-tracing-observability.md)  
**Next (curriculum Pack C) →** [Lesson 13 — Graph workflows](13-graph-workflows.md)  
**Next (ops deep) →** [Lesson 41 — CI/CD & SRE release ops](41-cicd-sre-deployment-ops.md)
