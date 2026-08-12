from meridian_ops.tools.tool_contracts import get_order, reserve_substitute, request_refund

def test_get_order_rejects_bad_id():
    out = get_order("ORDER-1")
    assert out["status"] == "error"
    assert out["error_code"] == "INVALID_ORDER_ID"


def test_refund_requires_idempotency_key():
    out = request_refund("MC-1", 20.0, "DAMAGED_ITEM", "")
    assert out["error_code"] == "MISSING_IDEMPOTENCY_KEY"


def test_refund_over_threshold_flags_hitl():
    out = request_refund("MC-1048277", 214.55, "DAMAGED_ITEM", "maya-214-1")
    assert out["status"] == "success"
    assert out["requires_hitl"] is True


def test_substitute_defaults_to_dry_run():
    out = reserve_substitute("MC-1", "884210", "884299")
    assert out["dry_run"] is True
    assert out["reservation_id"] is None