# Runbook — Rollback Meridian OrderOps

**Severity:** SEV-2 if WISMO error rate > 5% or groundedness pages  
**Owner:** Customer Operations Platform on-call

## Symptoms

- Spike in `meridian_wismo_errors_total`
- Customers get invented POD / wrong lifecycle
- `/readyz` failing after a release

## Immediate actions (first 15 minutes)

1. Declare incident channel; paste `git_sha` / `image_tag` from a failing `/v1/wismo` response (or Cloud Run revision).
2. **Rollback traffic** to previous healthy revision (do not “hot-fix prompts” during SEV).

### Cloud Run

```bash
# List revisions
gcloud run revisions list --service=meridian-orderops --region=REGION

# Send 100% traffic to last known good
gcloud run services update-traffic meridian-orderops \
  --region=REGION \
  --to-revisions=PREVIOUS_REVISION=100
```

### Local compose / lab

```bash
export MERIDIAN_IMAGE_TAG=0.1.0   # last good tag
docker compose -f project/meridian_ops/deploy/docker-compose.yml up -d --build
./project/meridian_ops/deploy/smoke.sh
```

3. Run smoke against the rolled-back URL — expect `SMOKE OK`.
4. Freeze further deploys until root cause + golden eval added.

## After stabilize

- Capture failing ADK trajectory (Lesson 11)
- Add/adjust `AgentEvaluator` golden (Lesson 08)
- Log NO-SHIP on the bad `instruction_sha` in MLflow (Lesson 10)
- Postmortem within 48h