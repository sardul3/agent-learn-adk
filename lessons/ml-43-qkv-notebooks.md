# ml-43 — Q, K, V notebooks

**Level:** Absolute beginner  
**Time:** ~50 minutes  
**Prerequisites:** ml-42; venv from **ml-00**  
**Lab outcome:** You print **Q, K, V** each shape **`(4, 3)`** and **mixed values** shape **`(4, 3)`**, then walk `Q = X Wq`, `A = softmax(QKᵀ / √3)`, `out = A V`

---

## At a glance

ml-42 let each token look at others using **the same vector** for “who I am” and “who I seek.” Real attention **splits the job** into three notebooks:

- **Query (Q)** — what I am looking for
- **Key (K)** — the label on a page
- **Value (V)** — the notes on that page

By the end you can explain, without hand-waving:

- three mixes `X @ Wq`, `X @ Wk`, `X @ Wv`
- why you divide by **√3** (`sqrt(3)` ≈ 1.732)
- `out = A @ V` as “blend the notes using the who-looks-at-whom table”

You will run `lab_qkv`. No plot. Shapes are the output.

---

## Why this matters

Maya hunts a policy page. **Query** is her question (“late smash refund?”). **Keys** are section titles. **Values** are the paragraphs. She does not mix titles into the answer — she mixes **paragraphs**, weighted by how well titles matched the question.

If you skip this lab, “QKV” is three random letters. Here they are three **(4, 3)** tables and one mix.

```
X (tokens) → Q, K, V
A = softmax(Q K.T / sqrt(3))     # who looks at whom
out = A @ V                      # blended notes
```

---

## Concept primer

| Word | Plain English | In Maya’s warehouse |
| --- | --- | --- |
| **X** | Token table | 4 tokens × 3 numbers |
| **Wq, Wk, Wv** | Three small recipes (3×3) | Turn X into notebooks |
| **Q query** | “What am I looking for?” | Shape `(4, 3)` |
| **K key** | “What is this page labeled?” | Shape `(4, 3)` |
| **V value** | “What notes do I copy if I pick you?” | Shape `(4, 3)` |
| **Scale √d** | Divide scores so softmax is not spiky | `d = 3`, `sqrt(3)` |
| **Mixed values** | Each token’s new vector after reading others | `out`, shape `(4, 3)` |

```
for each token i:
    look at keys of everyone
    pick a row of weights A[i, :]   (sums to 1)
    out[i] = weighted sum of value rows
```

> **Tip:** Q and K must share the last size (here 3) so `Q @ K.T` is 4×4. V’s last size can differ in bigger models. In this lab all three are 3.

> **Watch out:** `lab_qkv` uses `np.exp(Q @ K.T / scale)` **without** subtracting the row max first. Fine for this tiny random draw. ml-42 was the numerically safer pattern. Do not “fix” the lab unless you are in stretch-and-revert.

---

## Setup

Reuse the **ml-00** venv.

### Step 1 — Enter the playground

Why now: seed `1` and numpy 2.5.2 freeze the shapes (shapes would match anyway; stay pinned).

```bash
cd project/ml_playground
source .venv/bin/activate
```

- `cd` means “change directory.”
- `source` activates the venv in this shell.

**It worked when** `(.venv)` shows and:

```bash
python --version
python -c "import numpy, sklearn; print(numpy.__version__, sklearn.__version__)"
```

```text
Python 3.14.6
2.5.2 1.9.0
```

No `plt.show()`. Two print lines.

---

## Hands-on

### Step 2 — Run the QKV lab

Why this command now: the shapes are the acceptance test. If you skip it, you will guess `(4, 4)` because attention is 4×4.

```bash
python later_labs.py qkv
```

- `qkv` is a positional lab name, not `--qkv`.

**It worked when** you see:

```text
Q query notebook shape (4, 3) K key (4, 3) V value (4, 3)
mixed values shape (4, 3)
```

Read it:

- **Q, K, V** — same shape as `X`: one notebook row per token
- **mixed values (4, 3)** — still one row per token, but each row is a **blend** of value rows

The 4×4 attention table is **inside** the function (`A`). It is **not** printed. You already saw a 4×4 in ml-42.

- [ ] All four printed shapes are `(4, 3)`
- [ ] You did not expect a magma plot today

### Step 3 — Walk `lab_qkv` line by line

Open `later_labs.py`. Find `lab_qkv`.

1. `rng = np.random.default_rng(1)` — seed **1** (ml-42 used 0). Different random `X`.
2. `X = rng.normal(size=(4, 3))` — four tokens, three numbers.
3. `Wq = rng.normal(size=(3, 3))` — query recipe.
4. `Wk = rng.normal(size=(3, 3))` — key recipe.
5. `Wv = rng.normal(size=(3, 3))` — value recipe.
6. `Q, K, V = X @ Wq, X @ Wk, X @ Wv` — three mixes. Each is `(4, 3)` because `(4, 3) @ (3, 3) → (4, 3)`.
7. `print("Q query notebook shape", Q.shape, "K key", K.shape, "V value", V.shape)` — line 1 of stdout.
8. `scale = np.sqrt(3)` — **√3**, because the notebook width is 3. This is the **d** in “scaled dot-product attention.”
9. `A = np.exp(Q @ K.T / scale)` then `A = A / A.sum(1, keepdims=True)`
   - `K.T` is `(3, 4)`
   - `Q @ K.T` is `(4, 4)` scores
   - divide by √3
   - exp / row-sum = softmax (without max-subtract)
10. `out = A @ V` — `(4, 4) @ (4, 3) → (4, 3)`
11. `print("mixed values shape", out.shape)` — line 2 of stdout

Say it as Maya:

> “I score my **query** against everyone’s **keys**, turn scores into who-I-read weights, then mix their **values**.”

> **Tip:** `/ scale` is **not** a learning rate. Large `d` makes dots huge; softmax then picks a single winner too hard. Dividing by √d calms that. Here d=3 is already small; the formula still matches the papers.

> **Watch out:** `A.sum(1, keepdims=True)` — axis **1** is “along the keys.” If you summed axis 0, you would normalize the wrong direction.

### Step 4 — Confirm √3 and row sums

Why now: shapes you already have; scale and softmax you should hear from Python.

```bash
python -c "
import numpy as np
rng = np.random.default_rng(1)
X = rng.normal(size=(4, 3))
Wq = rng.normal(size=(3, 3))
Wk = rng.normal(size=(3, 3))
Wv = rng.normal(size=(3, 3))
Q, K, V = X @ Wq, X @ Wk, X @ Wv
scale = np.sqrt(3)
A = np.exp(Q @ K.T / scale)
A = A / A.sum(1, keepdims=True)
out = A @ V
print('shapes', Q.shape, K.shape, V.shape, out.shape)
print('sqrt3', scale)
print('A row sums', A.sum(1))
"
```

- `-c` means “run this code string and exit.”
- Draw `Wq`, `Wk`, `Wv` in **that order** after `X` so the RNG stream matches `lab_qkv`.

**Expect:**

```text
shapes (4, 3) (4, 3) (4, 3) (4, 3)
sqrt3 1.7320508075688772
A row sums [1. 1. 1. 1.]
```

- [ ] `sqrt3` starts `1.732`
- [ ] `A` rows sum to 1 like ml-42

---

## How it works (deeper)

Why three matrices, not one?

- If Q=K=V=X (ml-42), a token that is **long** always matches **itself** (C’s 0.94). Splitting lets a token **query** for “damage words” while its **value** still carries “refund policy.”
- `Wq`/`Wk`/`Wv` are the knobs training would nudge. This lab leaves them **random**. Same honesty as ml-33: **shape** of the recipe, not a trained reader.

Encoder vs decoder (preview of ml-44):

- **Encoder** attention: every ticket token may look at every ticket token (this lab’s 4×4).
- **Decoder** attention when **writing**: you only look at tokens **already written**, plus the encoder. Not coded here.

Tiny GPT (later) stacks this block many times. You already own one block’s arithmetic.

---

## Common pitfalls

1. **`ModuleNotFoundError`.** `source .venv/bin/activate` in `project/ml_playground`.
2. **You expected the 4×4 print.** That was `attn`. `qkv` prints **shapes**.
3. **You thought `(4, 3)` meant 4×3 attention.** Attention `A` is 4×4; it is unprinted.
4. **`sqrt(3)` vs `sqrt(4)`.** Scale uses **channel size 3**, not token count 4.
5. **Wrong seed.** Seed 1 is not seed 0. Shapes still `(4, 3)` either way.

---

## Knowledge check

Answer from the two print lines and the walk.

1. What shapes does the lab print for Q, K, V, and mixed values?
2. Write `Q` in terms of `X` and `Wq`.
3. Write `A` as softmax of what (include the scale)?
4. Write `out` in terms of `A` and `V`.
5. What is `np.sqrt(3)` numerically (first four digits are enough)?

<details>
<summary>Answers</summary>

1. All `(4, 3)`.
2. `Q = X @ Wq`
3. `A = softmax(Q @ K.T / sqrt(3))` (lab: `exp` then divide by row sum).
4. `out = A @ V`
5. `1.732…` (`1.7320508075688772`)

</details>

---

## Recap

- **You printed** Q/K/V and mixed values, all `(4, 3)`.
- **You understand** query-key scores, √d scale, then mix values.
- **Next** you stamp **positions** so “first token” ≠ “last token,” and contrast encoder vs decoder.

Next: `ml-44-positions-encoder-decoder`

---

## Stretch goal

In `lab_qkv`, change `size=(4, 3)` to **`size=(4, 8)`** and every `(3, 3)` weight to **`(8, 8)`**, and `np.sqrt(3)` to **`np.sqrt(8)`**. Save. Rerun:

```bash
python later_labs.py qkv
```

- **Expect:** prints **`(4, 8)`** for Q, K, V, and mixed values. Token count stays 4; notebook width grew.
- Put **3** back everywhere (`X`, three `W`s, `sqrt(3)`) when you are done so this lesson’s `(4, 3)` still matches.

---

## Feedback

Could you redo this lab from memory? Note the **lesson id** (`ml-43`), the **step number**, what you **expected**, and what you **saw** (traceback or printout).
