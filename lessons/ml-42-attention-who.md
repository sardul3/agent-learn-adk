# ml-42 — Attention: who looks at whom

**Level:** Absolute beginner  
**Time:** ~50 minutes  
**Prerequisites:** ml-41; venv from **ml-00**  
**Lab outcome:** You print a **4×4** table of who-looks-at-whom, check that **rows sum to 1**, and see token **C** stare at itself **0.94**

---

## At a glance

**Attention** means: each token gets a row of **weights** over the other tokens (and itself). Bigger weight = “I am reading **you** right now.” Weights in a row are a **recipe that sums to 1** (a distribution).

By the end you can explain, without hand-waving:

- the printed 4×4 (tokens A–D)
- rows sum to **1**
- **C** looks at itself **0.94** (almost only C)
- this lab is **toy `X @ X.T` scores**, **not** Q/K/V yet (ml-43)

You will run `lab_attn` and walk softmax-by-hand.

---

## Why this matters

Maya’s ticket is four chunks: `where` `is` `my` `box`. A bag (ml-32) mixes them. Attention lets **`box`** look hard at **`where`** and ignore filler.

If you skip the table, “self-attention” is a brand. Here you can point at row C, column C, **0.94**.

```
        look at A   B    C    D
token A   0.34    0.30 0.15 0.21
token B   0.29    0.33 0.11 0.27
token C   0.03    0.02 0.94 0.00
token D   0.10    0.13 0.01 0.76
```

---

## Concept primer

| Word | Plain English | In Maya’s warehouse |
| --- | --- | --- |
| **Token** | One slot in the sequence | A, B, C, D on the plot ticks |
| **Score** | Raw “how similar” before squash | `X @ X.T` (dot of rows) |
| **Softmax** | Turn a row of scores into positive numbers that **sum to 1** | exp, then divide by the row sum |
| **Attention weight** | After softmax: how much this token reads that one | Cell `A[i, j]` |
| **Self-attention** | Tokens in **one** list looking at that **same** list | C looking at C = 0.94 |
| **Q / K / V** | Three extra mixes (next lesson) | **Not used** in `lab_attn` |

Softmax on one row, in steps:

```
1. subtract the row max   (keeps exp from exploding; does not change the result)
2. exp(each score)
3. divide by the sum of those exp
```

> **Tip:** 0.94 is not “94% sure the ticket is refund.” It is “C’s mixed value will be 94% C’s own vector.”

> **Watch out:** Darker on the `magma` plot = **more** attention (title: `darker = more attention`). Do not invert it.

---

## Setup

Reuse the **ml-00** venv.

### Step 1 — Enter the playground

Why now: the heatmap needs matplotlib; the matrix needs numpy 2.5.2 with seed 0.

```bash
cd project/ml_playground
source .venv/bin/activate
```

- `cd` means “change directory.”
- `source` activates the venv.

**It worked when** `(.venv)` shows and:

```bash
python --version
python -c "import numpy, sklearn; print(numpy.__version__, sklearn.__version__)"
```

```text
Python 3.14.6
2.5.2 1.9.0
```

Close the plot to return to the terminal.

```bash
export ML_HEADLESS=1
```

if you have no display. Stdout **still prints** the 4×4. Prefer a laptop for the heatmap.

---

## Hands-on

### Step 2 — Run the attention lab

Why this command now: the rounded matrix is the exam. Seed `0` makes it match this page.

```bash
python later_labs.py attn
```

- `attn` is the LABS key (function `lab_attn`). Positional, not `--attn`.

**It worked when** stdout is:

```text
attention weights (who looks at whom)
[[0.34 0.3  0.15 0.21]
 [0.29 0.33 0.11 0.27]
 [0.03 0.02 0.94 0.  ]
 [0.1  0.13 0.01 0.76]]
```

and a window titled `ml-42: darker = more attention` with ticks **A B C D** on both axes.

Check three facts on the numbers (do it with a finger):

- Row 0: 0.34+0.30+0.15+0.21 = **1.00**
- Row 2 (token **C**): **0.94** on C, nearly 0 elsewhere
- Row 3 (token **D**): **0.76** on D — also mostly itself, less extreme than C

`0.` in the print is **0.00** rounded to two decimals.

- [ ] You copied the matrix from **your** terminal
- [ ] You found 0.94 at row C, column C

### Step 3 — Walk `lab_attn`

Open `later_labs.py`. Find `lab_attn`.

1. `rng = np.random.default_rng(0)` — frozen random tokens.
2. `X = rng.normal(size=(4, 3))` — **4 tokens**, each a **3-number** list. Not words. Random vectors standing in for embeddings (ml-26’s cousin).
3. `scores = X @ X.T`
   - `X.T` is 3×4
   - `X @ X.T` is **4×4**
   - cell `(i, j)` = dot product of token i with token j — **similarity**, not QKᵀ
4. Softmax rows:
   - `e = np.exp(scores - scores.max(1, keepdims=True))` — subtract row max (`keepdims=True` keeps a column shape so it broadcasts)
   - `A = e / e.sum(1, keepdims=True)` — divide by row sum → rows of `A` sum to 1
5. `print(np.round(A, 2))` — two decimals, the matrix you saw
6. `imshow(A, cmap="magma")` with ticks `list("ABCD")`

There is **no** `Wq`, `Wk`, `Wv`. Those names wait in `lab_qkv`.

> **Tip:** `X @ X.T` is “each token queries with **itself** as key.” ml-43 splits query and key into two notebooks.

> **Watch out:** `scores.max(1, keepdims=True)` — the `1` is **axis 1** (across columns of a row), not “max of 1.” Axis 0 would be wrong and rows would not softmax correctly.

### Step 4 — Prove rows sum to 1

Why now: `round(..., 2)` can hide 0.999. Sum the **true** `A`.

```bash
python -c "
import numpy as np
rng = np.random.default_rng(0)
X = rng.normal(size=(4, 3))
scores = X @ X.T
e = np.exp(scores - scores.max(1, keepdims=True))
A = e / e.sum(1, keepdims=True)
print(np.round(A, 2))
print('row sums', A.sum(1))
print('C self', A[2, 2])
"
```

- `-c` means “run this code string and exit.”
- `A[2, 2]` is token C (0-based index 2) looking at C.

**Expect:**

```text
[[0.34 0.3  0.15 0.21]
 [0.29 0.33 0.11 0.27]
 [0.03 0.02 0.94 0.  ]
 [0.1  0.13 0.01 0.76]]
row sums [1. 1. 1. 1.]
C self 0.9442466233628882
```

The lab’s **0.94** is `round(0.9442…, 2)`. Rows are **exactly** 1.0 in float.

- [ ] `row sums` prints four ones
- [ ] `C self` is about 0.944

---

## How it works (deeper)

Why C is so selfish: after random draw, C’s 3-vector is **long** in a direction the others do not share, so `C·C` dwarfs `C·A`. Softmax then **sharpens** the winner (same idea as low temperature in a later lab).

This is still a bag-with-similarities unless you add **positions** (ml-44). Swap two tokens’ rows in `X` and the pattern of who-looks-at-whom **moves with them** — there is no “first word” stamp yet.

ml-43 will do:

```
Q = X Wq
K = X Wk
V = X Wv
A = softmax(Q K.T / sqrt(d))
out = A V
```

Today you only have `A` from `X X.T`. The mix `A V` is next.

---

## Common pitfalls

1. **Plot never opens.** Unset `ML_HEADLESS` if you want the heatmap. The matrix still prints.
2. **`ModuleNotFoundError`.** `source .venv/bin/activate`.
3. **You called this QKV.** There are no `Wq` matrices in `lab_attn`.
4. **You summed columns.** Attention here is **row-softmax** (who **this** token reads). Columns need not sum to 1.
5. **Index mix-up.** Plot label C is row **2**, not row 3. D is row 3 (0.76).

---

## Knowledge check

Answer from the printed matrix and the code.

1. Copy row 2 of the rounded matrix (token C).
2. Do rows sum to 1? How did you check?
3. What score recipe builds `scores` — QKᵀ or `X @ X.T`?
4. What does token D print on itself (rounded)?
5. How many tokens and what vector size is `X`?

<details>
<summary>Answers</summary>

1. `[0.03 0.02 0.94 0. ]` (C looks at itself 0.94).
2. Yes. `A.sum(1)` is `[1, 1, 1, 1]`; rounded rows also add to 1.00.
3. `X @ X.T` (toy). Not QKV.
4. `0.76`
5. 4 tokens, 3 numbers each `size=(4, 3)`.

</details>

---

## Recap

- **You printed** a 4×4 who-looks-at-whom table and a magma plot.
- **You understand** softmax rows, C’s 0.94 self-look, and that this is not QKV yet.
- **Next** you split query / key / value notebooks and mix `V` with those weights.

Next: `ml-43-qkv-notebooks`

---

## Stretch goal

In `lab_attn`, change `np.round(A, 2)` to **`np.round(A, 3)`**. Save. Rerun:

```bash
python later_labs.py attn
```

- **Expect:** C’s self-weight prints around **`0.944`** instead of `0.94`. Rows still sum to 1. The plot is unchanged (it uses `A`, not the rounded copy).
- Put **`2`** back when you are done so this lesson’s matrix still matches.

---

## Feedback

Could you redo this lab from memory? Note the **lesson id** (`ml-42`), the **step number**, what you **expected**, and what you **saw** (traceback or plot).
