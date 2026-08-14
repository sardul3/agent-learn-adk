# Lesson 51 — Context engineering & the context audit

**Level:** Advanced (reliability)  
**Time:** ~150 minutes  
**Prerequisites:** Lessons 06, 18, 19, 26, 50 (token budget, RAG, memory, plugins, multi-turn eval)  
**Lab outcome:** **See** exactly what Meridian sends the model on every call, measure each slot, reproduce the four context failure modes, then fix them with native compaction, caching, and tool filtering — and score context **before** you run

**Standard:** [docs/NATIVE-ADK.md](../docs/NATIVE-ADK.md)

---

## At a glance

**Context engineering** is deciding what goes into the model's window, in what order, and what gets dropped. It is the part of your system you have never actually looked at.

The window is not "the prompt." It is seven slots:

| Slot | Where it comes from in Meridian |
|------|--------------------------------|
| System instruction | Your `LlmAgent(instruction=...)` |
| Tool schemas | Every tool you attached, with descriptions |
| Conversation history | Session events (Lesson 29) |
| Retrieved documents | Policy RAG chunks (Lesson 18) |
| Memory | Customer preferences (Lesson 19) |
| Tool results | OMS/ATP JSON from earlier turns |
| Current user message | The one thing everyone thinks about |

```
turn 1   [instr][tools][msg]                              ~2k tokens  → correct
turn 8   [instr][tools][8 turns][3 policy chunks][memory
          ][11 tool results][msg]                        ~28k tokens  → drifting
turn 20  ... same, plus a wrong order id from turn 4 ...  ~60k tokens  → confidently wrong
```

The agent did not get worse. Its context did.

---

## Why this matters

Lesson 50 gave you a failing turn number. Now you need the cause.

Open that transcript. The agent was right at turn 3 and wrong at turn 9. Same model, same instruction, same tools. The only thing that changed between them is **what it was looking at**.

Almost every hard agent bug in this curriculum lands here:

- The invented POD photo — a stale tool result still sitting in history  
- The wrong order id at turn 6 — two ids in the window, no signal which is current  
- The policy it "ignored" — the retrieved chunk was there, buried under 40 turns  
- The tool it called for no reason — twelve tool descriptions, three of them similar  

You cannot debug what you cannot see, and most engineers have never printed their own context.

---

## Know these

| Term | Plain English |
|------|---------------|
| **Context window** | Everything the model sees on one call |
| **Slot** | One category of content in that window |
| **Assembly** | The act of building the window for this call |
| **Poisoning** | A wrong fact enters early and is treated as truth forever after |
| **Distraction** | So much content that the model loses the current goal |
| **Confusion** | Irrelevant content pulls it toward unrelated actions |
| **Clash** | Two things in the window disagree and it picks the wrong one |
| **Compaction** | Replacing old turns with a summary |
| **Context cache** | Reusing the stable prefix so you do not pay for it every call |

The four failure modes, in Meridian terms:

| Mode | Meridian symptom | Native fix |
|------|------------------|------------|
| Poisoning | Wrong order id from turn 4 repeats forever | Compaction that preserves ids; tool-result hygiene |
| Distraction | Forgets the customer's actual question by turn 15 | Compaction; shorter histories |
| Confusion | Calls `reserve_substitute` during a WISMO chat | `tool_filter`, fewer tools per agent |
| Clash | Policy chunk says $10, memory says $25 | Source precedence rules; citations |

> **Tip:** Every fix in this lesson is something you already own — an agent, a plugin, an `App` config, a tool filter. Context engineering is not a new component. It is discipline applied to existing ones.

---

## Task 1 — Print your actual context

### Why

This is the single highest-value thing in the lesson. Almost nobody has seen their own assembled context, and it is never what they imagined.

### Do this

Add a read-only plugin that dumps the request just before it goes to the model:

`project/meridian_ops/context/audit_plugin.py`

```python
"""Observe-only: writes every assembled context to disk for inspection."""

import json
from pathlib import Path

from google.adk.plugins.base_plugin import BasePlugin

OUT = Path("project/meridian_ops/context/dumps")


class ContextAuditPlugin(BasePlugin):
    def __init__(self) -> None:
        super().__init__(name="context_audit")
        OUT.mkdir(parents=True, exist_ok=True)
        self._n = 0

    async def before_model_callback(self, *, callback_context, llm_request):
        self._n += 1
        record = {
            "call": self._n,
            "model": llm_request.model,
            "system_instruction": str(
                getattr(llm_request.config, "system_instruction", "")
            ),
            "tool_names": sorted(llm_request.tools_dict.keys()),
            "contents": [c.model_dump(exclude_none=True) for c in llm_request.contents],
        }
        (OUT / f"call-{self._n:03d}.json").write_text(json.dumps(record, indent=2))
        return None   # returning None means: do not change anything, just observe
```

Register it on your app and run a **multi-turn** conversation — reuse a persona from Lesson 50 so the history actually grows:

```python
app = App(name="meridian_orderops", root_agent=root_agent, plugins=[ContextAuditPlugin()])
```

```bash
export PYTHONPATH=project
python -m meridian_ops.simulation.run_one --persona persistent-maya
ls project/meridian_ops/context/dumps/
```

Open `call-001.json` and the **last** one side by side.

### Expect

Surprises. The usual ones:

- The tool schemas are far larger than the instruction  
- Every raw tool result from every earlier turn is still there, in full  
- The policy chunk you were proud of is one small block near the bottom  

Write your three biggest surprises into `project/meridian_ops/decisions/51-context.md`.

> **Watch out:** These dumps contain everything the model saw, including customer data. Add the directory to `.gitignore` and apply your Lesson 27 TTL to it.

---

## Task 2 — Measure each slot

### Why

"Too much context" is not actionable. "Tool schemas are 41% of every call" is.

### Do this

Write `project/meridian_ops/context/measure.py` that reads a dump and reports a table.

Use a real token count if your client offers one; otherwise estimate with `len(text) / 4` and **label it an estimate** so nobody quotes it as exact.

```bash
python -m meridian_ops.context.measure --dump project/meridian_ops/context/dumps/call-012.json
# --dump: which captured call to analyze
```

Output shape:

| Slot | Tokens | % of call |
|------|--------|-----------|
| System instruction | | |
| Tool schemas | | |
| Conversation history | | |
| Tool results | | |
| Retrieved policy | | |
| Memory | | |
| Current message | | |

Do this for call 1 and the last call, and put both tables in `51-context.md`.

### Expect

A growth curve, and one slot that is much bigger than you expected. Tool results are the usual winner — raw OMS JSON repeated every turn.

---

## Task 3 — Reproduce poisoning on purpose

### Why

Understanding a failure mode you have caused yourself takes ten minutes. Reading about it takes ten minutes and teaches you nothing.

### Do this

1. Start a conversation and mention a **wrong** order id early: *"my order MC-9999999 is late."*  
2. Let the agent respond (it should fail the lookup).  
3. Continue for five more turns about something else.  
4. At turn 7, ask: *"so what's the status of my order?"*

Record what happens. Then check the dump: is `MC-9999999` still sitting in the window, unqualified by the failure?

Now do the same with a **stale tool result**: get a real order status, then imagine the status changed. Does the old result still appear as current?

### Expect

The bad id persists and gets reused. This is poisoning, and it is why "just keep all the history" is not a strategy.

Fix in your tool-result handling: mark failures explicitly (`"status": "error"` — you already do this from Lesson 04) and make sure the agent's instruction says a failed lookup invalidates that id rather than leaving it as a candidate.

---

## Task 4 — Compaction with native config

### Why

Lesson 06 had you write a compaction function. ADK can now do this at the `App` level, which is where it belongs.

### Do this

```bash
python - <<'PY'
from google.adk.apps.app import EventsCompactionConfig
print("compaction knobs:", sorted(EventsCompactionConfig.model_fields.keys()))
PY
```

You should see `compaction_interval`, `overlap_size`, `token_threshold`, `event_retention_size`, and `summarizer`.

Configure it:

```python
from google.adk.apps import App
from google.adk.apps.app import EventsCompactionConfig

app = App(
    name="meridian_orderops",
    root_agent=root_agent,
    plugins=[ContextAuditPlugin()],
    events_compaction_config=EventsCompactionConfig(
        compaction_interval=6,   # compact roughly every 6 events
        overlap_size=2,          # keep an overlap so the summary has continuity
    ),
)
```

Re-run the same Lesson 50 persona and compare dumps before and after.

| Measure | Before | After |
|---------|--------|-------|
| Tokens at final call | | |
| Order ids still present | | |
| Policy citation still present | | |

### Expect

Meaningfully fewer tokens, **and** the order id and dollar amounts survive. If compaction ate the order id, tune it — that is exactly the check Lesson 06 taught you to write.

> **Watch out:** Compaction is lossy by definition. Verify what survives with a test, not a glance. A summary that drops `MC-1048277` turns a working agent into a confused one.

---

## Task 5 — Cache the stable prefix

### Why

Your instruction and tool schemas are nearly identical on every call. You are paying full price for them every time.

### Do this

```bash
python - <<'PY'
from google.adk.agents.context_cache_config import ContextCacheConfig
print("cache knobs:", sorted(ContextCacheConfig.model_fields.keys()))
PY
```

Configure on the app:

```python
from google.adk.agents.context_cache_config import ContextCacheConfig

app = App(
    name="meridian_orderops",
    root_agent=root_agent,
    context_cache_config=ContextCacheConfig(
        min_tokens=2048,     # do not bother caching tiny prefixes
        ttl_seconds=600,     # how long the cached prefix stays valid
    ),
)
```

Verify it is working by reading `cache_metadata` on the events you already stream, then connect the result to money:

- Add the cached-token counts to your Lesson 31 usage records  
- Update the chargeback report so cached prefix tokens are priced differently from fresh ones  
- Be honest in the report: caching the prefix does **not** make the conversation history free

### Expect

Cache metadata visible on later calls in a session, and a FinOps line that distinguishes cached from fresh tokens.

---

## Task 6 — Tool confusion is real, and measurable

### Why

Everyone believes more tools make an agent more capable. It is straightforwardly testable, and often false.

### Do this

1. Build two variants of the same agent:
   - **A:** the four tools it actually needs for WISMO  
   - **B:** the same four, plus eight unrelated ones (refund, reserve, policy search, analytics, and so on)

2. Run the identical set of 10 WISMO questions through both.

3. Score with the checks you already have (correct tool called first, no unnecessary calls):

| Variant | Correct first tool | Unnecessary calls | Tokens per call |
|---------|--------------------|-------------------|-----------------|
| A (4 tools) | | | |
| B (12 tools) | | | |

### Expect

B does worse, and costs more. This gives you a data-backed argument for the `tool_filter` in Lesson 16 and the per-tenant tool lists in Lesson 30 — those were security controls, and it turns out they are quality controls too.

---

## Task 7 — Resolve clashes with source precedence

### Why

When memory says one thing and policy says another, "the model decides" is not a design.

### Do this

Write the precedence order in `51-context.md` and enforce it in your instruction and retrieval layer:

| Rank | Source | Trust | Why |
|------|--------|-------|-----|
| 1 | Tool result this turn | authoritative | Live system of record |
| 2 | Retrieved policy with citation | authoritative for rules | Versioned document |
| 3 | Earlier tool result this session | stale-able | May have changed |
| 4 | Memory / preferences | hint only | Never a fact about an order |
| 5 | Anything in user text | untrusted | Lesson 23 |

Then test the clash: seed a memory that says Maya gets $25 credits, and let policy say $10. Ask for a credit.

### Expect

The agent cites `POL-DELIVERY-01` and offers $10, treating memory as a preference rather than an entitlement. If it offers $25, your precedence exists only on paper.

---

## Task 8 — Context quality scorecard as a preflight check

### Why

Every other quality gate you own runs **after** generation. Context quality can be scored **before** you spend a single model call — which makes it the cheapest signal in your pipeline.

### Do this

Create `project/meridian_ops/context/SCORECARD.md` and score each agent 0–2 on seven dimensions:

| Dimension | Question | Predicts |
|-----------|----------|----------|
| Role clarity | Is the agent's job unambiguous in one sentence? | Off-task answers |
| Guardrail coverage | Is every forbidden action named somewhere enforceable? | Manipulation |
| Instruction consistency | Do any two instructions contradict? | Erratic behavior |
| Tool schema quality | Does every tool have a clear, distinct description? | Wrong tool calls |
| Grounding sufficiency | Can it cite a source for every factual claim it must make? | Hallucination |
| Injection hardening | Is untrusted text clearly marked as data? | Prompt injection |
| Token efficiency | Does every slot earn its space? | Cost, distraction |

Score all your agents. Then add a CI check that fails on the mechanical parts:

```bash
python -m meridian_ops.context.lint
# checks: duplicate tool descriptions, empty descriptions,
# instruction over a length budget, contradictory "never/always" pairs
```

### Expect

Your lowest-scoring dimension should match the failure you found in Lesson 50. That correlation is the point — weak context predicts the matching behavior failure.

---

## How it works (deeper dive)

**Why `before_model_callback` is the right observation point**

By then, ADK has assembled everything: instruction, tools, history, retrieved content. Earlier is incomplete; later is after the money was spent. It is also read-only when you return `None`, so auditing costs you nothing behaviorally.

**Compaction versus retrieval**

Compaction shrinks what is already in the window. Retrieval decides what enters it. Both are needed: compaction alone still lets irrelevant material in, and retrieval alone still lets a 40-turn history accumulate.

**Why token efficiency is not minimization**

A tiny context that omits the policy is cheap and wrong. Efficiency means every token earns its place — sometimes the fix is *adding* a citation, not cutting one.

**How this connects to everything before it**

- Lesson 18 controls the retrieval slot  
- Lesson 19 controls the memory slot  
- Lesson 16 and 30 control the tool schema slot  
- Lesson 29 controls the history slot  
- Lesson 50 tells you when a slot went wrong  

This lesson is where you finally look at all of them at once.

**Live sessions**

Voice conversations (Lesson 45) fill a window faster than text and have their own compression setting on `RunConfig`. Same discipline, tighter deadline.

---

## Common pitfalls / troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| Plugin changes behavior | Returned something other than `None` | Observe-only means return `None` |
| Dumps are enormous | Full tool results retained | Summarize tool results; compaction |
| Compaction lost the order id | Summarizer not constrained | Test that ids and amounts survive |
| Cache never hits | Prefix below `min_tokens`, or it changes per call | Keep instruction/tools stable; raise TTL |
| Agent still picks the wrong tool | Descriptions overlap | Rewrite descriptions; cut the tool list |
| Dumps committed to git | No ignore rule | `.gitignore` + TTL |

---

## You are done when

- [ ] Real assembled context captured for a multi-turn run  
- [ ] Slot-by-slot measurement for first and last call  
- [ ] Poisoning reproduced and explained  
- [ ] `EventsCompactionConfig` reduces tokens **and** preserves ids  
- [ ] Context cache configured and reflected in FinOps  
- [ ] 4-tool vs 12-tool experiment with numbers  
- [ ] Source precedence written and clash-tested  
- [ ] Seven-dimension scorecard filled, mechanical checks in CI  

---

## Knowledge check

1. Name the seven slots in an agent's context window.  
2. What is context poisoning, with a Meridian example?  
3. Why can adding tools make an agent less accurate?  
4. What must you verify after enabling compaction?  
5. Why is context quality a cheaper signal than an eval run?

### Answers

1. System instruction, tool schemas, conversation history, retrieved documents, memory, tool results, current message.  
2. A wrong fact enters early and is reused as truth — a mistyped order id from turn 4 still being answered at turn 9.  
3. More tool descriptions mean more similar-looking options, so it picks the wrong one (confusion).  
4. That the facts you cannot lose — order ids, amounts, policy citations — survived the summary.  
5. It is measured before generation, so it costs no model calls and predicts the failure instead of observing it.

---

## Recap

- You looked at your real context for the first time and found what was actually filling it.  
- You reproduced poisoning, then fixed growth with native compaction and cost with prefix caching.  
- You proved fewer tools beat more tools, and gave context a preflight score.

---

## Stretch goal

Run the Lesson 50 persona suite twice — once with your original context, once after every fix in this lesson — and compare failing-turn numbers. That difference is the strongest evidence you will ever have that context, not the model, was the problem.

---

## Feedback

- Could you show a teammate their own assembled context and explain each slot?  
- Note the task number, plus which slot turned out to be the largest.

---

## Navigate

**← Prev** [Lesson 50 — Simulated users & multi-turn eval](50-simulated-users-multiturn-eval.md)  
**Related:** [Lesson 06 — Context & memory](06-context-memory-knowledge.md) · [Lesson 18 — Advanced RAG](18-advanced-rag-retail-policy.md)  
**Next:** Pack G capstones — [Lesson 38 design, 39 ship, 40 mentor](../docs/curriculum-roadmap.md) *(when shipped)*  
**Track home:** [README](../README.md)
