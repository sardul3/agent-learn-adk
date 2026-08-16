# ml-47 — Fine-tune vs prompt vs RAG

**Level:** Absolute beginner  
**Time:** ~50 minutes  
**Prerequisites:** ml-46; Setup from ml-00  
**Lab outcome:** You run the three printed ways, then map three Meridian jobs onto them *in the terminal* by adding `print` lines — not on paper

---

## At a glance

Three ways to change what a language model *does* for Maya:

| Way | What you change | Weights move? | Meridian picture |
| --- | --- | --- | --- |
| **Prompt** | Instructions you send *now* | No. Model frozen | “Always ask for the MC- order id first.” |
| **Fine-tune** | The weights, using your texts | Yes | You-bot voice: tiny **local counts** on this CPU (ml-49), not a GPU run of GPT |
| **RAG** | What you **fetch** and paste in, then generate | No. Weights stay | **Weekly refund policy** — point at ADK Lesson 18 by title: **Advanced RAG for retail policy** |

The lab prints those three sentences. You will add three more `print` lines that map Maya’s jobs, rerun, then revert.

This is a **product** lesson. You still run the script. You do **not** replace OrderOps or ADK with `later_labs.py`.

---

## Why this matters

Maya gets three tickets in one hour:

1. “New refund rule dropped Monday. Does a cracked vase still get money back after 14 days?”
2. “Make the bot sound like *me* on night shift, not like a press release.”
3. “Before you guess an ETA, ask for the `MC-` id.”

If you fine-tune a giant model every Monday for (1), you will be late and you will bake last week’s policy into weights. **RAG** fetches this week’s policy.

If you RAG Maya’s *voice* (2), you fetch someone else’s sentences. Voice is a **style in the weights** (or, on this CPU, a **count table** from `my_voice.txt`). That is the fine-tune / local-counts bucket.

If you retrain for (3), you wasted a night. That is a **prompt**.

Skip this lab and every later “we’ll just fine-tune it” is a reflex, not a choice.

---

## Concept primer

| Word | Plain English | What Maya should remember |
| --- | --- | --- |
| **Prompt** | Write instructions. Freeze the model. | Cheap. Instant. Easy to get wrong if the instruction fights the model. |
| **Fine-tune** | Change weights on your texts | Real fine-tunes need data + a training loop. **This CPU track:** tiny local counts (ml-48 / ml-49), not Gemini. |
| **RAG** | Retrieve, then generate. Weights stay | Policy that **changes weekly** belongs here. ADK Lesson 18: **Advanced RAG for retail policy**. |

```text
Prompt:    [frozen model]  +  new instructions
Fine-tune: [same architecture] +  moved knobs
RAG:       [frozen model]  +  fetched Maya policy  +  then generate
```

> **Tip:** Ask “does this fact change next Monday?” If yes, do not bake it into weights. Fetch it (RAG).

> **Watch out:** RAG is not “the model read the internet.” It is **your** retrieve step, then generate. Fine-tune is not “add a system prompt.” Fine-tune **moves numbers in the recipe**.

---

## Setup

If your prompt does not show `(.venv)`, finish Setup in ml-00 first. This playground is **Python 3.14.6**, **numpy 2.5.2**, **scikit-learn 1.9.0**.

```bash
cd project/ml_playground
source .venv/bin/activate
```

- `source` runs the activate script in *this* terminal so `python` is the island’s Python.

**It worked when** `(.venv)` is at the front of the prompt.

---

## Hands-on

### Step 1 — Run the three ways

Why this command now: `threeways` is the argparse name for `lab_three_ways`. The product lesson still starts with real stdout.

```bash
python later_labs.py threeways
```

`threeways` is a lab name, not a dash-flag.

**It worked when** you see **exactly** three lines:

```text
Prompt: write instructions, freeze the model.
Fine-tune: change weights on your texts (CPU: tiny model only).
RAG: keep weights, fetch Maya policy, then generate — this is Lesson 18 in the ADK track.
```

Maya’s read of those three lines:

- Line 1 is a **sticky note** on a frozen recipe.
- Line 2 is **moving knobs** (on this CPU: tiny counts / a tiny `W`, not a 7B download).
- Line 3 is **open the binder, then speak** — and the binder lives in the ADK track.

- [ ] You ran `python later_labs.py threeways`
- [ ] You can point at which line is prompt vs fine-tune vs RAG

### Step 2 — Map Maya’s three jobs in the file (terminal proof)

Why now: reading a table is cheap. Seeing the map **print** is the lab. No notebook paragraph.

Open `later_labs.py`. Find `lab_three_ways`. After the three existing `print` lines, add **these three** (same function, still Python):

```python
    print("Meridian prompt: always ask for the MC- order id before guessing ETA.")
    print("Meridian fine-tune: you-bot voice — tiny local counts on my_voice.txt.")
    print("Meridian RAG: weekly refund policy — Advanced RAG for retail policy.")
```

Save. Run again:

```bash
python later_labs.py threeways
```

**It worked when** you see **six** lines: the original three, then your three maps.

Read them back as Maya:

- Weekly **refund policy** → **RAG** (ADK Lesson 18 title only: **Advanced RAG for retail policy**). You are not doing that lesson tonight.
- **You-bot voice** → **tiny local counts** (the CPU stand-in for fine-tune). Next two lessons actually run that.
- **Ask for MC- id first** → **prompt**. Frozen model. Instructions only.

**Revert** those three `print` lines when you have seen the six-line run, so later screenshots still match Step 1.

- [ ] You added three `print` lines, reran, and saw six lines
- [ ] You can say which Meridian job is RAG vs local counts vs prompt
- [ ] You deleted the three extra lines (reverted)

### Step 3 — Walk the original function

With the extras gone, `lab_three_ways` is three `print` calls. That is on purpose.

1. Line 1: **Prompt** — write instructions, freeze the model.
2. Line 2: **Fine-tune** — change weights on your texts. The parenthetical is the honesty pin: **CPU: tiny model only.** You will not download a 7B model in this folder.
3. Line 3: **RAG** — keep weights, fetch Maya policy, then generate. It points at **Lesson 18 in the ADK track** by that lesson’s role, not by pasting the ADK graph.

There is no numpy in this function. sklearn is not used. The “model” is the *decision* of which lever to pull.

> **Tip:** The ADK track is where weekly policy actually gets retrieved with citations. This bonus track only names the lever.

> **Watch out:** Do not wire `later_labs.py` into OrderOps. Do not tell Maya this script is the refund bot. Prompt / fine-tune / RAG in production still sit on Native ADK + Gemini + tools.

### Step 4 — Confirm revert, then misspell the lab name once

Why now: extra `print` lines left behind will confuse ml-48 notes. Argparse will also teach you the real lab name if your fingers slip.

After you deleted the three map prints, run the happy path again:

```bash
python later_labs.py threeways
```

**Expect:** only the original three lines (no `Meridian prompt:`).

Now misspell it on purpose:

```bash
python later_labs.py threeway
```

**Expect:** argparse error, `invalid choice: 'threeway'`, and a list of legal names that **includes** `threeways`, `tinygpt`, `youbot`, `qvnet`, `capstone`. There is no dash-flag here. The first argument is the lab name.

- [ ] Happy path is three lines again
- [ ] You saw `threeways` in the argparse choices list

---

## How it works (deeper)

Think of a frozen recipe (ml-00) as the **base model**.

- **Prompt** = a sticky note on the recipe: “ask for the id first.” The 5 and the 2 do not move.
- **Fine-tune** = nudge the 5 and the 2 using *your* packing times (or your sentences). On this CPU, ml-48 nudges a bigram table `W`; ml-49 *counts* your characters. Both are “change the recipe from local text.”
- **RAG** = before you guess, open this week’s policy binder and put the matching page next to the question. The 5 and the 2 still do not move.

Weekly refund rules change. Weights should not have to. That is why Maya’s policy work is RAG in the ADK track, not a Monday fine-tune.

Voice is the opposite: the fact you want is *how Maya sounds*, not a paragraph that Legal rewrote this morning. Tiny local counts (or a real fine-tune later) belong there.

A **nightly CSV export** of scan times is a job. It is not prompt, not fine-tune, not RAG. Stretch will print that so the three buckets do not swallow the warehouse.

---

## Common pitfalls

1. **`ModuleNotFoundError`.** Venv not active. `cd project/ml_playground` and `source .venv/bin/activate`.
2. **You left the extra `print` lines in.** Revert after you have the six-line proof. Stretch adds a *different* fourth line next.
3. **You called weekly policy a fine-tune.** Policy text that Legal updates is a fetch. RAG.
4. **You called you-bot RAG.** Fetching a style guide is not the same as counting *your* characters. Voice → local counts on this track.
5. **You planned to replace OrderOps with these prints.** This lesson names levers. Pack A / Pack D still own production CX.

---

## Knowledge check

Answer from the three original printed lines and the maps you ran.

1. What is the exact first printed line of `python later_labs.py threeways` (before your extras)?
2. Weekly refund policy: which of the three ways? Which ADK lesson title do you point at (title only)?
3. You-bot voice on this CPU: which way, and what does “tiny” mean here?
4. “Always ask for the MC- order id first”: which way, and do weights move?
5. Does this script replace the OrderOps agent?

<details>
<summary>Answers</summary>

1. `Prompt: write instructions, freeze the model.`
2. RAG. **Advanced RAG for retail policy** (ADK Lesson 18). You do not run that lesson in this folder.
3. Fine-tune bucket, implemented as **tiny local counts** (you-bot / bigram), not a GPU GPT fine-tune.
4. Prompt. Weights stay frozen.
5. No.

</details>

---

## Recap

- **You ran** the three printed levers, then proved Maya’s maps with extra `print` lines in the terminal.
- **You understand** weekly policy → RAG; voice → local counts; sticky-note instructions → prompt.
- **Next** a baby language model that actually **nudges** a character table for 200 steps — garbage-ish sample is success.

Next: `ml-48-tiny-gpt-cpu`

---

## Stretch goal

In `lab_three_ways`, add **one** extra line (keep or restore the original three prints only, plus this):

```python
    print("Nightly CSV job — not a model.")
```

Rerun:

```bash
python later_labs.py threeways
```

**Expect:** four lines. The fourth is a warehouse job that is **not** prompt, fine-tune, or RAG. Maya still exports CSVs with a script. That is allowed. It is just not a language model.

Delete the extra `print` when you are done (revert).

- [ ] You saw `Nightly CSV job — not a model.`
- [ ] You reverted so the lab prints three lines again

---

## Feedback

Could you redo this lab from memory? Note the **lesson id** (`ml-47`), the **step number**, what you **expected**, and what you **saw** (traceback or printed lines).
