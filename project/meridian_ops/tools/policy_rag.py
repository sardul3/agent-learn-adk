from __future__ import annotations

import re
from pathlib import Path
from typing import Any

_POLICY_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "policies"


def retrieve_policy(query: str, top_k: int = 2) -> dict[str, Any]:
    """Retrieve Meridian policy markdown files relevant to a query."""
    _POLICY_DIR.mkdir(parents=True, exist_ok=True)
    tokens = set(re.findall(r"[a-z0-9]+", query.lower()))
    scored: list[tuple[int, Path]] = []
    for path in sorted(_POLICY_DIR.glob("*.md")):
        text = path.read_text().lower()
        score = sum(1 for t in tokens if t in text)
        scored.append((score, path))
    scored.sort(key=lambda x: x[0], reverse=True)
    picked = [p for score, p in scored if score > 0][:top_k]
    if not picked:
        return {
            "status": "error",
            "error_code": "NO_POLICY_HIT",
            "message": "No policy documents matched; do not invent policy.",
        }
    return {
        "status": "success",
        "documents": [{"path": p.name, "text": p.read_text()} for p in picked],
    }