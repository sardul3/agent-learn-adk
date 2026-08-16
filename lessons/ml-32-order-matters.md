# ml-32 — Order matters

**Level:** Absolute beginner  
**Time:** ~40 minutes  
**Prerequisites:** ml-23 (bags) and ml-31; venv from **ml-00**  
**Lab outcome:** You prove `late smashed` and `smashed late` become the **same** bag, then say why Maya still cares which word came first

---

## At a glance

A **bag of words** (ml-23) counts each word and **throws the order away**. Maya’s tickets are not bags. “Late, then smashed” is a delay story. “Smashed late” is a damage story.

By the end you can explain, without hand-waving:

- why two opposite warehouse sentences can share one count vector
- what **sequence** means (read left to right, keep who came first)
- why the next labs exist (RNN, then LSTM, then attention)

You will run the lab, then type a five-line `CountVectorizer` proof. You will not train a net today.

---

## Why this matters

Maya reads a night-shift ticket:

> “carton arrived **late smashed** at dock 2”

versus:

> “carton arrived **smashed late** — photo attached”

A bag sees the words `late` and `smashed` once each. Same pile. Same panic. Same wrong refund path.

If you skip this lab, ml-33 looks like “extra math.” It is not. It is the fix for this hole.

```
bag:     {late: 1, smashed: 1}   ← order gone
sequence: late → smashed         ← order kept
```

---

## Concept primer

| Word | Plain English | In Maya’s warehouse |
| --- | --- | --- |
| **Token** | A chunk you count (here: a word) | `late`, `smashed` |
| **Bag of words** | A list of counts. Order is discarded | Both phrases → `[1, 1]` |
| **Count vector** | That list, as a row of numbers | Column `late`, column `smashed` |
| **Sequence** | Tokens in the order they were written | First `late`, then `smashed` |
| **RNN** | A recipe that reads one token, then the next, and keeps a short memory | Reads `A1-B2` left to right (ml-33) |
| **Transformer** | A recipe that looks at all tokens at once **plus positions** | Can tell first word from last (ml-42+) |

n-grams (ml-24) were a **partial** fix: they count “late smashed” as a pair. They still miss long-distance order. Sequences are the real fix.

> **Tip:** If swapping two words can change the refund, a bag is the wrong picture.

> **Watch out:** Do not jump to GPT to classify ten tickets. Naive Bayes on bags (ml-25) can still win when order does not matter. Use a sequence model when order **does**.

---

## Setup

You already built the Python island in **ml-00**. Do not recreate it.

### Step 1 — Enter the playground

Why now: `later_labs.py` imports `meridian_data.py` from the **current** folder. If you skip `cd`, imports fail.

```bash
cd project/ml_playground
source .venv/bin/activate
```

- `cd` means “change directory.” There is no dash-flag here.
- `source` runs `activate` **in this shell** so `python` is the venv’s interpreter.

**It worked when** your prompt shows `(.venv)` and this prints the pins from ml-00:

```bash
python --version
python -c "import numpy, sklearn; print(numpy.__version__, sklearn.__version__)"
```

```text
Python 3.14.6
2.5.2 1.9.0
```

This track is pinned to **Python 3.14.6**, **numpy 2.5.2**, and **sklearn 1.9.0**. You do not need a GPU.

---

## Hands-on

### Step 2 — Run the order lab

Why this command now: it prints the exact pair this lesson is about. If you skip it, the hole stays abstract.

```bash
python later_labs.py order
```

- `later_labs.py` is the script. `order` is a **positional lab name**, not a flag. There is no `--order`.
- `argparse` only accepts the short list in `LABS` (including `order`, `rnn`, `lstm`, …). A typo prints the legal names and exits.

**It worked when** you see exactly:

```text
bag-of-words cannot tell these apart: late smashed vs smashed late
RNN / transformers can, because they read left to right (or with positions).
```

- [ ] The first line names both phrases
- [ ] The second line names the two families you will meet next

### Step 3 — Walk `lab_order` (do not paste blindly)

Open `later_labs.py`. Find `lab_order`.

1. `a = "late smashed"` — Maya’s delay-then-damage wording.
2. `b = "smashed late"` — Maya’s damage-then-time wording.
3. `print(...)` — the script **does not** build a bag. It only names the failure. You will prove the bag in Step 4.

That is the whole function. Two strings and two prints. The math lives in sklearn, which you already used in ml-23.

> **Tip:** A motivation lab still has a command. Reading the comment is not the lab. Running it is.

> **Watch out:** The print says “cannot tell these apart.” That is a claim about **bags**, not about Maya. Maya can tell. The bag cannot.

### Step 4 — Prove the bags are equal

Why now: the lab *told* you the bags match. You should **force sklearn to say it** so you are not taking a slogan on faith.

`-c` means “run this Python code string, then exit.” Quotes wrap the program so the shell does not eat it.

```bash
python -c "
from sklearn.feature_extraction.text import CountVectorizer
v = CountVectorizer()
X = v.fit_transform(['late smashed', 'smashed late'])
print('vocab', v.get_feature_names_out())
print(X.toarray())
print('equal', (X[0].toarray() == X[1].toarray()).all())
"
```

Walk that snippet before you trust the output:

1. `CountVectorizer()` — sklearn’s bag builder. Default: lowercase on, split on word characters. No extra flags in this call.
2. `fit_transform([...])` — **fit** = learn the column names from these two phrases; **transform** = count. Together: build the table.
3. `get_feature_names_out()` — the column headers, alphabetical: `late` then `smashed`.
4. `toarray()` — turn the sparse matrix into a dense 2×2 you can read.
5. `.all()` — True only if every cell of row 0 matches row 1.

**It worked when** you see:

```text
vocab ['late' 'smashed']
[[1 1]
 [1 1]]
equal True
```

Read the matrix out loud:

> “Row 0 is late smashed: one `late`, one `smashed`. Row 1 is smashed late: one `late`, one `smashed`. Same row. `equal True`.”

That `True` is the whole point of ml-32.

- [ ] Vocab is exactly `late` and `smashed` (two columns)
- [ ] Both rows are `[1 1]`
- [ ] `equal True` printed

### Step 5 — Say the Maya sentence

Fill this in out loud (or honestly in your head):

> “A bag of words turns **late smashed** and **smashed late** into **[1, 1]**. Maya would not refund them the same way. Next I need a model that **reads in order**.”

- [ ] You said it with the numbers from Step 4
- [ ] You can point at which file (`later_labs.py`) printed the slogan vs which command proved it

---

## How it works (deeper)

The computer is not “confused by English.” It is doing the job you asked: **count**, not **read**.

```
phrase → split into words → count each vocab slot → forget who was first
```

For these two phrases the counts are identical, so every later step that **only** sees the bag (Naive Bayes, a linear layer on counts, a keyword score) gets the same input. Same input → same guess.

A sequence model gets a **list**:

```
["late", "smashed"]     ≠     ["smashed", "late"]
```

ml-33 stores a memory `h` that changes after each letter. ml-42 stores **who looks at whom**. ml-44 stamps **position** so “first token” is not “last token.” All of that is in service of this `True`.

n-grams would give `late smashed` a column that `smashed late` does not share. That helps **adjacent** swaps. It does not help “not … damaged” with ten words in between. That is why the track does not stop at ml-24.

---

## Common pitfalls

1. **`ModuleNotFoundError: sklearn` (or numpy).** The venv is not active. Your prompt must show `(.venv)`. Redo Step 1’s `source` line.
2. **`No such file` / cannot import `meridian_data`.** You are not in `project/ml_playground`. `cd` there first.
3. **`unrecognized arguments: --order`.** `order` is positional. Drop the dashes.
4. **`python -c` SyntaxError.** The shell split your string. Use the exact quotes from Step 4 (double quotes around the program, single quotes inside).
5. **You treated `equal True` as “Maya agrees.”** She does not. The **representation** is equal. The **meanings** are not.

---

## Knowledge check

Answer from the stdout you printed, not from a blog.

1. What is the **first line** `python later_labs.py order` prints? Copy it.
2. After `CountVectorizer`, what are the two column names, in order?
3. What two rows does `X.toarray()` print, and what does `equal` print?
4. Is `lab_order` itself building a bag, or only naming the failure?
5. Name two model families the lab says can tell the phrases apart — and say *how* (left-to-right vs positions).

<details>
<summary>Answers</summary>

1. `bag-of-words cannot tell these apart: late smashed vs smashed late`
2. `late` then `smashed` (sklearn sorts the vocab).
3. `[[1 1], [1 1]]` and `equal True`.
4. Only naming. The two assignments and two `print`s. Your `-c` snippet is the bag.
5. RNNs (read left to right) and transformers (positions, later labs).

</details>

---

## Recap

- **You ran** `python later_labs.py order` and a `CountVectorizer` proof.
- **You understand** a bag is counts without order; Maya’s tickets need order.
- **Next** you unroll a tiny RNN so memory changes after each character of `A1-B2`.

Next: `ml-33-rnn-unrolled`

---

## Stretch goal

In `lab_order`, change the two phrases to Maya’s other swap: `a = "not damaged"` and `b = "damaged not"`. Save. Run:

```bash
python later_labs.py order
```

Then rerun Step 4’s `-c` with those two strings instead.

- **Expect:** the slogan still prints (the lab does not care which strings you stored). The vectorizer still prints `equal True` — both bags are one `damaged` and one `not`.
- Put `late smashed` / `smashed late` back when you are done so this lesson’s screenshot still matches.

---

## Feedback

Could you redo this lab from memory? Note the **lesson id** (`ml-32`), the **step number**, what you **expected**, and what you **saw** (traceback or printout).
