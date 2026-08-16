# ml-48 — Tiny GPT on CPU

**Level:** Absolute beginner  
**Time:** ~55 minutes  
**Prerequisites:** ml-45 (bigram job) and ml-46 (softmax); Setup from ml-00  
**Lab outcome:** You train a character bigram table `W` for 200 steps, sample 40 characters starting at `p`, and treat garbage-ish text as **success**

---

## At a glance

This is a **baby language model** on CPU. Not ChatGPT. Not a transformer stack.

It learns a table `W`: rows = “character I am on,” columns = “character I might emit next.” Same **job** as ml-45. This time the table starts **random** and is **nudged** for **200** steps with the softmax you used in ml-46.

Training text (one string, on purpose tiny):

```text
pack the box. scan the box. dock the van. pack the box. 
```

Sampling **starts at `p`**, then rolls 40 more characters.

**It worked when** you see a messy line like:

```text
sample: pannvbocpsxapan. the bacdve vppanvckthdnt
```

That garbage-ish string is **success**. An honest baby LM. If it wrote a warehouse novel, you would be in the wrong tutorial.

---

## Why this matters

Maya’s intern trains “a GPT” on four warehouse slogans and expects a customer-ready dock script. The sample will look like a keyboard slipped.

That disappointment is the lesson. **Next-token + a bigram table + 200 nudges** can memorize local habits (`pack`, `the`, a period) and still emit `vppanvckthdnt`.

If you skip this, ml-49’s clumsy cousin-of-you bot looks like a bug. It is the same job on *your* sentences.

Do not deploy this as Meridian CX. Do not replace OrderOps with it.

---

## Concept primer

| Word | Plain English | In `lab_tiny_gpt` |
| --- | --- | --- |
| **Bigram brain** | Next character depends only on the current character | `logits = W[data[i]]` |
| **W** | A square table of scores (logits), vocab × vocab | Starts as tiny random numbers (`scale=0.01`) |
| **Step** | One pass of “score how wrong, nudge W” | **200** steps |
| **Sample** | From a start character, pick next, repeat | Start `'p'`, then 40 picks |
| **Baby LM** | A language model small enough to be honest | Garbage-ish output is in spec |

ml-45 **counted**. This lab **trains**:

```text
for 200 steps:
    for each (now, next) in the slogan string:
        chances = softmax(W[now])
        loss += −log(chance of the true next)
        nudge that row of W
```

Then sample with the same softmax, using `rng.choice(..., p=p)`.

> **Tip:** If you see `the` or `pan` inside the mess, the table learned *local* habits. That is all a bigram can honestly claim.

> **Watch out:** A GPT *stacks attention* on top of this same next-character (or next-token) job. The last print in the lab says that. This file does not run attention.

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

### Step 1 — Train and sample

Why this command now: `tinygpt` is the argparse name for `lab_tiny_gpt`. The sample string is the picture.

```bash
python later_labs.py tinygpt
```

`tinygpt` is a lab name, not a dash-flag. The loop is 200 steps on a short string; it should finish in a second or two on this CPU.

**It worked when** you see (numpy 2.5.2, generator seed **4** — this should match):

```text
sample: pannvbocpsxapan. the bacdve vppanvckthdnt
This is a bigram brain. A GPT stacks attention on top of the same next-char job.
```

Read the sample as Maya:

- It **starts with `p`** because the code forces `stoi["p"]`.
- `pan` is a cousin of `pack`.
- ` the ` (space-t-h-e) showed up — that word is in the slogans.
- `vppanvckthdnt` is not a SKU. The intern does not ship it.

- [ ] You ran `python later_labs.py tinygpt`
- [ ] Your sample matches `pannvbocpsxapan. the bacdve vppanvckthdnt`
- [ ] You can say out loud: garbage-ish is success

### Step 2 — Count the slogan once

Open `later_labs.py`. Find `text = "pack the box. scan the box. dock the van. pack the box. "` (trailing space included).

Unique characters become the vocab: letters, spaces, periods. `sorted(set(text))` is the row/column order of `W`.

The string is short on purpose. A bigram cannot learn “dock comes after scan” as a *phrase*. It only learns “after `k` I often see space,” “after space I often see `t` or `s` or `d`,” and so on.

- [ ] You found the training string
- [ ] You believe `W` is vocab × vocab, not “a 12-layer GPT”

### Step 3 — Walk the training loop

Stay in `lab_tiny_gpt`.

1. `rng = np.random.default_rng(4)` freezes the random table **and** the later sample. That is why your sample matches this lesson.
2. `W = rng.normal(scale=0.01, size=(len(chars), len(chars)))` — almost zeros, a little noise.
3. `lr = 0.5` — learning rate: how hard each step yanks `W`.
4. Outer loop: `for _ in range(200):` — **200 steps**.
5. Inner loop: every pair `(data[i], data[i+1])`:
   - `logits = W[data[i]]` — one row: scores for “what next?”
   - `e = np.exp(logits - logits.max())` then `p = e / e.sum()` — **softmax**, with the max trick from ml-46’s tip
   - `y = data[i + 1]` — the true next character
   - `loss += -np.log(p[y] + 1e-8)` — “how shocked were we?” (`1e-8` avoids log(0))
   - `dlogits = p` then `dlogits[y] -= 1` — the softmax+cross-entropy gradient in one line: subtract 1 from the true slot
   - `g[data[i]] += dlogits` — pile the nudge onto that row
6. After the inner loop: `W -= lr * g / (len(data) - 1)` — average the nudges, take a step.

Then **sample**:

7. `ix = stoi["p"]`, `out = ["p"]`.
8. Forty times: softmax that row, `rng.choice` with those chances, append the character, move `ix`.

> **Tip:** `loss` is accumulated but **never printed**. You are not watching a curve today. You are watching the sample.

> **Watch out:** This is **not** attention. Context is one character. That is why `pack` can turn into `pan` and then wander into `nvb`.

### Step 4 — Mini experiment (do it)

Change **only** the start character from `'p'` to `'s'` (the slogans also contain `scan`):

```python
    ix = stoi["s"]
    out = ["s"]
```

Save. Rerun:

```bash
python later_labs.py tinygpt
```

**Expect:** the printed sample **starts with `s`**, then more garbage-ish warehouse crumbs. Still not a paragraph Maya would email.

Put `'p'` / `["p"]` back when you are done.

- [ ] You started from `s`, saw the first letter change
- [ ] You reverted to `p`

---

## How it works (deeper)

ml-45’s table `P` was **counts / row sums**. That is the *maximum-likelihood* bigram if you have enough pairs.

This lab’s `W` is the same idea with **logits**: softmax(row) should end up looking like those chances. Gradient steps are how you get there from random, without writing the count loop.

A production GPT:

- tokens, not always single characters
- attention over a **window** of past tokens (ml-42–ml-45)
- many layers
- temperature on the logits when sampling (ml-46)

The **job** does not change: score every vocab item, turn scores into chances, pick next.

Maya’s rule: if the sample is not something she would send, it is not a CX model. It is a homework brain. ml-49 will force that eval on *your* voice.

---

## Common pitfalls

1. **`ModuleNotFoundError: numpy`.** Venv not active. `source .venv/bin/activate` in `project/ml_playground`.
2. **Your sample does not match.** You changed the seed, the text, the start letter, or you are not on numpy 2.5.2 with this file. Revert edits; seed must stay **4**.
3. **You treated garbage as failure.** The second printed line is the contract: bigram brain. Success is honest mess plus a hint of `the` / `pan`.
4. **You thought 200 steps trained a transformer.** Count the loops: rows of `W` only.
5. **You planned to pipe this sample into OrderOps.** Do not. ADK + Gemini + policy RAG own customer text.

---

## Knowledge check

Answer from the stdout and the loop you walked.

1. What is the exact sample string (after `sample:`)?
2. How many training steps? What table is being nudged?
3. Which character does sampling start from?
4. Why is `pannvbocpsxapan. the bacdve vppanvckthdnt` a **pass**, not a fail?
5. What does the second printed line say a GPT adds on top of this job?

<details>
<summary>Answers</summary>

1. `pannvbocpsxapan. the bacdve vppanvckthdnt`
2. **200** steps. Character bigram table **W**.
3. `'p'`.
4. A baby bigram LM on a tiny slogan string should look clumsy. Local crumbs (`the`, `pan`) plus junk is the honest result.
5. Attention (stacked), still aimed at next-character / next-token.

</details>

---

## Recap

- **You trained** a random vocab×vocab table for 200 steps and sampled from `p`.
- **You understand** garbage-ish is an honest baby LM; GPT’s extra is attention on the same next-token job.
- **Next** the same job on **your** sentences — then Maya’s eval: would she send it to a customer?

Next: `ml-49-you-bot`

---

## Stretch goal

In the outer loop, change `range(200)` to `range(5)` (almost no training). Rerun.

**Expect:** the sample still starts with `p` but looks *more* like noise (less `the`, less `pan`). Five nudges are not 200.

Put `200` back when you are done.

- [ ] You saw the sample change when steps dropped to 5
- [ ] You reverted to 200 so this lesson’s screenshot still matches

---

## Feedback

Could you redo this lab from memory? Note the **lesson id** (`ml-48`), the **step number**, what you **expected**, and what you **saw** (traceback or sample string).
