"""Meridian OrderOps API edge — invokes native ADK App + Runner."""

from __future__ import annotations

import os
import time
import uuid

from fastapi import Depends, FastAPI, Header, HTTPException
from google.adk.apps import App
from google.adk.runners import InMemoryRunner
from google.genai import types
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Prefer Workflow package when present; fall back documented in Lesson 12.
try:
    from meridian_orderops.agent import root_agent
except ImportError:  # pragma: no cover - lab fallback
    from google.adk.agents import LlmAgent
    from meridian_ops.tools.oms import get_order

    root_agent = LlmAgent(
        name="meridian_order_status_fallback",
        model=os.getenv("MERIDIAN_MODEL_NAME", "gemini-2.5-flash"),
        instruction="Use get_order before factual claims. Never invent POD.",
        tools=[get_order],
    )


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="MERIDIAN_", extra="ignore")

    api_key: str = "dev-local-key-change-me"
    env: str = "local"
    model_name: str = "gemini-2.5-flash"
    git_sha: str = "unknown"
    image_tag: str = "dev"


settings = Settings()

api = FastAPI(title="Meridian OrderOps API", version="0.1.0")
adk_app = App(name="meridian_orderops", root_agent=root_agent)
runner = InMemoryRunner(app=adk_app)

# Lab counters for /metrics (Prometheus text exposition).
_REQUESTS = 0
_ERRORS = 0


class WismoRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    session_id: str | None = None


def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    if not x_api_key or x_api_key != settings.api_key:
        raise HTTPException(status_code=401, detail="unauthorized")


@api.get("/healthz")
def healthz() -> dict[str, str]:
    """Liveness — process is up."""
    return {"status": "ok"}


@api.get("/readyz")
def readyz() -> dict[str, str]:
    """Readiness — safe to receive traffic (extend with session/deps checks in stage)."""
    return {"status": "ready", "env": settings.env, "git_sha": settings.git_sha}


@api.get("/metrics")
def metrics() -> str:
    return (
        "# HELP meridian_wismo_requests_total WISMO requests\n"
        "# TYPE meridian_wismo_requests_total counter\n"
        f"meridian_wismo_requests_total {_REQUESTS}\n"
        "# HELP meridian_wismo_errors_total WISMO errors\n"
        "# TYPE meridian_wismo_errors_total counter\n"
        f"meridian_wismo_errors_total {_ERRORS}\n"
    )


@api.post("/v1/wismo", dependencies=[Depends(require_api_key)])
async def wismo(
    body: WismoRequest,
    x_correlation_id: str | None = Header(default=None),
) -> dict:
    global _REQUESTS, _ERRORS
    _REQUESTS += 1
    t0 = time.time()
    correlation_id = x_correlation_id or f"corr-{uuid.uuid4().hex[:12]}"
    session = await runner.session_service.create_session(
        app_name="meridian_orderops", user_id="api"
    )
    session_id = body.session_id or session.id
    final_text = ""
    try:
        async for event in runner.run_async(
            user_id="api",
            session_id=session_id,
            new_message=types.Content(
                role="user",
                parts=[types.Part.from_text(text=body.message)],
            ),
        ):
            content = getattr(event, "content", None)
            if content and getattr(content, "parts", None):
                for part in content.parts:
                    if getattr(part, "text", None):
                        final_text = part.text
    except Exception as exc:  # noqa: BLE001
        _ERRORS += 1
        raise HTTPException(status_code=500, detail="agent_error") from exc

    return {
        "session_id": session_id,
        "correlation_id": correlation_id,
        "final_text": final_text,
        "engine": "google-adk",
        "env": settings.env,
        "git_sha": settings.git_sha,
        "image_tag": settings.image_tag,
        "latency_ms": round((time.time() - t0) * 1000, 2),
    }