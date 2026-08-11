# Lesson 41 — CI/CD, canary, rollback drills & on-call

**Level:** Advanced (SRE / release engineering)  
**Time:** ~150–180 minutes  
**Prerequisites:** Lesson 12 (image + smoke + runbooks); Lessons 08–10 (eval gates, MLflow)  
**Lab outcome:** A Meridian **release train**: CI gates → stage deploy → canary → prod, plus a practiced rollback and an on-call cheat sheet

**Standard:** [docs/NATIVE-ADK.md](../docs/NATIVE-ADK.md)

---

## At a glance

Lesson 12 ships a container. This lesson operates the **factory**:

```
PR → unit tools → docker build → (nightly AgentEvaluator)
        │
        ▼
   stage deploy → smoke → soak
        │
        ▼
   canary 10% → 50% → 100%
        │
        ├─ metrics OK → done
        └─ burn SLO → automatic/manual rollback
```

Everything still invokes **ADK Runner** behind the edge.

---

## Why this matters

Friday 4:58pm push. Prompt “tweak” merges. Saturday: POD lies spike.

Without a release train you argue in Slack.  
With one you: fail CI on trajectory, canary at 10%, auto-rollback, page the right human, attach the MLflow run.

That is deployment **ops**, not “we have a Dockerfile.”

---

## Know these

| Term | Meaning | Meridian example |
|------|---------|------------------|
| **CI** | Automated checks on every change | pytest tools + docker build |
| **CD** | Automated delivery to environments | Stage then prod |
| **Environment promotion** | Same image, new config/secrets | `0.1.0` → stage → prod |
| **Canary** | Small % traffic on new revision | 10% of WISMO |
| **Blue/green** | Two full stacks; flip traffic | Optional alternative to canary |
| **Soak** | Watch for a quiet period post-deploy | 30 minutes error/p95 |
| **Rollback drill** | Practice restore before disaster | Monthly game day |
| **Error budget** | Allowed unreliability from SLO | Page when burned |
| **Synthetic check** | Scripted probe from outside | `smoke.sh` from CI runner |
| **Change freeze** | No deploys window | Peak holiday grocery week |
| **Runbook** | Step-by-step incident/deploy guide | `deploy/runbooks/*.md` |

---

## Task 1 — Walk the existing CI workflow

### Why

You already have a starter GitHub Actions file — learn it before extending.

### Do this

Open `.github/workflows/meridian-orderops-ci.yml`.

Answer in `project/meridian_ops/decisions/41-release-train.md`:

1. What runs on every PR?  
2. What does **not** run on every PR (and why)?  
3. Where would you add `AgentEvaluator` (PR vs nightly)?

### Expect

You state: tools on PR; live Evaluator nightly/labeled — matches Lesson 08 layering.

---

## Task 2 — Add a smoke job definition (CI-as-code)

### Why

Images that do not boot must never be tagged `prod`.

### Do this

Extend the workflow (or add `meridian-orderops-smoke.yml`) with a job that:

1. Builds the image  
2. Runs the container with a dummy/dev key  
3. Executes `smoke.sh` against `localhost:8080`  

Sketch (adapt to Actions networking):

```yaml
  smoke:
    runs-on: ubuntu-latest
    needs: docker-build
    steps:
      - uses: actions/checkout@v4
      - name: Run container
        run: |
          docker build -f project/meridian_ops/deploy/Dockerfile -t meridian-orderops:smoke .
          docker run -d --name orderops -p 8080:8080 \
            -e MERIDIAN_API_KEY=dev-local-key-change-me \
            -e MERIDIAN_ENV=ci \
            -e GOOGLE_API_KEY=${{ secrets.GOOGLE_API_KEY }} \
            meridian-orderops:smoke
          sleep 5
          chmod +x project/meridian_ops/deploy/smoke.sh
          MERIDIAN_API_KEY=dev-local-key-change-me ./project/meridian_ops/deploy/smoke.sh
          docker logs orderops
          docker rm -f orderops
```

> **Tip:** If you lack a GitHub `GOOGLE_API_KEY` secret, gate the live smoke behind `if: ${{ secrets.GOOGLE_API_KEY != '' }}` and keep docker-build always on.

### Expect

Workflow file updated; decisions note whether smoke is blocking or optional without secrets.

---

## Task 3 — Environment promotion map

### Why

“Works in compose” ≠ prod. Same **image digest**, different config.

### Do this

Fill this table in `41-release-train.md`:

| Env | URL pattern | `MERIDIAN_ENV` | Secrets source | Who can deploy | Auto? |
|-----|-------------|----------------|----------------|----------------|-------|
| local | localhost:8080 | local | `.env` | anyone | n/a |
| compose | localhost:8080 | compose | `.env` | anyone | n/a |
| stage | … | stage | Secret Manager | CI + on-call | yes on main |
| prod | … | prod | Secret Manager | CI after approval | canary |

Add a hard rule: **never rebuild for prod** — promote the stage-tested digest.

### Expect

Promotion = retag/traffic shift, not “build again on the prod laptop.”

---

## Task 4 — Canary plan for Cloud Run (or lab simulation)

### Why

100% blast radius is how grocery apps ruin weekends.

### Do this

Write `project/meridian_ops/deploy/CANARY.md`:

**Traffic steps**

1. Deploy new revision with `--no-traffic`  
2. Route **10%** → soak 20 minutes  
3. **50%** → soak 20 minutes  
4. **100%**  

**Abort conditions** (any one):

- Error rate > 2× baseline  
- Groundedness/synthetic fail  
- p95 latency > SLO (Lesson 11)  
- Manual on-call abort  

**Cloud Run commands** (fill REGION/SERVICE):

```bash
gcloud run deploy meridian-orderops --image IMAGE --region REGION --no-traffic
gcloud run services update-traffic meridian-orderops --region REGION \
  --to-revisions=NEW=10,OLD=90
# ... then 50/50, then NEW=100
```

**Lab simulation without GCP:** two compose tags `0.1.0` (stable) and `0.1.1` (canary). Document how you’d split traffic with an API gateway later; for today, run smoke against each and practice the abort decision table.

### Expect

Abort conditions are numeric, not vibes.

---

## Task 5 — Rollback drill (do it, don’t only read)

### Why

Unpracticed runbooks fail at 2am.

### Do this

1. Tag current image `meridian-orderops:good`  
2. Build a deliberate **bad** revision: e.g. temporarily set API to return 500 on `/v1/wismo` **or** point `MERIDIAN_API_KEY` wrong so smoke fails  
3. “Detect” via failed `smoke.sh`  
4. Execute [ROLLBACK.md](../project/meridian_ops/deploy/runbooks/ROLLBACK.md) — restore `good`  
5. Re-run smoke → `SMOKE OK`  
6. Log time-to-restore in `41-release-train.md`

### Expect

Measured restore (minutes). Bad revision not left running.

> **Watch out:** Prefer rollback over forward-fix during SEV unless the fix is already validated.

---

## Task 6 — On-call cheat sheet

### Why

Pager text must be short.

### Do this

Create `project/meridian_ops/deploy/runbooks/ONCALL_CHEATSHEET.md`:

```markdown
# OrderOps on-call (one screen)

## Links
- Stage URL:
- Prod URL:
- MLflow experiment: meridian_orderops_evals
- Dashboard: (latency, errors, $)

## First 5 minutes
1. Open /readyz and /metrics on prod
2. Run smoke.sh against prod (read-only WISMO)
3. Check last deploy: image_tag + git_sha from /v1/wismo or Cloud Run
4. If burn → ROLLBACK.md
5. Capture correlation_id from a bad response

## Pages
- Error rate > 5% for 10m
- Smoke synthetic fail 2 intervals
- Cost/task > budget for 1h (warn)
```

Fill blank links with your real or `TBD` values.

### Expect

Cheatsheet ≤ one page; rollback is step 4.

---

## Task 7 — Wire eval SHIP into “deploy allowed”

### Why

CD without quality gates ships trajectory regressions.

### Do this

Add a checklist job or doc gate in `41-release-train.md`:

**Deploy to prod allowed only if**

- [ ] MLflow eval card = SHIP for this `git_sha`  
- [ ] Critical `tool_trajectory_avg_score` met on WISMO set  
- [ ] Image digest matches stage smoke  
- [ ] Not in change freeze calendar  

Optional: script `assert_ship_gate.py` that reads `release_manifest.json` + a SHIP flag file from Lesson 10.

### Expect

A NO-SHIP eval blocks the mental model for prod even if CI is green on unit tests only.

---

## Task 8 — Change freeze & communication template

### Why

Retail peaks (holidays) need freezes.

### Do this

Add to decisions:

| Window | Policy |
|--------|--------|
| Black Friday week | prod freeze except SEV rollback |
| Normal | canary required |

Draft a release Slack/email template:

- service, image, git_sha, mlflow run, canary plan, rollback owner

### Expect

Template committed under `deploy/runbooks/RELEASE_ANNOUNCEMENT.md`.

---

## How it works (deeper dive)

### Why same image digest

Rebuilds are not bit-for-bit identical. Promote digests so stage proof applies to prod.

### Canary vs blue/green

| | Canary | Blue/green |
|--|--------|------------|
| Blast radius | Small % | Flip all at once |
| Cost | One service, two revisions | Often two stacks |
| Meridian default | Canary on Cloud Run traffic | Special cases |

### ADK-specific ops note

Prompt/agent JSON changes are **code**. They ship through the same train — never “just edit prod instruction in a bucket” without eval + canary.

---

## Common pitfalls / troubleshooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| CI green, prod bad | No smoke / no Evaluator gate | Add blocking smoke + SHIP gate |
| Canary forever at 10% | Forgot promotion | Checklist timer |
| Rollback to wrong rev | No manifest | Require manifest in announce |
| Secret missing in Actions | Not configured | Optional smoke; document |

---

## You are done when

- [ ] CI workflow understood + smoke job sketched/added  
- [ ] Env promotion table filled (same digest rule)  
- [ ] CANARY.md with numeric abort rules  
- [ ] Rollback drill completed with time-to-restore  
- [ ] ONCALL_CHEATSHEET.md exists  
- [ ] SHIP gate checklist written  
- [ ] Freeze + announcement template done  

---

## Knowledge check

1. What should you promote across envs — a new build, or a digest?  
2. Name two canary abort conditions.  
3. When do live `AgentEvaluator` jobs belong if not on every PR?  
4. What is the first on-call action when error rate burns after deploy?  
5. Why are prompt changes treated like code deploys?

### Answers

1. The **same image digest** tested in stage.  
2. e.g. error rate 2× baseline; synthetic smoke fail; p95 over SLO.  
3. Nightly or labeled PRs (cost/flake).  
4. Rollback, then investigate.  
5. They change production behavior and need eval + canary.

---

## Recap

- Meridian has a release train, not only a Dockerfile.  
- Next ops depth: [Lesson 32 — Chaos, DR & feature flags](32-chaos-dr-feature-flags.md).

---

## Stretch goal

Add a nightly Actions workflow that runs `AgentEvaluator` and publishes an MLflow run id into `release_manifest.json` as an artifact.

---

## Feedback

- Could you run the rollback drill again without opening ROLLBACK.md?  
- What tripped you up: Actions smoke, canary math, or SHIP gating?  
- Note task number + expected vs actual.

---

## Navigate

**← Deploy foundation** [Lesson 12](12-deployment-ops.md)  
**Related** [Lesson 32 — Chaos, DR & feature flags](32-chaos-dr-feature-flags.md)  
**Pack C continues** [Lesson 13](13-graph-workflows.md)  
**Track home:** [README](../README.md)