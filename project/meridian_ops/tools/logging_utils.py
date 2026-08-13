import json
import sys
import time
from typing import Any
import uuid


def new_correlation_id() -> str:
    return f"corr-{uuid.uuid4().hex[:12]}"


def log_tool_event(
    *,
    tool: str,
    correlation_id: str,
    level: str = "INFO",
    **fields: Any,
) -> None:
    record = {
        "ts": time.time(),
        "level": level,
        "tool": tool,
        "correlation_id": correlation_id,
        **fields,
    }

    print(
        json.dumps(record, indent=2),
        file=sys.stderr,
        flush=True,
    )
