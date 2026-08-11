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