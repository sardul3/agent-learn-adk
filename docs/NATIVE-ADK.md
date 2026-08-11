# Native ADK Rule (Meridian curriculum)

**Do not reinvent ADK.** Meridian domain code is allowed; alternate agent frameworks are not.

## Use ADK for

| Need | Native ADK |
|------|------------|
| Agent / LLM node | `LlmAgent` / `Agent` |
| Graph / routes / fan-in | `Workflow`, `JoinNode`, `Event(route=...)` |
| Sequential / parallel / loop (1.x) | `SequentialAgent`, `ParallelAgent`, `LoopAgent` — prefer `Workflow` on ADK 2+ |
| Invoke in tests/services | `App` + `Runner` / `InMemoryRunner` |
| Sessions | `InMemorySessionService` or configured session service — not a home-grown store for chat state |
| Eval / trajectories | `AgentEvaluator` + `*.test.json` / evalsets |
| MCP tools | `McpToolset` + `StdioConnectionParams` / SSE params |
| A2A | `RemoteA2aAgent`, `to_a2a(...)`, agent cards |
| HITL in graphs | `RequestInput` (+ app resumability) |
| Tool confirmation | ADK tool-confirmation / `RequireConfirmation` patterns |
| Dev UI | `adk web` / `adk run` |
| Events from tools/agents | ADK `Event` stream from `runner.run_async` |

## Allowed Meridian-only code (not “reimplementing ADK”)

- OMS / ATP / payments / policy **domain tools** and fixtures  
- FastAPI **edge** for AuthN/Z, webhooks, HMAC (product API; still calls ADK `Runner`)  
- MLflow **experiment logging** (third-party tracker)  
- Domain **rubrics** that score ADK trajectories/responses  
- Config YAML (role → MCP `tool_filter` lists)

## Forbidden patterns in this repo’s lessons

- Custom graph engines (`MeridianGraph`, DIY edge runners)  
- DIY agent loops / “stub planners” that replace `LlmAgent` + `AgentEvaluator`  
- DIY MCP buses that replace `McpToolset`  
- DIY A2A doubles that replace `RemoteA2aAgent` / `to_a2a`  
- DIY checkpoint stores that replace ADK session + `RequestInput` resume  
- DIY span trees when ADK events / OTel / MLflow tracing cover the need  

## Version note

Labs target **ADK 2.x `Workflow`**. If an import fails, upgrade:

```bash
pip install -U "google-adk>=2.0.0"
```

Template agents remain literacy for older codebases — not the default for new Meridian work.

## Verify before merging a lesson change

```bash
# Prefer inspecting your install over inventing APIs
python -c "from google.adk.workflow import Workflow, JoinNode; print('workflow OK')"
python -c "from google.adk.tools.mcp_tool import McpToolset; print('mcp OK')"
python -c "from google.adk.evaluation.agent_evaluator import AgentEvaluator; print('eval OK')"
```