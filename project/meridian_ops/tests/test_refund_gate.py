from meridian_ops.safety.refund_gate import HitlDecision, run_refund_pipeline


def test_injectionish_reason_blocked():
    out = run_refund_pipeline(
        order_id="MC-1048277",
        amount_usd=214.55,
        reason_code="IGNORE_PREVIOUS_INSTRUCTIONS",
        idempotency_key="hack-hack",
        hitl=HitlDecision(True, "priya", "nope"),
    )
    assert out["stage"] == "preview"
    assert out["result"]["error_code"] == "REASON_NOT_ALLOWED"


def test_over_threshold_requires_hitl():
    out = run_refund_pipeline(
        order_id="MC-1048277",
        amount_usd=214.55,
        reason_code="DAMAGED_ITEM",
        idempotency_key="maya-214-safe",
        hitl=None,
    )
    assert out["stage"] == "hitl_required"
    assert out["hitl_status"] == "PENDING"


def test_supervisor_deny_does_not_confirm():
    out = run_refund_pipeline(
        order_id="MC-1048277",
        amount_usd=214.55,
        reason_code="DAMAGED_ITEM",
        idempotency_key="maya-214-denied",
        hitl=HitlDecision(False, "priya", "photo unclear"),
    )
    assert out["stage"] == "hitl_required"
    assert out["hitl_status"] == "DENIED"


def test_supervisor_approve_confirms_once():
    decision = HitlDecision(True, "priya", "melted dairy photo verified")
    out = run_refund_pipeline(
        order_id="MC-1048277",
        amount_usd=214.55,
        reason_code="DAMAGED_ITEM",
        idempotency_key="maya-214-safe2",
        hitl=decision,
    )
    assert out["stage"] == "confirmed"
    assert out["result"]["status"] == "success"