# ml-45 — Tiny transformer

**Level:** Absolute beginner  
**Time:** ~50 minutes  
**Prerequisites:** ml-44 (positions, encoder vs decoder); Setup from ml-00  
**Lab outcome:** You print a 3×3 next-character table on `abcabcabc` and can say why that table is GPT’s *job*, not a trained transformer stack

---

## At a glance

A **transformer** is a stack: mix tokens with **attention**, then a small net, repeat. This CPU lab does **not** train that stack.

It shows the **job** every GPT still has: guess the **next token** given what you just saw.

You will count `P[next | now]` on the looping string `abcabcabc`. The print is a 3×3 cycle:

- after **a**, next is **b** with chance **1.0**
- after **b**, next is **c** with chance **1.0**
- after **c**, next is **a** with chance **1.0**

That table is a **bigram** table: pairs of (this character, next character). GPT’s last step is still “pick the next token.” Attention is how a real model *looks farther* than one letter.

---

## Why this matters

Meet **Maya**, night-shift warehouse lead at Meridian. She watches someone type a location code: `A`, then `B`, then `C`, then `A` again. After `B` she already knows `C` is coming. No magic. A habit.

If you skip this lab, “we built a tiny transformer” sounds like you trained GPT-2 on a laptop. You did not. You printed the **scoreboard** a language model is trying to fill.

Maya does not need a 12-layer stack to believe “B is followed by C.” She needs you to name the job before you name the architecture.

---

## Concept primer

| Word | Plain English | In this lab |
| --- | --- | --- |
| **Token** | A chunk the model reads as one unit | Here: one character `a`, `b`, or `c` |
| **Vocab** | The list of legal tokens | `"abc"` — three rows, three columns |
| **Bigram** | A pair: now + next | `a` then `b` |
| **P[next \| now]** | Chance of the next token given the current one | Row `b` is `[0, 0, 1]` — only `c` |
| **Transformer stack** | Attention mix, then a net, stacked many times | **Not trained today** |
| **GPT’s job** | Guess the next token | Same job as this table |

The cycle:

```text
     1.0         1.0         1.0
  a ────► b ────► c ────► a ────► …
```

Matrix form (rows = now `a,b,c`; columns = next `a,b,c`):

```text
        next a  next b  next c
now a  [  0.     1.     0.  ]
now b  [  0.     0.     1.  ]
now c  [  1.     0.     0.  ]
```

That is “identity-ish” only in the sense that each row is a one-hot. It is a **cycle**, not the 3×3 identity matrix (identity would mean “next is always myself”).

> **Tip:** If you can count arrows, you can read this lab. Softmax and attention from ml-42–ml-44 are how a *deeper* model fills a table like this when the pattern is not a perfect loop.

> **Watch out:** Do not say “I trained a transformer.” You counted. Counting is honest. Stacking attention is how you get longer patterns than one previous letter.

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

### Step 1 — Run the tiny table

Why this command now: `tinytf` is the argparse lab name for `lab_tiny_tf`. If you skip the run, the matrix stays a drawing.

```bash
python later_labs.py tinytf
```

`tinytf` is a lab name, not a dash-flag. `later_labs.py` only accepts a short list of names (`tinytf`, `temp`, `tinygpt`, …).

**It worked when** you see exactly this (seed is unused; the string is fixed):

```text
P[next|now] rows a,b,c
[[0. 1. 0.]
 [0. 0. 1.]
 [1. 0. 0.]]
This is a one-step transformer-shaped table. Real transformers mix with attention first.
```

- [ ] You ran `python later_labs.py tinytf`
- [ ] Your 3×3 matches the block above

### Step 2 — Read one row out loud

Point at **row 0** (now = `a`).

> “After **a**, next is **b** with chance **1.0**. Next is **a** with chance **0.0**. Next is **c** with chance **0.0**.”

Point at **row 1** (now = `b`).

> “After **b**, next is **c** with chance **1.0**.”

Point at **row 2** (now = `c`).

> “After **c**, next is **a** with chance **1.0**.”

That is Maya’s location-code habit, as numbers.

- [ ] You said all three sentences with the numbers filled in

### Step 3 — Walk the code (do not paste blindly)

Open `later_labs.py`. Find `lab_tiny_tf`.

1. `vocab = "abc"` and `stoi` maps `a→0`, `b→1`, `c→2`.
2. `data` is the integer list for `"abcabcabc"`: `0,1,2,0,1,2,0,1,2`.
3. `C` is a 3×3 **count** table. The loop walks every pair `(now, next)`:

```text
a b  b c  c a  a b  b c  c a  a b  b c
```

That is **8** pairs (string length 9, last letter has no next).

4. Counts:

- `a→b` happens **3** times
- `b→c` happens **3** times
- `c→a` happens **2** times (the **last** `c` is never a “now”)

5. `P = C / row sums`. Each row becomes chances. Row `c` is `2/2 = 1.0` toward `a`, still a clean one-hot.

6. `np.round(P, 2)` is what you printed. The last print tells you the truth: real transformers **mix with attention first**, then guess next.

`rng = np.random.default_rng(0)` sits at the top and is **not used**. That is a clue: this lab is counts, not a random trained net.

> **Tip:** The last `c` having no partner is not a bug. Next-token data is always “pairs from a stream.” End of string = no label.

> **Watch out:** `P[c, a] = 1.0` does **not** mean `c` appeared only once. It means *whenever `c` was a “now,”* the next letter was always `a`.

### Step 4 — Mini experiment (do it)

In `lab_tiny_tf`, change only the training string:

```python
data = np.array([stoi[c] for c in "aaa"])
```

Save. Run again:

```bash
python later_labs.py tinytf
```

**Expect:** row `a` becomes `[1. 0. 0.]` (a→a). Rows `b` and `c` stay `[0. 0. 0.]` because those letters never appear as “now” (the `maximum(..., 1)` guard stops a divide-by-zero, so empty rows print as zeros).

Put `"abcabcabc"` back when you are done so later notes still match.

- [ ] You changed the string, reran, and saw row `a` become self-loop
- [ ] You put `"abcabcabc"` back

---

## How it works (deeper)

A one-step “transformer-shaped” table is:

```text
now  →  (optional mix of farther tokens)  →  scores for every vocab item  →  chances  →  pick next
```

Today the “optional mix” is skipped. Context is **one character**. The scores are **counts**. The chances are **counts / row total**.

A real decoder (GPT-style) still ends on that last arrow: **next token**. What changes:

- context is the whole prefix, not one letter
- attention (ml-42–ml-43) decides *who* to look at
- position tags (ml-44) keep “first A” different from “last A”
- the mix is stacked, then a linear map to vocab size

**Bigram table = the job. Stack = the engine.** Do not mix those sentences.

Maya’s warehouse analogue: a lookup card “after scan letter B, expect C” is the job. A night-shift crew that also reads zone, hour, and the previous *two* letters is the stack.

---

## Common pitfalls

1. **`ModuleNotFoundError: numpy`.** The venv is not active. Prompt must show `(.venv)`. `source .venv/bin/activate` from `project/ml_playground`.
2. **`No such file` / cannot import `meridian_data`.** You are not in `project/ml_playground`. `cd` there first.
3. **You called this “training GPT.”** There is no loss loop here. ml-48 trains a bigram *with gradients*. Today is counts.
4. **You read the matrix as identity.** Identity would be `a→a`, `b→b`, `c→c`. Yours is a **cycle**.
5. **You thought `c→a` should be 3/3.** The last `c` has no next character. Counts use 8 pairs, not 9 letters.

---

## Knowledge check

Answer from the print and the loop you walked, not from a blog.

1. After `b`, what is `P[next = c]` and `P[next = a]`?
2. Write the printed 3×3 as three rows of numbers.
3. How many `a→b` pairs are in `abcabcabc`? Why is `c→a` only 2?
4. Is this lab a trained transformer stack? What is it?
5. What job does GPT still share with this table?

<details>
<summary>Answers</summary>

1. `P[next = c | b] = 1.0`. `P[next = a | b] = 0.0`.
2. `[[0. 1. 0.], [0. 0. 1.], [1. 0. 0.]]`.
3. Three `a→b` pairs. `c→a` is 2 because the final `c` is never a “now.”
4. No. It is a bigram count table (`C` then row-normalize). Attention is not run.
5. Next-token prediction: fill `P[next | context]`. Here context is one character.

</details>

---

## Recap

- **You built** a 3×3 next-character table on `abcabcabc`.
- **You understand** GPT’s job is next token; a transformer stack is how you mix longer context first.
- **Next** you will turn raw scores into chances with **temperature** — and see that T is not weather.

Next: `ml-46-next-token-temperature`

---

## Stretch goal

In `lab_tiny_tf`, change `"abcabcabc"` to `"aabbccaa"` and rerun.

**Expect** (rounded like the lab):

```text
[[0.67 0.33 0.  ]
 [0.   0.5  0.5 ]
 [0.5  0.   0.5 ]]
```

- Row `a`: two `a→a` and one `a→b` out of three “now = a” pairs (`2/3`, `1/3`, `0`).
- Put `"abcabcabc"` back when you are done.

- [ ] You reran and saw fractions, not only 0/1
- [ ] You reverted the string

---

## Feedback

Could you redo this lab from memory? Note the **lesson id** (`ml-45`), the **step number**, what you **expected**, and what you **saw** (traceback or matrix).
