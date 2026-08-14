# Lesson 29 — Sessions & state at scale

**Level:** Advanced (platform)  
**Time:** ~120–150 minutes  
**Prerequisites:** Lessons 03, 12, 15 (session object, deploy, HITL resume)  
**Lab outcome:** Stop relying on **in-process** chat memory. Wire **ADK session services**, prove **replay**, and document **stickiness** vs a shared store — no homemade checkpoint database

**Standard:** [docs/NATIVE-ADK.md](../docs/NATIVE-ADK.md)

---

## At a glance

Devon’s handheld is a **multi-turn** conversation: order id, then “and the oat milk,” then “approve the substitute.”

That conversation is a **session**: ADK’s record of events + state for one `app_name` + `user_id` + `session_id`.

| Store | Survives process restart? | Survives two Cloud Run instances? | Lab use |
|-------|---------------------------|-----------------------------------|---------|
| `InMemorySessionService` | no | no | `adk web`, unit tests |
| `DatabaseSessionService` / `VertexAiSessionService` | yes | yes, if all instances share it | stage/prod |
| DIY JSON files of “checkpoints” | maybe | maybe | **forbidden** as a second ADK |

```
Handheld  →  FastAPI edge  →  Runner
                 │                │
                 │                ▼
                 │         ADK SessionService
                 │                │
                 └──── session_id ┘
```

---

## Why this matters

Lesson 12’s edge uses `InMemoryRunner`. That is fine for a laptop demo.

Friday: you scale to **two** containers because Black Friday WISMO spikes.

- Request 1 lands on instance A, creates a session  
- Request 2 (“also refund it”) lands on instance B  
- Instance B has **never seen** the session  

Priya approves a HITL refund tomorrow (Lesson 15). If the session lived only in RAM, the pause is gone.

This lesson is how OrderOps stays a conversation under **more than one process**.

---

## Know these

| Term | Meaning |
|------|---------|
| **Session** | ADK object: events + state for one conversation |
| **Session service** | The ADK component that **loads/saves** sessions |
| **Event** | One model/tool/user turn in that session |
| **Replay** | Rebuild what happened by reading events (debug, eval, resume) |
| **Stickiness** | Load balancer always sends one `session_id` to the same instance |
| **Shared store** | Every instance reads/writes the same session backend |
| **Affinity** | Another word for stickiness |

> **Tip:** Stickiness is a **crutch**. Shared session storage is the real production design. Stickiness only reduces cache misses; it must not be the only way HITL resume works.

---

## Task 1 — Prove in-memory dies on restart

### Why

You need a failing demo so the shared store is not theoretical.

### Do this

1. Run `adk web` on a package you already use (`meridian_orderops_router` or `meridian_order_status`).  
2. Start a chat. Send: `Where is order MC-1048277?`  
3. Note the session id in the UI (or from logs).  
4. Stop the process (`Ctrl+C`). Start `adk web` again.  
5. Try to continue the **same** session if the UI allows, or start a new chat and observe that prior turns are gone.

Write `project/meridian_ops/decisions/29-session-store.md`:

- What disappeared (turns, state keys, HITL pause)?  
- Would two `adk web` processes share that memory? (answer: no)

### Expect

A written proof that **RAM is not a platform**.

> **Watch out:** Do not “fix” this with a pickle file of `Runner` internals. That is a DIY session store.

---

## Task 2 — The three native session services

### Why

ADK already ships the store you need. Know all three before you reach for anything else.

`google-adk` 2.6.3 gives you exactly these:

| Class | Backend | Survives restart | Shared across replicas | Extra install |
|-------|---------|------------------|------------------------|---------------|
| `InMemorySessionService` | RAM | no | no | none |
| `DatabaseSessionService` | any SQLAlchemy URL (SQLite, Postgres) | **yes** | yes, with a shared DB | **`google-adk[db]`** |
| `VertexAiSessionService` | Vertex AI managed | **yes** | yes | cloud project |

### Do this

`DatabaseSessionService` needs SQLAlchemy, which is not in the base install. Add it:

```bash
source .venv/bin/activate
pip install -U "google-adk[db]>=2.6.3"
# [db]: pulls in SQLAlchemy, which DatabaseSessionService needs
# -U: upgrade; quotes stop the shell reading >= as redirection
```

Skip that install and you get a precise error telling you exactly this:

```
ImportError: The 'sqlalchemy' package is required to use this feature.
Please install it by running: pip install google-adk[db]
```

Then confirm all three:

```bash
python - <<'PY'
from google.adk.sessions import (
    DatabaseSessionService,
    InMemorySessionService,
    VertexAiSessionService,
)
print("all three import OK")
PY
```

Record your choice in `29-session-store.md`:

| Environment | Service | Why |
|-------------|---------|-----|
| Unit tests | `InMemorySessionService` | fast, disposable |
| This lab | `DatabaseSessionService` (SQLite) | proves durability on one machine |
| Meridian prod target | | pick one and justify |

### Expect

`all three import OK`, and a filled row for your production target.

---

## Task 3 — Shared store lab (SQLite or documented ADK backend)

### Why

You need at least one session that **survives restart** on a single machine before Redis/Memorystore in the cloud.

### Do this

Use `DatabaseSessionService` pointed at a **local SQLite file**:

```python
from google.adk.apps import App
from google.adk.runners import Runner
from google.adk.sessions import DatabaseSessionService

session_service = DatabaseSessionService(db_url="sqlite:///./.adk/meridian_sessions.db")
# db_url: standard SQLAlchemy URL — swap sqlite:// for postgresql:// in stage

app = App(name="meridian_orderops", root_agent=root_agent)
runner = Runner(app=app, session_service=session_service)
```

Wire this in a **lab-only** path, for example `project/meridian_ops/runtime/session_factory.py`, that:

1. Reads `MERIDIAN_SESSION_BACKEND=memory|sqlite`  
2. Returns the matching ADK session service  
3. Never implements `get_session` yourself

Prove:

```bash
# mkdir -p: create .adk if missing; sqlite file appears after first run
mkdir -p project/.adk

export MERIDIAN_SESSION_BACKEND=sqlite
# run your small script that creates a session, appends a user message, lists events
```

Stop Python. Start again with the **same** `session_id`. Print event count — it should **not** reset to zero.

Same code moves to Postgres in stage by changing only `db_url`. That is the point of using the native service instead of writing your own store.

### Expect

Restart → same `session_id` → prior events still there.

> **Tip:** Put `*.db` and `.adk/` in `.gitignore` (your router/inventory packages already ignore session DBs). Do not commit Maya’s transcripts.

---

## Task 4 — Edge contract: `session_id` is part of the API

### Why

Two WISMO HTTP calls without a session id are two strangers. HITL resume needs a stable id.

### Do this

Open `project/meridian_ops/deploy/app.py`. Note `WismoRequest.session_id`.

In `29-session-store.md`, specify the contract:

| Field | Who creates it | Where it is stored |
|-------|----------------|--------------------|
| `app_name` | you, constant | ADK |
| `user_id` | auth / device (lab: header) | ADK |
| `session_id` | client or edge on first turn | ADK + client |

Add (or document) headers for the lab:

- `X-Meridian-User` — stable user (never log raw email; hash if you have Lesson 27 redaction)  
- `X-Session-Id` — optional; if missing, edge creates a UUID and **returns** it

Write the rule: **clients must send the id back on the next turn.**

If you change `app.py`, keep using `Runner` + session service — do not stash chat history in a FastAPI `dict`.

### Expect

A client can round-trip `session_id`. The edge is a **pass-through**, not a second memory.

---

## Task 5 — Stickiness vs shared store (write the failure)

### Why

Ops will offer “sticky cookies” as a shortcut. You must know when that lies.

### Do this

Add this matrix to the decision file:

| Setup | HITL resume after 8 hours | Two instances, no shared DB | Session store down |
|-------|---------------------------|-----------------------------|--------------------|
| In-memory + sticky | | | |
| In-memory + no sticky | | | |
| Shared ADK session service | | | |
| Sticky **and** shared store | | | |

Fill each cell: **works / broken / degraded**.

Then one paragraph: what `/readyz` should do if the session backend ping fails (Lesson 32 already cares about this row).

### Expect

Only **shared ADK session service** gets a “works” for multi-instance HITL. Stickiness alone is **broken** for resume after scale-to-zero.

---

## Task 6 — Replay a session for an incident

### Why

Lesson 11 traces tell you spans. Session **events** tell you the conversation the model saw.

### Do this

After Task 3, print events for one `session_id`:

A `Session` carries `app_name`, `user_id`, `id`, `state`, `last_update_time`, and `events`. All three services take the same keyword arguments:

```python
session = await session_service.get_session(
    app_name="meridian_orderops",
    user_id="devon-handheld",
    session_id="the-id-you-used",
)
for event in session.events:
    print(event.author, event.partial, bool(event.content))
```

In `29-session-store.md`, paste **redacted** output (no emails, no tokens). Answer:

- Could you tell whether `get_order` ran?  
- Could you resume HITL from this blob, or do you still need ADK resume APIs?

### Expect

Replay is **read events**, not re-implementing the agent loop.

---

## How it works (deeper dive)

**Why `app_name` matters**

Session keys are typically `(app_name, user_id, session_id)`.  
Reuse `app_name="meridian_orderops"` in prod and `"meridian_orderops_eval"` in eval so goldens do not collide with live HITL pauses.

**Redis / Memorystore**

In Google Cloud, **Memorystore** is managed Redis. You use it when:

- ADK (or your session adapter **documented by ADK**) speaks Redis, or  
- The **edge** needs shared **idempotency** keys (Lesson 04) — that is **not** a replacement for ADK sessions  

Do not store ADK events in a homemade Redis list if ADK already has a session service.

**Scale-to-zero**

Cloud Run can drop every instance. Sticky sessions die. Shared session storage + `RequestInput` resume is the HITL story.

---

## Common pitfalls / troubleshooting

| Symptom | Fix |
|---------|-----|
| Import error for `DatabaseSessionService` | Upgrade: `pip install -U "google-adk>=2.6.3"` |
| SQLite `database is locked` | One writer; don’t copy the db into two containers without NFS/Postgres |
| Two users share a session | Distinct `user_id`; never key only on `session_id` globally |
| HITL lost overnight | Session backend not wired to `Runner`; still on `InMemoryRunner` |
| PII in session dumps | Lesson 27 redaction before you paste into tickets |

---

## You are done when

- [ ] Restart proof for in-memory  
- [ ] All three native session services import, production target chosen  
- [ ] `DatabaseSessionService` survives a restart with the same `session_id`  
- [ ] Edge `session_id` contract written  
- [ ] Stickiness matrix filled  
- [ ] One redacted event replay  

---

## Knowledge check

1. Why does `InMemorySessionService` fail with two replicas?  
2. What three ids usually key a session?  
3. Why is load-balancer stickiness not enough for HITL tomorrow?  
4. What is replay in this lesson?  
5. Why is a DIY checkpoint table forbidden?

### Answers

1. Each process has its **own RAM**; the other replica has empty memory.  
2. **`app_name`**, **`user_id`**, **`session_id`**.  
3. Instances **go away**; stickiness cannot find a machine that no longer exists.  
4. Reading **session events** to see what the run did.  
5. ADK already owns pause/resume; a second store **splits** the source of truth.

---

## Recap

- Sessions are a **platform** resource, not a chat widget.  
- Shared ADK session service first; stickiness optional.  
- Next: many **tenants** sharing that platform without sharing privileges.

---

## Stretch goal

Add a `/readyz` check that opens the session backend (SQLite ping or `SELECT 1`). Fail ready when the store is down so the load balancer stops sending HITL traffic.

---

## Feedback

- Could you explain to on-call why a second Cloud Run instance “forgot” Devon’s order id?  
- Note task number + expected vs actual import names.

---

## Navigate

**← Prev** [Lesson 28 — Architecture catalog](28-architecture-catalog.md)  
**Next →** [Lesson 30 — Multi-tenant platforms](30-multi-tenant.md)  
**Track home:** [README](../README.md)
