# Lesson 12 — Deployment & first-line ops

**Level:** Advanced  
**Time:** ~150–180 minutes  
**Prerequisites:** Pack A + Lessons 08–11; Docker available  
**Lab outcome:** Ship Meridian OrderOps as a container behind FastAPI → **ADK Runner**, with health probes, smoke tests, secrets hygiene, and a Cloud Run–class runbook

**Standard:** [docs/NATIVE-ADK.md](../docs/NATIVE-ADK.md)  
**Goes next:** [Lesson 41 — CI/CD, canary, rollback drills & on-call](41-cicd-sre-deployment-ops.md)

---

## At a glance

Lesson 12 answers: *“How do we run this in an environment that is not my laptop?”*

```
Developer laptop
      │ docker build / compose
      ▼
┌─────────────┐     secrets/env      ┌──────────────────┐
│ orderops-api│ ◄─────────────────── │ Secret Manager / │
│ FastAPI     │                      │ .env (local only)│
│  └─ ADK     │
│     Runner  │
└──────┬──────┘
       │ smoke.sh + /readyz
       ▼
  stage → (Lesson 41) → prod
```

You will **not** put `adk web` on the public internet.

---

## Why this matters

Maya’s WISMO traffic hits an internal URL owned by Meridian platform.

If you only ever demo in `adk web`:

- Security cannot review AuthZ  
- On-call cannot rollback a revision  
- Evals in MLflow do not map to a running `image_tag`

Priya’s night: a bad prompt ships Friday → Monday morning POD lies. Without deploy ops, you cannot roll back in minutes.

---

## Know these

| Term | Plain English | Meridian use |
|------|---------------|--------------|
| **Edge / façade** | HTTP API in front of the agent | FastAPI `/v1/wismo` |
| **Image** | Immutable runnable package | `meridian-orderops:0.1.0` |
| **Liveness (`/healthz`)** | Process alive | Restart if down |
| **Readiness (`/readyz`)** | Safe to take traffic | Dependencies OK |
| **Smoke test** | Tiny post-deploy check | `smoke.sh` |
| **Secret** | Credential not in git | `MERIDIAN_API_KEY`, `GOOGLE_API_KEY` |
| **Revision** | One deployed version | Cloud Run revision to rollback to |
| **Release manifest** | Record tying code↔eval↔image | `git_sha` + MLflow run |

---

## Task 1 — Confirm the native edge app

### Why

Deploy ops only matter if production calls ADK — not a stub.

### Do this

Read `project/meridian_ops/deploy/app.py`. Confirm it uses:

- `App` + `InMemoryRunner` (lab)  
- `root_agent` from `meridian_orderops` when available  

Run locally:

```bash
cd /Users/alishaghatane/dev/agent-learn-sme
source .venv/bin/activate
pip install -r project/meridian_ops/deploy/requirements.txt
pip install -U "google-adk>=2.0.0"
export PYTHONPATH=project
export MERIDIAN_API_KEY=dev-local-key-change-me
export GOOGLE_API_KEY=YOUR_KEY   # needed for live model turns
uvicorn meridian_ops.deploy.app:api --app-dir project --port 8080
```

In another terminal:

```bash
curl -fsS localhost:8080/healthz
curl -fsS localhost:8080/readyz
curl -fsS localhost:8080/v1/wismo \
  -H "Content-Type: application/json" \
  -H "X-Api-Key: dev-local-key-change-me" \
  -d '{"message":"Status for MC-1048292"}' | python -m json.tool
```

### Expect

- `engine` is `google-adk`  
- `final_text` non-empty  
- Missing/wrong API key → **401**

> **Watch out:** `InMemoryRunner` is for local/lab. Stage/prod needs a durable ADK session service (Lesson 29).

---

## Task 2 — Docker image (non-root, no baked secrets)

### Why

Images are what you promote. Secrets in layers are incidents.

### Do this

```bash
cd /Users/alishaghatane/dev/agent-learn-sme
docker build -f project/meridian_ops/deploy/Dockerfile -t meridian-orderops:0.1.0 .

docker run --rm -p 8080:8080 \
  -e MERIDIAN_API_KEY=dev-local-key-change-me \
  -e MERIDIAN_ENV=local-docker \
  -e MERIDIAN_GIT_SHA="$(git rev-parse --short HEAD 2>/dev/null || echo local)" \
  -e MERIDIAN_IMAGE_TAG=0.1.0 \
  -e GOOGLE_API_KEY="$GOOGLE_API_KEY" \
  meridian-orderops:0.1.0
```

Retest `/healthz` and `/v1/wismo`.

### Expect

Same JSON shape as Task 1; container runs as uid `10001` (non-root).

> **Tip:** Copy only what the edge needs. Do not `COPY` your home directory `.env` into the image.

---

## Task 3 — Compose + healthcheck

### Why

Compose is the shared “stage-like” story for the team.

### Do this

```bash
cd /Users/alishaghatane/dev/agent-learn-sme/project/meridian_ops/deploy
cp -n .env.example .env   # fill GOOGLE_API_KEY locally; never commit .env
docker compose up --build -d
docker compose ps
```

### Expect

Healthcheck passes; `docker compose ps` shows healthy.

---

## Task 4 — Smoke test script (gate before “we’re up”)

### Why

Humans forget curls under pressure. Automate the proof.

### Do this

```bash
chmod +x /Users/alishaghatane/dev/agent-learn-sme/project/meridian_ops/deploy/smoke.sh
export MERIDIAN_API_KEY=dev-local-key-change-me
./project/meridian_ops/deploy/smoke.sh http://127.0.0.1:8080
```

### Expect

```
SMOKE OK corr-... latency_ms= ...
```

If smoke fails, **do not** proceed to Cloud Run / “share the URL.”

---

## Task 5 — Config & secrets matrix

### Why

Wrong secret wiring is the top deploy failure after “forgot to build.”

### Do this

Create `project/meridian_ops/deploy/CONFIG_MATRIX.md`:

| Config | Local | Compose | Cloud Run | Source |
|--------|-------|---------|-----------|--------|
| `MERIDIAN_API_KEY` | env | `.env` (gitignored) | Secret Manager → env | Secret Manager |
| `GOOGLE_API_KEY` | env | `.env` | Secret Manager | Secret Manager |
| `MERIDIAN_ENV` | `local` | `compose` | `stage`/`prod` | Deploy pipeline |
| `MERIDIAN_GIT_SHA` | `git rev-parse` | CI inject | CI inject | CI |
| `MERIDIAN_IMAGE_TAG` | `0.1.0` | compose | revision tag | CI |

Confirm `.env` / `.env.example` pattern: example committed, real secrets not.

### Expect

A reviewer can see where every secret comes from.

---

## Task 6 — AuthZ note for the edge

### Why

API keys are a lab start; scopes prevent refund routes on WISMO keys later.

### Do this

Write `project/meridian_ops/deploy/AUTHZ.md`:

| Caller | AuthN | Scope |
|--------|-------|-------|
| CX toolkit | API key or OIDC (prod) | `orderops:wismo:read` |
| Store-ops batch | service account | `orderops:wismo:read` |
| Public internet | **denied** | — |

Lab: keep key check; document OIDC upgrade path (no need to implement IdP here).

### Expect

“No unauthenticated Cloud Run” is written as a hard rule.

---

## Task 7 — Cloud Run deploy runbook (live or dry-run)

### Why

SMEs ship a runnable runbook even when credentials are missing today.

### Do this

Open and complete placeholders in a new file  
`project/meridian_ops/deploy/CLOUD_RUN.md` using this skeleton:

```bash
gcloud config set project YOUR_PROJECT
gcloud auth configure-docker

docker tag meridian-orderops:0.1.0 \
  REGION-docker.pkg.dev/YOUR_PROJECT/meridian/orderops:0.1.0
docker push REGION-docker.pkg.dev/YOUR_PROJECT/meridian/orderops:0.1.0

# secrets (once)
# echo -n '...' | gcloud secrets create meridian-api-key --data-file=-

gcloud run deploy meridian-orderops \
  --image REGION-docker.pkg.dev/YOUR_PROJECT/meridian/orderops:0.1.0 \
  --region REGION \
  --no-allow-unauthenticated \
  --set-secrets=MERIDIAN_API_KEY=meridian-api-key:latest,GOOGLE_API_KEY=google-api-key:latest \
  --set-env-vars=MERIDIAN_ENV=stage,MERIDIAN_IMAGE_TAG=0.1.0,MERIDIAN_GIT_SHA=SHA \
  --cpu=1 --memory=512Mi --concurrency=40 --min-instances=0 --max-instances=10
```

If you lack GCP: append `DRY_RUN=$(date -u +%F)` and still fill REGION/PROJECT names you *would* use.

Compare runtimes in the same doc:

| Runtime | When |
|---------|------|
| Cloud Run | Request/response OrderOps API |
| GKE | Complex networking / sidecars |
| Managed Agent Runtime | ADK-native hosting when org standardizes on it |

### Expect

Teammate could execute or dry-run without Slack archaeology.

---

## Task 8 — Release manifest ↔ MLflow SHIP

### Why

Rollback needs a pointer: image ↔ git ↔ prompt ↔ eval.

### Do this

```bash
cd /Users/alishaghatane/dev/agent-learn-sme
GIT_SHA=$(git rev-parse --short HEAD 2>/dev/null || echo unknown)
cat > project/meridian_ops/deploy/release_manifest.json <<EOF
{
  "service": "meridian-orderops",
  "image_tag": "0.1.0",
  "git_sha": "${GIT_SHA}",
  "prompt_registry": {"order_status": "v2"},
  "mlflow_experiment": "meridian_orderops_evals",
  "mlflow_run_id": "REPLACE_AFTER_SHIP_EVAL",
  "eval_card": "evals/reports/EVAL_CARD.md",
  "smoke": "deploy/smoke.sh"
}
EOF
```

Fill `mlflow_run_id` from a Lesson 10 SHIP run (or `PENDING` if not run yet).

### Expect

Manifest exists and matches the image you built.

---

## Task 9 — First-line ops: metrics + runbooks on disk

### Why

Deploy without ops docs is a trap for future-you.

### Do this

1. Hit `curl -fsS localhost:8080/metrics` — see counters.  
2. Read `project/meridian_ops/deploy/runbooks/DEPLOY.md` and `ROLLBACK.md`.  
3. In `project/meridian_ops/decisions/12-ops-ready.md`, answer:

- Who is on-call for OrderOps?  
- What smoke proves “good”?  
- What is the first rollback command?

### Expect

You can execute mental rollback without opening Lesson 41 yet.

---

## How it works (deeper dive)

### Probe split

| Probe | Fails when | Orchestrator action |
|-------|------------|---------------------|
| Liveness | Process deadlocked/crash | Restart container |
| Readiness | Deps/session config bad | Stop sending traffic |

### Cost controls at the edge

- Default Flash / configured model via env  
- Concurrency caps on Cloud Run  
- Kill switches inside agents (Lesson 07) still apply per turn  

### What Lesson 41 adds

CI/CD, env promotion, canary %, automated rollback drills, pager expectations — the **release train**.

---

## Common pitfalls / troubleshooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| 401 loops | Key mismatch | Align `MERIDIAN_API_KEY` in shell and server |
| Import errors in image | Missing COPY / PYTHONPATH | Match Dockerfile layout; build from repo root |
| Smoke fails empty `final_text` | Missing `GOOGLE_API_KEY` or agent error | Check container logs; confirm key |
| Healthy but useless | Skipped smoke | Make smoke blocking in Lesson 41 CI |
| Secrets in git | Committed `.env` | Rotate keys; fix gitignore |

---

## You are done when

- [ ] Local uvicorn + Docker + compose all serve `/v1/wismo` via ADK  
- [ ] `smoke.sh` prints `SMOKE OK`  
- [ ] CONFIG_MATRIX + AUTHZ + CLOUD_RUN docs exist  
- [ ] `release_manifest.json` written  
- [ ] DEPLOY + ROLLBACK runbooks read  
- [ ] Decisions note answers on-call / smoke / rollback  

---

## Knowledge check

1. Why is `/readyz` separate from `/healthz`?  
2. What must never be baked into the image?  
3. What four fields should a release manifest tie together?  
4. What is the first move if prod WISMO error rate spikes after deploy?  
5. Why keep ADK behind FastAPI instead of exposing `adk web`?

### Answers

1. Alive ≠ safe for traffic (deps/config).  
2. API keys and other secrets.  
3. Image tag, git sha, prompt version, MLflow/eval evidence.  
4. Rollback to previous revision, then investigate.  
5. AuthZ, stable contract, probes, metrics, multi-instance ops.

---

## Recap

- Meridian OrderOps is shippable as a container with smoke + secrets + runbooks.  
- Engine remains native ADK.  
- **Next for ops depth:** Lesson 41 (CI/CD, canary, rollback drills) and Lesson 32 (chaos/DR/flags).

---

## Stretch goal

Add `/v1/version` returning `git_sha`, `image_tag`, `env` only (no secrets) for on-call paste.

---

## Feedback

- Could you rollback compose to `0.1.0` from memory using the runbook?  
- What tripped you up: Docker context, secrets, smoke, or Cloud Run dry-run?  
- Note task number + expected vs actual.

---

## Navigate

**← Prev** [Lesson 11 — Tracing & observability](11-tracing-observability.md)  
**Next (curriculum Pack C) →** [Lesson 13 — Graph workflows](13-graph-workflows.md)  
**Next (ops deep) →** [Lesson 41 — CI/CD & SRE release ops](41-cicd-sre-deployment-ops.md)