from __future__ import annotations

import argparse
import json

from meridian_ops.safety.refund_gate import HitlDecision, run_refund_pipeline


def main() -> None:
    p = argparse.ArgumentParser(description="Meridian lab HITL refund gate")
    p.add_argument("--order-id", required=True, help="Meridian order id, e.g. MC-1048277")
    p.add_argument("--amount", type=float, required=True, help="Refund amount in USD")
    p.add_argument("--reason", required=True, help="Allowlisted reason code")
    p.add_argument("--key", required=True, help="Idempotency key (caller-chosen, >= 6 chars)")
    p.add_argument("--actor", default="priya", help="Who clicked; default priya")
    p.add_argument("--approve", action="store_true", help="Priya approves; do not also pass --deny")
    p.add_argument("--deny", action="store_true", help="Priya denies; do not also pass --approve")
    p.add_argument("--note", default="", help="Evidence note, e.g. photo verified")
    args = p.parse_args()

    if args.approve == args.deny:
        raise SystemExit("Specify exactly one of --approve or --deny")

    hitl = HitlDecision(approved=args.approve, actor=args.actor, note=args.note)
    out = run_refund_pipeline(
        order_id=args.order_id,
        amount_usd=args.amount,
        reason_code=args.reason,
        idempotency_key=args.key,
        hitl=hitl,
    )
    print(json.dumps(out, indent=2, default=str))


if __name__ == "__main__":
    main()