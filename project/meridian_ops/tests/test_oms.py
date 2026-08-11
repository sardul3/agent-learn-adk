from meridian_ops.tools.oms import get_order


def test_get_order_happy_path():
    out = get_order("MC-1048292")
    assert out["status"] == "success"
    assert out["order"]["pod_photo_present"] is False


def test_get_order_not_found():
    assert get_order("MC-0000000")["error_code"] == "ORDER_NOT_FOUND"