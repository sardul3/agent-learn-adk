# Release announcement template — Meridian OrderOps

**Service:** meridian-orderops  
**Environment:** stage / prod  
**Image:** `meridian-orderops:X.Y.Z` (digest: `sha256:…`)  
**Git SHA:**  
**Prompt / registry version:**  
**MLflow experiment / run:**  
**Canary plan:** 10% → 50% → 100% (abort rules in CANARY.md)  
**Rollback owner on-call:**  
**Smoke:** `./project/meridian_ops/deploy/smoke.sh <BASE>`  
**Notes / risk:**  

After soak: reply in-thread with “promoted to 100%” or “rolled back to REV”.