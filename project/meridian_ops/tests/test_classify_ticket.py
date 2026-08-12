import json
from pathlib import Path

from meridian_ops.tools.classify_ticket import Route, classify_ticket

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "tickets.json"

def test_batch_ticket_is_script():
    tickets = json.loads(FIXTURES.read_text())
    batch = next(t for t in tickets if t["ticket_id"] == "TCK-9005")
    assert classify_ticket(batch["text"], batch["channel"]) == Route.SCRIPT

def test_refund_ticket_is_workflow():
    tickets = json.loads(FIXTURES.read_text())
    refund = next(t for t in tickets if t["ticket_id"] == "TCK-9004")
    assert classify_ticket(refund["text"], refund["channel"]) == Route.WORKFLOW


def test_inventory_short_is_multi_agent():
    tickets = json.loads(FIXTURES.read_text())
    inv = next(t for t in tickets if t["ticket_id"] == "TCK-9003")
    assert classify_ticket(inv["text"], inv["channel"]) == Route.MULTI_AGENT


def test_policy_question_is_rag():
    tickets = json.loads(FIXTURES.read_text())
    pol = next(t for t in tickets if t["ticket_id"] == "TCK-9006")
    assert classify_ticket(pol["text"], pol["channel"]) == Route.RAG