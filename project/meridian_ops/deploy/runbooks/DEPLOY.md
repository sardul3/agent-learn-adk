# Runbook — Deploy Meridian OrderOps

## Preconditions (SHIP gate)

- [ ] MLflow eval card says **SHIP** for this `git_sha` / `instruction_sha`
- [ ] `AgentEvaluator` trajectory gates green on WISMO critical set
- [ ] Image built and scanned (no critical CVEs in policy)
- [ ] Secrets present in target env (API key, `GOOGLE_API_KEY`)
- [ ] Change window OK (no freeze)

## Steps

1. Tag release: `meridian-orderops:X.Y.Z` and `git_sha`
2. Write/update `release_manifest.json` (image, sha, prompt version, mlflow run id)
3. Deploy to **stage** first
4. Run `smoke.sh` against stage base URL
5. Watch error rate + p95 for 15–30 minutes
6. Promote to **prod** (canary 10% → 50% → 100% — Lesson 41)
7. Paste smoke output + revision id in the release PR

## Abort

If smoke fails or error rate doubles vs baseline → execute [ROLLBACK.md](ROLLBACK.md).