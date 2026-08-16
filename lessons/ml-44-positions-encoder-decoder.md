# ml-44 — Positions, encoder, decoder

**Level:** Absolute beginner  
**Time:** ~50 minutes  
**Prerequisites:** ml-43; venv from **ml-00**  
**Lab outcome:** You open an **8×4** sine heatmap of **position tags**, then say what an **encoder** reads vs what a **decoder** writes — and what happens if you **skip** positions

---

## At a glance

Attention (ml-42, ml-43) does not know **order** unless you **tell** it. A **position tag** is a small extra vector that means “I am token 0 / 1 / 2 …” so `late smashed` cannot collapse into `smashed late` (ml-32) again.

By the end you can explain, without hand-waving:

- the plot is **8 positions × 4 channels** of `sin`
- **encoder** reads **all** tokens (with those tags) in one go
- **decoder** **writes one token at a time** (next letter, then the next)
- skip positions → you are back in a **bag**

You will run `lab_pos` and walk the sine formula. No numeric stdout.

---

## Why this matters

Maya’s location code `A1-B2` is not a pile of characters. **A** in slot 0 is zone. **A** in slot 3 would be a different story. ml-33 kept order with a running `h`. Transformers keep order by **adding a tag** to each slot, then mixing with attention.

If you skip positions, swapping two warehouse words does not change `X`’s **multiset** of rows — attention can still run, but it has no “first vs last.” That is a bag with extra steps.

```
token vectors  +  position tags  →  encoder can tell slot 0 from slot 7
token vectors  +  nothing        →  bag again
```

---

## Concept primer

| Word | Plain English | In Maya’s warehouse |
| --- | --- | --- |
| **Position** | Which slot in the sequence (0,1,2,…) | First scan vs last scan |
| **Position encoding (PE)** | A tag vector for that slot | 4 numbers per slot here |
| **Sine tag** | `sin(pos / 10000^(i/d))` — a wave whose speed depends on channel `i` | The heatmap |
| **Encoder** | Reads the **whole** ticket (all positions) and mixes | “Understand the request” |
| **Decoder** | **Writes** the reply **one token at a time**, each time looking at what it already wrote (+ the encoder) | “Type the next letter” |
| **Bag** | Counts without order (ml-23, ml-32) | What you get if PE is zeros |

The formula in the file:

```
pe[pos, i] = sin( pos / (10000 ** (i / d)) )
```

- `pos` = 0..7 (rows)
- `i` = 0..3 (columns)
- `d` = 4 (width of the tag)
- `10000` is a **fixed scale** from the original transformer paper, not a learning rate

Row 0 is `sin(0)` = **all zeros**. That is a feature, not a bug: the first slot’s sine tags start at 0.

```
encoder:  look at everyone  (8 tags visible)
decoder:  write token t, then t+1, then t+2   (cannot peek at the future)
```

> **Tip:** Cosine channels (even/odd) appear in the paper. This CPU lab only plots **sin** so the picture stays one formula.

> **Watch out:** The heatmap is **not** attention. It is **only** the tags. No `Q @ K.T` in `lab_pos`.

---

## Setup

Reuse the **ml-00** venv.

### Step 1 — Enter the playground

Why now: `imshow` needs matplotlib; formula needs numpy 2.5.2.

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

Close the plot window when you have counted 8 rows and 4 columns.

```bash
export ML_HEADLESS=1
```

if you have no display. This lab prints **nothing** — without a window you must still open the file and run Step 4’s `-c` to see `pe.shape`. Prefer a laptop.

---

## Hands-on

### Step 2 — Run the position lab

Why this command now: the 8×4 wave picture is the whole demo. If you skip it, “sine heatmap” is a caption.

```bash
python later_labs.py pos
```

- `pos` is a positional lab name (`lab_pos`). Not `--pos`.

**It worked when** a window opens titled **`ml-44: position tags so 'first word' ≠ 'last word'`**.

On the plot (`coolwarm`):

- **8 rows** — positions 0 (top) through 7 (bottom)
- **4 columns** — channels `i = 0,1,2,3`
- top row looks **flat / zero**
- column 0 **oscillates fastest** as you go down (the `i/d` exponent is smallest when `i=0`, so the divisor is closest to 1, so `sin(pos / 1)` = `sin(pos)`)

No stdout. The picture is success.

- [ ] You counted 8 rows and 4 columns
- [ ] You can point at row 0 as “first slot”

### Step 3 — Walk `lab_pos`

Open `later_labs.py`. Find `lab_pos`.

1. `n, d = 8, 4` — **n** positions, **d** tag channels. Heatmap **8×4**.
2. `pos = np.arange(n)[:, None]` — column vector `[[0],[1],…,[7]]`. `[:, None]` adds a length-1 axis so it can broadcast.
3. `i = np.arange(d)[None, :]` — row vector `[[0, 1, 2, 3]]`.
4. `pe = np.sin(pos / (10000 ** (i / d)))` — every cell of the heatmap.
5. `imshow(pe, cmap="coolwarm")` plus the title about first word ≠ last word.

There is **no encoder loop** and **no decoder loop** in this function. The title and this lesson supply that story. The code is **only** the tags.

> **Tip:** `10000 ** (i / d)` for `i=0` is `10000 ** 0 = 1`. For `i=3`, `d=4`, it is `10000 ** 0.75` — a huge divisor, so that channel’s sine **barely** moves across 8 positions. Fast waves vs slow waves: a unique fingerprint per slot.

> **Watch out:** `i / d` in numpy is **float** divide. You want that. Integer `i // d` would be wrong (all zeros for i < d).

### Step 4 — Print the 8×4 numbers

Why now: prove shape and the zero first row without relying on color.

```bash
python -c "
import numpy as np
n, d = 8, 4
pos = np.arange(n)[:, None]
i = np.arange(d)[None, :]
pe = np.sin(pos / (10000 ** (i / d)))
print('pe', pe.shape)
print('row0', np.round(pe[0], 4))
print('col0', np.round(pe[:, 0], 4))
"
```

- `-c` means “run this code string and exit.”

**Expect:**

```text
pe (8, 4)
row0 [0. 0. 0. 0.]
col0 [ 0.      0.8415  0.9093  0.1411 -0.7568 -0.9589 -0.2794  0.657 ]
```

`col0` is `sin(0), sin(1), sin(2), …` in radians. Position 1 ≠ position 7. **That** is “first word ≠ last word.”

- [ ] `pe.shape` is `(8, 4)`
- [ ] Row 0 is zeros
- [ ] Column 0 is not constant

### Step 5 — Encoder vs decoder, said out loud

Fill this in (honestly):

> “The **encoder** reads **all eight** tagged slots at once (attention like ml-43 over the whole ticket). The **decoder** **writes one token at a time** — next character, then the next — and must not peek at future letters. If I **zero** `pe` or never add it, swapping slots does not change the set of vectors: I am back in a **bag**.”

- [ ] You used the words encoder, decoder, bag
- [ ] You tied bag to ml-32, not to a new slogan

---

## How it works (deeper)

How tags enter the net (not coded here, standard picture):

```
X_with_place = X + pe[:T, :]
```

You **add** (or concat) the tag to the token vector, then run QKV on `X_with_place`.

**Encoder block:** for a packing ticket, every word may attend to every word, **including future words in the ticket**. Reading is not typing.

**Decoder block:** when generating “refund approved,” at step 3 the model may look at tokens 0,1,2 of the **reply** plus the encoder memory — not token 4 of a reply that does not exist yet. That **causal** mask is why GPT types left to right.

This lab shows **why** the add is legal: eight rows of `pe` are **different**, so slot identity is a number, not a hope.

Skip positions on purpose and `late smashed` vs `smashed late` can share the same **set** of rows again. Attention still runs. Order dies. That is the ml-32 hole, reopened.

---

## Common pitfalls

1. **Plot never opens.** Unset `ML_HEADLESS` on a laptop. Use Step 4 if you only have SSH.
2. **`ModuleNotFoundError`.** Activate `.venv`.
3. **You called the heatmap attention.** It is sine tags only.
4. **You expected stdout.** `lab_pos` does not print. Silence + window (or `-c` shape) is success.
5. **You said the decoder “reads all like the encoder.”** Decoder **writes** stepwise. Encoder **reads** all.

---

## Knowledge check

Answer from the plot, the `-c` print, and the walk.

1. What is `pe.shape` (`n` and `d`)?
2. What is row 0 of `pe` (the first position)?
3. Copy the first four values of column 0 (rounded as in Step 4), or say they are `sin(0)`…`sin(3)`.
4. In one sentence each: what does an encoder do with tokens, and what does a decoder write?
5. If you skip position tags, which earlier lesson’s failure comes back?

<details>
<summary>Answers</summary>

1. `(8, 4)`
2. `[0, 0, 0, 0]`
3. `0`, `0.8415`, `0.9093`, `0.1411` (`sin` of 0,1,2,3).
4. Encoder reads all tagged tokens together. Decoder writes one token at a time (no future peek).
5. ml-32 — bags / order does not matter; first word equals last word again.

</details>

---

## Recap

- **You viewed** an 8×4 sine position heatmap and printed row 0 / column 0.
- **You understand** tags make slots unique; encoder reads all; decoder writes stepwise; skip PE → bag.
- **Next** a tiny next-character table — the **job** a transformer is paid to do.

Next: `ml-45-tiny-transformer`

---

## Stretch goal

In `lab_pos`, change `n, d = 8, 4` to **`n, d = 8, 8`** (same length, **wider** tags). Save. Rerun:

```bash
python later_labs.py pos
```

- **Expect:** the heatmap is **8×8**. Row 0 is still zeros. Column 0 is still `sin(pos)` (because `i=0` still gives divisor 1). Extra columns are slower waves.
- Put **`4`** back when you are done so this lesson’s 8×4 still matches.

---

## Feedback

Could you redo this lab from memory? Note the **lesson id** (`ml-44`), the **step number**, what you **expected**, and what you **saw** (traceback or plot).
