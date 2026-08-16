# ml-51 — Capstone — ticket + photo + delay

**Level:** Absolute beginner  
**Time:** ~70 minutes  
**Prerequisites:** **ml-49** (you-bot humility) and **ml-38** (dented-box pixels). Setup from ml-00.  
**Lab outcome:** You run one CPU slice that prints `intent refund`, `dent_score 0.117`, `delay_days 0.86`, suggests **check scans first**, and you can walk *why* the damage path did **not** fire

---

## At a glance

One Meridian moment, three leftover toys glued together:

| Signal | Where you learned it | What the capstone does |
| --- | --- | --- |
| **Ticket intent** | Naive Bayes on ten toy sentences (M5) | Predicts a label for a mixed sentence |
| **Dent score** | Dark pixels on a 16×16 box (M8 / ml-38) | Fraction of pixels darker than 0.4 |
| **Delay days** | Ticket table (M1) | Prints the first row’s delay — **not** used in the `if` |

You will run:

```bash
python later_labs.py capstone
```

Stdout (numpy 2.5.2, sklearn 1.9.0, frozen seeds):

```text
intent refund dent_score 0.117 delay_days 0.86
suggested: check scans first.
ADK track: same ticket would call tools + Gemini. This capstone is the 'feel the parts' version.
```

**Teaching punch:** the query is `"the carton is crushed and I want a refund"`. The photo **is** dented (`0.117 > 0.02`). Bayes still said **refund** (mixed ticket). The `if` requires `intent == "damage"` **and** `dent_score > 0.02`. So you do **not** open the damage path.

Composition plus a **failure mode**. That is the capstone.

This script is **not** OrderOps. The ADK track would call **tools + Gemini + policy RAG**. Do not replace OrderOps with this file.

---

## Why this matters

Maya gets: “the carton is crushed and I want a refund.”

A human hears **damage** *and* **refund**. A ten-sentence Bayes model hears a word fight and picks **refund** (`0.368` vs `0.358` vs `0.274` — you will print those in a mini experiment).

If the intern ships “we combined NLP + vision + delay,” but the `if` ignores delay and requires a **pure** damage label, the night shift still checks scans while a crushed carton sits on the floor.

If you cannot walk that `if/else`, the bonus track was tourism. If you then say “so we should replace OrderOps with this script,” you missed Pack A.

---

## Concept primer

No new math. **Composition** of parts you already ran.

| Piece | Function | Honest limit |
| --- | --- | --- |
| **MultinomialNB + TfidfVectorizer** | Bag of weighted words → `wismo` / `refund` / `damage` | Ten toy lines. Mixed tickets wobble. |
| **`_box(True, 9)`** | Plant a dark dent, add noise | Synthetic 16×16. Not a dock camera. |
| **`dent_score`** | `(img < 0.4).mean()` | Fraction of dark pixels. Threshold `0.02` is a toy gate. |
| **`tickets(40)` delay** | First row `0.86` days | Printed. **Not** in the branch. |
| **Suggested path** | `if intent == "damage" and dent_score > 0.02` | Else: check scans first. |

```text
query ──► Bayes intent
photo ──► dent_score
table ──► delay_days (spectator)

if intent is damage AND dent_score > 0.02:
    open damage path (CPU toys only)
else:
    check scans first
```

> **Tip:** Read the `if` before you trust the three printed numbers. Printing a number does not mean the recipe used it.

> **Watch out:** Do not replace OrderOps, ADK, or Gemini with `lab_capstone`. The last print already says the ADK track would call tools + Gemini.

---

## Setup

If your prompt does not show `(.venv)`, finish Setup in ml-00 first. This playground is **Python 3.14.6**, **numpy 2.5.2**, **scikit-learn 1.9.0**.

```bash
cd project/ml_playground
source .venv/bin/activate
```

- `source` runs the activate script in *this* terminal so `python` is the island’s Python.

**It worked when** `(.venv)` is at the front of the prompt.

You do not need the RL venv. Stay in `ml_playground`.

---

## Hands-on

### Step 1 — Run the capstone

Why this command now: `capstone` is the argparse name for `lab_capstone`. The failure mode only exists if you see **refund** next to a real dent score.

```bash
python later_labs.py capstone
```

`capstone` is a lab name, not a dash-flag.

**It worked when** you see:

```text
intent refund dent_score 0.117 delay_days 0.86
suggested: check scans first.
ADK track: same ticket would call tools + Gemini. This capstone is the 'feel the parts' version.
```

Say this as Maya:

> “Intent is **refund**. Dent score is **0.117**. Delay is **0.86** days. Suggestion is **check scans first** — not the damage path.”

- [ ] You ran `python later_labs.py capstone`
- [ ] Your three numbers match `refund`, `0.117`, `0.86`

### Step 2 — Walk the `if/else` (the punch)

Open `later_labs.py`. Find `lab_capstone`.

Read this block in order:

1. `df = tickets(40)` — fake ticket table, seed 3 inside `tickets`.
2. `TICKET_TEXTS` — ten `(sentence, label)` pairs from `meridian_data.py`. Labels: `wismo`, `refund`, `damage`.
3. `make_pipeline(TfidfVectorizer(), MultinomialNB()).fit(texts, y)` — same family as ml-25. Open `TICKET_TEXTS` in `meridian_data.py` and count labels: **4** `wismo`, **3** `refund`, **3** `damage`. Priors are not even. The mixed query still loses as **refund** because of the words, not because damage was missing from training.
4. `img = _box(True, 9)` — **dented** box (`True`), seed 9. Same helper as ml-38.
5. `dent_score = (img < 0.4).mean()` — **0.117**. That is **30 / 256** pixels (16×16). The planted dark patch is about that size.
6. `delay = df["delay_days"].iloc[0]` — **0.86**. First row only. Look: delay is **never** named again in the `if`.
7. Query:

```python
intent = clf.predict(["the carton is crushed and I want a refund"])[0]
```

8. Branch:

```python
if intent == "damage" and dent_score > 0.02:
    print("suggested: open damage path, ask for photo — CPU models only, not Gemini.")
else:
    print("suggested: check scans first.")
```

Now plug in **your** stdout:

| Check | Value | Pass the `if`? |
| --- | --- | --- |
| `intent == "damage"` | `intent` is **`refund`** | **No** |
| `dent_score > 0.02` | **0.117 > 0.02** | Yes |

**And** fails. Else branch. **check scans first.**

The carton *is* crushed in the sentence. The photo *is* dented. The recipe still walks away from the damage path because Bayes lost a photo-finish to **refund**.

That is not “the computer is dumb” as a vibe. That is **this `if`** plus **this mixed query** plus **ten training lines**.

> **Tip:** `0.117 > 0.02` can lull you. Always check **both** sides of an `and`.

> **Watch out:** `delay_days 0.86` looks like a third input. It is a spectator. A late package story is sitting in the printout unused.

### Step 3 — Mini experiment: print the Bayes fight

Why now: “mixed ticket” should be a number, not a slogan.

In `lab_capstone`, just after `intent = clf.predict(...)`, add:

```python
    print(np.round(clf.predict_proba(["the carton is crushed and I want a refund"])[0], 3), clf.classes_)
```

Save. Rerun:

```bash
python later_labs.py capstone
```

**Expect** a line like:

```text
[0.358 0.368 0.274] ['damage' 'refund' 'wismo']
```

Read it:

- `damage` **0.358**
- `refund` **0.368** ← winner, by **0.010**
- `wismo` **0.274**

Maya would not bet a warehouse on a 0.01 gap. The script still picks `argmax` and moves on.

Delete that `print` when you have the numbers (revert) unless you want it for notes — then revert anyway so this lesson’s default stdout stays three lines.

- [ ] You printed `[0.358 0.368 0.274]` and the class order
- [ ] You can say refund won by about **0.01**
- [ ] You reverted the extra print

### Step 4 — Mini experiment: a pure damage sentence

Change **only** the query string to:

```python
    q = "the carton is crushed"
    intent = clf.predict([q])[0]
```

(Keep using `q` in `predict` if you introduced it; otherwise replace the string in place.)

Rerun `python later_labs.py capstone`.

**Expect:**

- `intent` becomes **`damage`**
- `dent_score` stays **0.117**
- `delay_days` stays **0.86**
- suggested line becomes:

```text
suggested: open damage path, ask for photo — CPU models only, not Gemini.
```

Now both sides of the `and` pass. The photo was never the blocker. The **mixed wording** was.

Put `"the carton is crushed and I want a refund"` back when you are done.

- [ ] You saw the damage-path sentence
- [ ] You reverted the query so the capstone fails closed again (scans first)

### Step 5 — Contrast with the ADK track (do not build it here)

The last printed line is the contract:

```text
ADK track: same ticket would call tools + Gemini. This capstone is the 'feel the parts' version.
```

What this CPU file **cannot** do:

- look up order `MC-…` with a real tool
- fetch **this week’s** refund policy (RAG — Lesson 18 title: **Advanced RAG for retail policy**)
- ask a human, log a trace, eval a trajectory
- refuse to answer when `0.358` vs `0.368` is a coin flip

What you should **not** do:

- replace OrderOps with `later_labs.py`
- paste `suggested: check scans first` into production CX
- call this Gemini

If you have **not** done Pack A yet, your next home is `01-agentic-foundations`. If you already finished Pack A, Pack D is where policy RAG and multimodal OrderOps live.

- [ ] You read the last printed line (tools + Gemini, feel-the-parts)
- [ ] You did not wire this script into OrderOps as a replacement

---

## How it works (deeper)

**Intent.** `TfidfVectorizer` turns the ten training sentences into weighted word counts. `MultinomialNB` multiplies per-class word chances (naive = pretends words are independent — ml-25). `"crushed"` pulls toward `damage`. `"refund"` pulls toward `refund`. Together, refund wins by a hair.

**Dent.** `_box(True, 9)` paints a rectangle of brightness `0.25` on a `0.6` box on a `0.85` background, plus noise. `(img < 0.4).mean()` counts the dark patch. **0.117** is that fraction. ml-38 trained a linear-on-pixels toy; here we skip the trained weights and use a **threshold on darkness**. Honest shortcut.

**Delay.** `tickets(40)` draws `delay_days` with seed 3. Row 0 is **0.86**. A real refund policy might care. **This `if` does not read it.** Composition theater.

**Why “check scans first” is still a reasonable *else*.** If the model is not sure it is damage, Maya often *does* pull scans before she opens a claims path. The bug is not the else text. The bug is **being sure** you combined vision when the branch never asked the photo unless Bayes already said `damage`.

```text
human: crushed + refund  →  handle both
Bayes: refund (0.368)    →  skip damage if
photo: dented (0.117)    →  unused
delay: 0.86              →  unused
```

That diagram is the capstone.

---

## Common pitfalls

1. **`ModuleNotFoundError: sklearn`.** ML venv not active. `cd project/ml_playground` then `source .venv/bin/activate`. sklearn **1.9.0**.
2. **Numbers differ.** You edited `_box`, the query, or `tickets` seed. Revert. Expect `refund`, `0.117`, `0.86`.
3. **You thought dent_score 0.117 was too small to count.** The gate is `> 0.02`. The photo passed. Intent failed.
4. **You thought delay changed the suggestion.** It is not in the `if`.
5. **You left the damage query in.** Put the mixed sentence back so the failure mode stays the default demo.
6. **You decided to replace OrderOps with this script.** Do not.

---

## Knowledge check

Answer from the stdout and the `if` you walked. Actual numbers.

1. What three values print after `intent`, `dent_score`, and `delay_days`?
2. What is the suggested line on the default query?
3. Write the `if` condition in English.
4. Why did the damage path **not** run, even though `dent_score` is 0.117?
5. What are the three class probabilities (damage, refund, wismo) on the mixed query, and which class names go with that vector?
6. Does `delay_days` 0.86 enter the branch?
7. Should this file replace OrderOps / ADK?

<details>
<summary>Answers</summary>

1. `refund`, `0.117`, `0.86`.
2. `suggested: check scans first.`
3. If intent is exactly `"damage"` **and** dent_score is greater than **0.02**, open the damage path; otherwise check scans first.
4. `intent` is `"refund"`, so the first half of the `and` is false. The photo already passed `0.117 > 0.02`.
5. `[0.358 0.368 0.274]` with `clf.classes_` `['damage' 'refund' 'wismo']`. Refund wins 0.368 to 0.358.
6. No. It is only printed.
7. **No.** ADK track: tools + Gemini + policy RAG. This is the feel-the-parts version.

</details>

---

## Recap

- **You assembled** intent + dent + delay on CPU and watched the mixed ticket **miss** the damage path.
- **You understand** composition can print three signals and still branch on one label; 0.01 Bayes gaps are not warehouse-grade certainty.
- **You can start** the agent track without thinking these scripts are production CX.

Next: `01-agentic-foundations`  
If you **already** finished Pack A, go to **Pack D** (start at Lesson 18 — **Advanced RAG for retail policy** — when the job is weekly policy, not this CPU `if`).

---

## Stretch goal

Two edits, one at a time, then revert both.

**A.** Make the photo gate *easier* — change `0.02` to `0.001`. Rerun with the **default mixed query**.

**Expect:** still **check scans first.** Intent is still `refund`. A looser photo gate does not matter until Bayes says `damage`. (`0.117` already passed `0.02`; this only makes that side easier.)

**B.** Put `0.02` back. Change the query to `"box was crushed corner torn item dented"` (a training-like damage line). Rerun.

**Expect:** `intent damage` and the **open damage path** line (dent_score still `0.117`).

Revert the query to `"the carton is crushed and I want a refund"` when you are done.

- [ ] Stretch A: mixed query + high dent gate still said scans first
- [ ] Stretch B: a damage-like line opened the damage path
- [ ] You reverted so default stdout matches this lesson

---

## Feedback

Could you redo this lab from memory? Note the **lesson id** (`ml-51`), the **step number**, what you **expected**, and what you **saw** (traceback, `intent` label, or suggested line).
