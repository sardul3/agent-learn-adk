from meridian_ops.tools.payments import request_refund


def test_preview_does_not_persist():
    out = request_refund("MC-1048277", 214.55, "DAMAGED_ITEM", "k1", confirm=False)
    assert out["preview"] is True
    assert out["requires_hitl"] is True


def test_confirm_is_idempotent():
    a = request_refund("MC-1048277", 214.55, "DAMAGED_ITEM", "maya-214", confirm=True)
    b = request_refund("MC-1048277", 214.55, "DAMAGED_ITEM", "maya-214", confirm=True)
    assert a["refund_request_id"] == b["refund_request_id"]
    assert b.get("replayed") is True


def test_missing_key_fails_loud():
    out = request_refund("MC-1048277", 10.0, "DAMAGED_ITEM", "", confirm=True)
    assert out["error_code"] == "MISSING_IDEMPOTENCY_KEY"