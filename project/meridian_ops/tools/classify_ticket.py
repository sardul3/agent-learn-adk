from __future__ import annotations

from enum import Enum
import re

class Route(str, Enum):
    SCRIPT = "script"
    WORKFLOW = "workflow"
    RAG = "rag"
    SINGLE_AGENT = "single_agent"
    MULTI_AGENT = "multi_agent"

_REFUND = re.compile(r"\brefund\b|\bcharged\b|\bmelted\b", re.I)
_INVENTORY = re.compile(r"\bATP\b|\bSKU\b|\bsubstitute\b|\bshorted\b", re.I)
_POLICY = re.compile(r"\bpolicy\b|\bcredit policy\b", re.I)
_BATCH = re.compile(r"\brecompute\b|\bnightly\b|\bsegment\b", re.I)
_SCHEDULE = re.compile(r"\bchange my pickup\b|\breschedule\b", re.I)

def classify_ticket(text: str, channel: str | None = None) -> Route:
    """Classify a Meridian ticket into an execution pattern.

    This is deliberately deterministic. In the future, we will replace or wrap it
    with an LLM router — but the labels stay the same.
    """
    if channel == "internal_batch" or _BATCH.search(text):
        return Route.SCRIPT
    if _REFUND.search(text):
        # Refunds need policy + possible human approval → workflow with agent nodes
        return Route.WORKFLOW
    if _INVENTORY.search(text):
        return Route.MULTI_AGENT
    if _POLICY.search(text) and not _REFUND.search(text):
        return Route.RAG
    if _SCHEDULE.search(text):
        return Route.WORKFLOW

    return Route.SINGLE_AGENT