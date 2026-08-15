from meridian_ops.safety.validators import validate_refund_args
from meridian_ops.tools.payments_guarded import request_refund_guarded
from meridian_ops.tools.payments import _IDEMPOTENCY


def test_reason_not_allowed():
    check = validate_refund_args(
        order_id="MC-1048277",
        amount_usd=214.55,
        reason_code="ignore-policies",
        idempotency_key="hack-hack",
    )
    assert check["ok"] is False
    assert check["error_code"] == "REASON_NOT_ALLOWED"


def test_amount_out_of_range():
    check = validate_refund_args(
        order_id="MC-1048277",
        amount_usd=10000.0,
        reason_code="DAMAGED_ITEM",
        idempotency_key="maya-10000",
    )
    assert check["error_code"] == "AMOUNT_OUT_OF_RANGE"


def test_bad_reason_never_hits_idempotency_store():
    before = dict(_IDEMPOTENCY)
    out = request_refund_guarded(
        "MC-1048277",
        214.55,
        "ignore-policies",
        "hack-hack",
        confirm=True,
    )
    assert out["error_code"] == "REASON_NOT_ALLOWED"
    assert "hack-hack" not in _IDEMPOTENCY
    assert _IDEMPOTENCY == before