from meridian_ops.tools.policy_rag import retrieve_policy


def test_late_delivery_query_hits_delivery_policy():
    out = retrieve_policy("late grocery delivery credits")
    assert out["status"] == "success"
    paths = [d["path"] for d in out["documents"]]
    assert "late_delivery_credits.md" in paths


def test_melted_items_hits_refund_policy():
    out = retrieve_policy("melted dairy full refund")
    paths = [d["path"] for d in out["documents"]]
    assert "refunds_damaged_items.md" in paths