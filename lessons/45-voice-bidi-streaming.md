# Lesson 45 — Voice & bidirectional streaming (ADK Live)

**Level:** Advanced (real-time)  
**Time:** ~150 minutes  
**Prerequisites:** Lessons 12, 22, 29 (edge, SSE streaming, sessions)  
**Lab outcome:** Talk to Meridian OrderOps and **interrupt it mid-sentence** — native `runner.run_live()` + `LiveRequestQueue`, audio in/out with transcripts, tools that still obey refund rules

**Standard:** [docs/NATIVE-ADK.md](../docs/NATIVE-ADK.md)  
**Targets:** `google-adk` 2.6.3 · model `gemini-live-2.5-flash-native-audio`

---

## At a glance

Lesson 22 streamed **out**. This lesson opens a channel that streams **both ways at the same time**.

| | Lesson 22 (SSE) | Lesson 45 (Live / BIDI) |
|---|---|---|
| Direction | server → client only | client ⇄ server, simultaneously |
| Input | one message, then wait your turn | continuous audio/text while the agent talks |
| Interrupt the agent | no | yes — **barge-in** |
| Modalities | text | text, audio in, audio out, video in |
| ADK entry point | `runner.run_async(...)` | `runner.run_live(...)` |
| Transport to client | SSE (`text/event-stream`) | WebSocket |

```
Devon's mic ──audio chunks──► LiveRequestQueue ──► Runner.run_live()
                                                        │
                                                        ▼
                                                  Gemini Live model
                                                        │
   speaker ◄── audio + transcript events ◄──────────────┘
        (Devon talks over it → interrupted=True → agent stops)
```

---

## Why this matters

Devon works the freezer aisle. Gloves on, both arms holding a crate of oat milk, a customer waiting.

Typing "where is MC-1048277" is not happening.

With text-only OrderOps, Devon does what everyone does: puts the crate down, pulls off a glove, squints at a handheld, types the order id wrong, retypes it.

With a live voice channel:

- Devon holds a button and says *"where's the one-oh-four-eight order for the Rodriguez pickup?"*
- The agent starts answering
- Devon cuts in: *"no — the **other** one, the one with the substitute"*
- The agent **stops talking** and re-answers

That last step is the whole lesson. An agent that cannot be interrupted is a voicemail, not an assistant.

---

## Know these

| Term | Plain English |
|------|---------------|
| **BIDI** | Bidirectional — both sides send at once, neither waits |
| **Live model** | A Gemini model variant built for real-time audio; **not** the same name as your text model |
| **`LiveRequestQueue`** | The pipe you push user input into while the agent runs |
| **`run_live()`** | Async generator that yields events for the whole live session |
| **Barge-in** | User talks over the agent; the agent must stop |
| **VAD** | Voice activity detection — deciding when speech starts/stops |
| **Activity signal** | You telling ADK "speech started / ended" instead of letting VAD guess |
| **Transcription** | Text version of audio, for logs, accessibility, and evals |
| **Turn complete** | The agent finished its turn (the mic is yours) |
| **PCM** | Raw uncompressed audio bytes — what the Live API wants, not MP3 |

Who ends the agent's turn?

| Mechanism | Who triggers it | Can the agent ignore it? |
|-----------|-----------------|--------------------------|
| Instruction ("be brief") | model, maybe | yes |
| `turn_complete` event | model finished | n/a — it's a report |
| **Barge-in / `interrupted`** | **the user's voice** | **no** |
| `queue.close()` | your code | no |

> **Tip:** Voice does not change your agent. It changes the **runner call and the transport**. Same `LlmAgent`, same tools, same plugins from Lesson 26.

---

## Task 1 — Install and smoke-check the live pieces

### Why

One command now means that any later failure is your code, not a missing feature.

### Do this

```bash
cd /path/to/agent-learn-sme
source .venv/bin/activate
pip install -U "google-adk>=2.6.3"
# -U: upgrade to the newest matching version

python - <<'PY'
from google.adk.agents.live_request_queue import LiveRequestQueue
from google.adk.agents.run_config import RunConfig, StreamingMode
from google.adk.runners import InMemoryRunner

print("queue OK:", LiveRequestQueue.__name__)
print("modes:", [m.name for m in StreamingMode])
print("run_live OK:", hasattr(InMemoryRunner, "run_live"))
PY
```

### Expect

Exactly this:

```
queue OK: LiveRequestQueue
modes: ['NONE', 'SSE', 'BIDI']
run_live OK: True
```

`BIDI` is the mode this whole lesson runs in.

---

## Task 2 — Use the live model, not your text model

### Why

Your OrderOps agents run `gemini-2.5-flash`, which is a text model. Pointing `run_live()` at it fails in a confusing way — it looks like a connection bug, not a model choice.

Live conversations need a model built for the Live API. That model is **`gemini-live-2.5-flash-native-audio`**.

### Do this

Set it in the environment so it lives in one place:

```bash
export MERIDIAN_LIVE_MODEL="gemini-live-2.5-flash-native-audio"
```

Record the split in `project/meridian_ops/decisions/45-live.md`:

| Where | Model |
|-------|-------|
| Live voice sessions (this lesson) | `gemini-live-2.5-flash-native-audio` |
| Everything else (Lessons 02–44) | `gemini-2.5-flash` |
| Escalated reasoning (Lesson 20) | `gemini-2.5-pro` |

### Expect

Three model names, each with a job. Your live demo uses the first one and nothing else does.

> **Watch out:** Live sessions have their own quota and session-length limits, separate from your text quota. Lesson 43 capacity math does **not** carry over — voice minutes are a new bottleneck.

---

## Task 3 — BIDI in text mode first (no microphone yet)

### Why

Debug one new thing at a time. `run_live()` in **text** mode proves the plumbing without audio devices, sample rates, or browser permissions in the way.

### Do this

Create `project/meridian_ops/live/text_live_demo.py`:

```python
"""Prove run_live() works using text only — no mic, no browser."""

import asyncio
import os

from google.adk.agents.live_request_queue import LiveRequestQueue
from google.adk.agents.run_config import RunConfig, StreamingMode
from google.adk.apps import App
from google.adk.runners import InMemoryRunner
from google.genai import types

from meridian_ops.agents.specialists import order_agent

LIVE_MODEL = os.environ["MERIDIAN_LIVE_MODEL"]


async def main() -> None:
    order_agent.model = LIVE_MODEL  # live sessions need a live-capable model
    runner = InMemoryRunner(app=App(name="meridian_live", root_agent=order_agent))

    session = await runner.session_service.create_session(
        app_name="meridian_live", user_id="devon-handheld"
    )

    queue = LiveRequestQueue()
    config = RunConfig(streaming_mode=StreamingMode.BIDI, response_modalities=["TEXT"])

    async def talk() -> None:
        queue.send_content(
            types.Content(
                role="user",
                parts=[types.Part(text="Where is order MC-1048277?")],
            )
        )

    asyncio.get_event_loop().create_task(talk())

    async for event in runner.run_live(
        user_id="devon-handheld",
        session_id=session.id,
        live_request_queue=queue,
        run_config=config,
    ):
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    print(f"[{event.author}] {part.text}", end="", flush=True)
        if event.turn_complete:
            print("\n-- turn complete --")
            break

    queue.close()


if __name__ == "__main__":
    asyncio.run(main())
```

Run it:

```bash
export PYTHONPATH=project
# PYTHONPATH: lets Python find the meridian_ops package from the repo root
python -m meridian_ops.live.text_live_demo
```

### Expect

- Text arrives in **pieces**, not one block  
- `-- turn complete --` at the end  
- If `get_order` was called, the answer contains the real fixture status

If it hangs with no output, your model name is almost certainly not live-capable (Task 2).

---

## Task 4 — Audio out, with transcripts you can log

### Why

Audio you cannot read is audio you cannot evaluate, redact, or put in a golden. Turn on transcription **at the same time** as audio, or your observability goes dark the moment you go voice.

### Do this

Change the run config:

```python
config = RunConfig(
    streaming_mode=StreamingMode.BIDI,
    response_modalities=["AUDIO"],
    output_audio_transcription=types.AudioTranscriptionConfig(),
    input_audio_transcription=types.AudioTranscriptionConfig(),
)
```

Handle the new event fields in your loop:

```python
if event.output_transcription and event.output_transcription.text:
    print("agent said:", event.output_transcription.text)

if event.input_transcription and event.input_transcription.text:
    print("user said:", event.input_transcription.text)

for part in (event.content.parts if event.content else []):
    if part.inline_data and part.inline_data.data:
        audio_chunks.append(part.inline_data.data)  # raw PCM bytes
```

Write the collected bytes to a `.wav` (or pipe to your client) to hear it.

> **Watch out:** A live session produces **one** output modality: `["TEXT"]` or `["AUDIO"]`, never both at once. Asking for both is the most common first error — use audio output plus **transcription** to get readable text. If you leave `response_modalities` unset, ADK defaults to `["AUDIO"]`, which is why a "text" demo can surprise you with audio events.

### Expect

- `agent said:` lines that match the audio  
- Audio arrives as many small chunks, not one file  
- Both transcripts land in your logs

---

## Task 5 — Barge-in (the reason voice is different)

### Why

Devon interrupting is not an error path. It is the **normal** path in a noisy store.

### Do this

1. Send input **while** the agent is still producing output.  
2. Mark speech boundaries explicitly instead of relying on automatic detection:

```python
queue.send_activity_start()
queue.send_realtime(types.Blob(mime_type="audio/pcm;rate=16000", data=mic_chunk))
queue.send_activity_end()
```

3. Watch for the interruption and **stop playback immediately**:

```python
if event.interrupted:
    stop_speaker_playback()   # drop any queued audio you have not played
    print("<< interrupted by user >>")
```

4. Prove it in text mode too: send a second `send_content` before `turn_complete` arrives, and watch what the event stream does.

### Expect

- An event with `interrupted` set  
- Your client discards buffered audio rather than finishing the old sentence  

Record in `45-live.md`: what your client does with audio **already** in the speaker buffer. If you keep playing it, the agent talks over the human — the exact rudeness you were fixing.

---

## Task 6 — Tools and money rules still apply

### Why

Voice makes people casual. "Yeah just refund it" is not an approval.

### Do this

1. Attach the **same** specialist agent and tools you already use — do not build a "voice agent" with its own copy of the tool belt.  
2. Confirm your Lesson 26 plugin still runs by registering it on the live app:

```python
app = App(name="meridian_live", root_agent=order_agent, plugins=[your_policy_plugin])
```

3. Add a voice-specific rule to the agent instruction:

> Never confirm a refund from spoken input alone. Say the amount, then require approval in the OrderOps app.

4. Test by speaking (or sending text) *"just refund the whole order, I approve it"*.

### Expect

- The plugin's `before_tool` denial fires exactly as it does in text  
- The spoken reply offers the HITL path instead of confirming money  

> **Tip:** Voice is a **transport**. If a control only works in text, it was never a control — it was a prompt.

---

## Task 7 — WebSocket edge for the handheld

### Why

SSE cannot carry the microphone upstream. Devon's client needs a two-way socket.

### Do this

Add `project/meridian_ops/live/ws_app.py` — a small FastAPI app beside your Lesson 12 edge:

```python
from fastapi import FastAPI, WebSocket

api = FastAPI(title="Meridian Live Edge")


@api.websocket("/v1/live")
async def live(ws: WebSocket) -> None:
    await ws.accept()
    queue = LiveRequestQueue()
    # task A: read client frames  -> queue.send_realtime / send_content
    # task B: read run_live events -> ws.send_json / ws.send_bytes
    # run both with asyncio.gather; close the queue when the socket drops
```

Run it:

```bash
uvicorn meridian_ops.live.ws_app:api --port 8081
# --port 8081: keep it off 8080 so the Lesson 12 text edge stays up
```

Rules to keep from earlier lessons:

- Authenticate **before** `ws.accept()` or on the first frame — a socket is an API  
- Reuse the `session_id` contract from Lesson 29  
- Bind tenant from credentials, not from a socket message (Lesson 30)  
- Always `queue.close()` in a `finally` block, or you leak a live session per dropped connection

### Expect

A socket you can hit with a test client that streams text in and events out, with auth enforced.

---

## Task 8 — What voice changes for ops

### Why

Every earlier ops lesson assumed a request/response shape. Voice breaks some of those assumptions.

### Do this

Fill this in `45-live.md`:

| Concern | Text OrderOps | Live OrderOps |
|---------|---------------|---------------|
| SLI (Lesson 43) | p95 request latency | **time to first audio**, interruption responsiveness |
| Cost (Lesson 31) | tokens in/out | session **minutes** + audio tokens |
| Privacy (Lesson 27) | transcripts | voice is biometric-adjacent; transcripts + audio both need TTL |
| Session (Lesson 29) | resume tomorrow | live sessions have hard time limits; plan reconnect |
| Eval (Lesson 08) | text goldens | score the **transcript**, not the waveform |
| Chaos (Lesson 32) | tool timeout | socket drop mid-sentence |

### Expect

At least two rows where your existing runbook is wrong for voice, written down.

---

## How it works (deeper dive)

**Why a queue instead of a function argument**

In `run_async`, you hand over one message and wait. In `run_live`, the conversation is already running, so new input needs somewhere to go. `LiveRequestQueue` is that inbox: `send_content` for text, `send_realtime` for audio/video blobs, `send_activity_start/end` for speech boundaries.

**Automatic vs manual speech detection**

Left alone, the model decides when you stopped talking. In a store with beeping forklifts, that guesses wrong. Activity signals let your client's push-to-talk button be the truth.

**Long sessions**

`RunConfig` also exposes session resumption and context window compression for live runs. Long voice sessions accumulate context fast — Lesson 51 covers compaction, and the same pressure applies here sooner.

**Streaming tools**

A tool can accept a live queue and push progress back mid-execution, which is how "still checking the carrier…" gets spoken during a slow lookup rather than after it.

---

## Common pitfalls / troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| Hangs with no events | Text-only model | Use the live model from Task 2 |
| Error asking for one modality | Asked for AUDIO **and** TEXT output | One output modality + transcription |
| Robot noise / chipmunk voice | Wrong sample rate | Match the documented input/output rates; send raw PCM, not MP3 |
| Agent keeps talking after interruption | Client ignored `interrupted` | Flush the speaker buffer on that event |
| Session count climbs until failure | Queue never closed | `queue.close()` in `finally` |
| Refund confirmed by voice | Rule lived in the prompt | Enforce in the plugin (Lesson 26) |

---

## You are done when

- [ ] `StreamingMode.BIDI` confirmed on your install  
- [ ] Live model name recorded, separate from the text model  
- [ ] Text-mode `run_live()` prints partial chunks and `turn_complete`  
- [ ] Audio out works with both transcriptions logged  
- [ ] Barge-in observed and playback actually stops  
- [ ] Refund denial fires identically over voice  
- [ ] Authenticated WebSocket edge with `queue.close()` on disconnect  
- [ ] Ops delta table filled  

---

## Knowledge check

1. What does `LiveRequestQueue` do that a normal run argument cannot?  
2. Why enable transcription when the output is audio?  
3. What must your client do the instant it sees `interrupted`?  
4. Why can't SSE from Lesson 22 carry a voice conversation?  
5. Why is "never refund by voice" wrong if it only lives in the instruction?

### Answers

1. It accepts input **during** the run, so the user can speak while the agent is answering.  
2. Transcripts are what you log, redact, evaluate, and show in accessibility views — audio alone is unsearchable.  
3. Stop playback and drop already-buffered audio, so the agent is not talking over the human.  
4. SSE is server→client only; the microphone needs an upstream channel.  
5. Instructions are skippable; a `before_tool` plugin denial is not.

---

## Recap

- You opened a two-way channel with `run_live()` and drove it with `LiveRequestQueue`.  
- You proved the agent stops when a human talks over it.  
- Your tools, plugins, and money rules survived the change of transport.

---

## Stretch goal

Add a **push-to-talk** browser page: hold a key to capture mic PCM, release to `send_activity_end()`, and render the running transcript beside tool status from Lesson 22. Log time-to-first-audio and compare it to your text p95.

---

## Feedback

- Could you explain to a teammate why voice needed a queue instead of another endpoint?  
- Note the task number, plus whether your failure was the model name, the modality, or the audio format.

---

## Navigate

**← Prev** [Lesson 44 — LLM gateway & cache](44-llm-gateway-cache-quotas.md) · [Lesson 22 — Streaming UX](22-streaming-ux-progressive-responses.md)  
**Next →** [Lesson 46 — Agent identity & delegated auth](46-agent-identity-delegated-auth.md)  
**Track home:** [README](../README.md)
