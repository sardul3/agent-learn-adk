# ml-26 — Word vectors (toy)

**Level:** Absolute beginner  
**Time:** ~50 minutes  
**Prerequisites:** ml-25; Python 3.14.6, numpy 2.5.2, sklearn 1.9.0 from the ml-00 venv  
**Lab outcome:** You plot nine warehouse words from a co-occurrence matrix and PCA — not Pack D RAG embeddings

---

## At a glance

A **word vector** is a short list of numbers that stands for a word. Nearby numbers ≈ words that play similar roles.

This lab does **not** download GloVe, Word2Vec, or a Gemini embedding. It builds a tiny **who-sits-with-whom** table from six hand-written pairs, then **PCA(2)** for a picture.

By the end you can:

- list the six pairs (refund–money, smash–dented, where–order, …)
- list the nine-word vocab in sorted order
- say why `dented` and `crushed` land on top of each other
- say in one breath: **this is not Pack D RAG**

You will run `later_labs.py wvec` and walk `lab_vectors_words`.

---

## Why this matters

Maya hears `smashed`, `dented`, `crushed` as the same damage family. `refund` and `money` travel together. `where` travels with `order` and `tracking`.

Bag-of-words (ml-23) treats those as unrelated columns. A vector space is how later models *share* meaning across spelling variants.

If you skip this lab, “embedding” in Pack D feels like a vendor noun. Tonight it is a 9 × 9 tally plus a rotation you already met in ml-20.

---

## Concept primer

| Word | Plain English | In Maya’s warehouse |
| --- | --- | --- |
| **Co-occur** | Two words appear as a pair in the toy list | `refund` with `money`; `smash` with `crushed` |
| **Co-occurrence matrix** | Rows and columns are words; a cell is “paired how many times” | 9 × 9 table `M` |
| **Word vector (here)** | One row of `M` (who this word sits with) | `smash`’s row has 1s under `dented` and `crushed` |
| **PCA(2)** | Rotate those rows into two plot axes | Same idea as ml-20, now on words |
| **RAG embedding** | A different factory: a language model’s vector, used to fetch policy | Pack D / Lesson 18 — **not this file** |

```text
six pairs  →  symmetric 9×9 counts  →  PCA(2)  →  labeled dots
```

> **Tip:** If two words have the **same** neighbors, their rows are equal, so PCA puts them on the **same** dot. That is why `dented` and `crushed` overlap.

> **Watch out:** `wvec` is the **lab name** in `later_labs.py`. The function is `lab_vectors_words`. Do not hunt for a file named `wvec.py`.

---

## Setup (short)

You already made the virtual environment in **ml-00**. Reuse it. Do not recreate it. Do not pip-install anything new. Do not pip-install torch or an embedding model.

### Step 1 — Enter the playground and turn the island on

Why now: `later_labs.py` lives in this folder. The lab does not even import `TICKET_TEXTS`; the pairs are inline.

```bash
cd project/ml_playground
source .venv/bin/activate
```

- `cd` means “change directory.” There is no dash-flag here.
- `source` runs `activate` in **this** shell so `python` points at the island.

**It worked when** your prompt shows `(.venv)` and this prints the pinned stack:

```bash
python --version
python -c "import numpy, sklearn; print(numpy.__version__); print(sklearn.__version__)"
```

```text
Python 3.14.6
2.5.2
1.9.0
```

- `--version` prints the interpreter version.
- `-c` means “run the next string as Python.”

---

## Hands-on

### Step 2 — Run the word-vector lab

Why this command now: the picture is how you *feel* “nearby meaning.” The terminal is quiet.

```bash
python later_labs.py wvec
```

`wvec` is a lab name, not a flag.

**It worked when** a scatter plot opens titled `ml-26: nearby meaning ≈ nearby dots (toy)`, with nine words labeled on dots.

What to stare at:

- **`dented` and `crushed`** sit on the **same** point (both only pair with `smash`)
- **`money` and `back`** sit together (both only pair with `refund`)
- **`order` and `tracking`** sit together (both only pair with `where`)
- **`refund`**, **`smash`**, **`where`** sit apart — they are the three hubs

Close the window after you can point at the damage cluster vs the refund cluster vs the WISMO cluster.

- [ ] You found the overlapping `dented` / `crushed` label
- [ ] You did not call this “the RAG index”

### Step 3 — Write the six pairs on the plot’s story

The pairs in `lab_vectors_words` are exactly:

1. `refund` — `money`
2. `refund` — `back`
3. `smash` — `dented`
4. `smash` — `crushed`
5. `where` — `order`
6. `where` — `tracking`

Sorted vocab (nine words):

```text
back, crushed, dented, money, order, refund, smash, tracking, where
```

Three families, three hubs. No sentence from `TICKET_TEXTS` entered this matrix.

- [ ] You can recite the six pairs
- [ ] Vocab has 9 strings, not 10 tickets

### Step 4 — Walk `lab_vectors_words` (do not paste blindly)

Open `later_labs.py`. Find `lab_vectors_words`.

1. `pairs = [(...), ...]` — the six tuples above.
2. `vocab = sorted({w for p in pairs for w in p})` — unique words, alphabetical.
3. `idx = {w: i for i, w in enumerate(vocab)}` — word → row/column number.
4. `M = np.zeros((len(vocab), len(vocab)))` — 9 × 9 zeros.
5. For each pair `(a, b)`: `M[idx[a], idx[b]] += 1` and `M[idx[b], idx[a]] += 1`. **Symmetric.** Sitting-with is two-way in this toy.
6. `z = PCA(2).fit_transform(M)` — each **row** of `M` is that word’s vector. PCA paints 2D.
7. `ax.scatter` then `ax.text` so you can read the words. No color legend. No `true_group`.

The matrix idea, for `smash`:

```text
smash row: 1 under crushed, 1 under dented, 0 elsewhere
```

`crushed` row: 1 under `smash` only. `dented` row: 1 under `smash` only. Same pattern → same PCA coordinates `[-0.08, -0.028]` on this run.

> **Tip:** `+= 1` is the whole “training.” There is no neural net. Change a pair, the dots move.

> **Watch out:** Pack D RAG embeddings are produced by a **different** model (policy retrieval in the ADK track). They live in another folder and another lesson. If you tell Maya “we embedded tickets like ml-26,” you are mixing factories.

### Step 5 — Mini experiment (do it)

In the loop, change **one number**: `+= 1` to `+= 5` on **both** lines (`M[idx[a], idx[b]]` and the symmetric line).

Save. Run:

```bash
python later_labs.py wvec
```

**Expect:** the *shape* of families stays (still the same who-sits-with-whom pattern). Distances may stretch because every count is 5×. Put `+= 1` back on both lines when you are done.

If you only change one of the two `+=` lines, the matrix stops being symmetric — a useful gotcha. For the stretch, change both the same way, then revert both.

- [ ] You reran and still saw three families
- [ ] You put `+= 1` back

---

## How it works (deeper)

Distributional idea in one line: **words that share neighbors get similar rows.**

```text
refund's neighbors: money, back
smash's neighbors:  dented, crushed
where's neighbors:  order, tracking
```

PCA then does what ml-20 did: rotate so you can see the spread on a laptop.

Real word vectors (Word2Vec, GloVe, modern embeddings) do this on **billions** of pairs with fancier scoring. The geometry lesson is the same. The factory in this repo for *policy search* is Pack D RAG, not `lab_vectors_words`.

---

## Common pitfalls

1. **`ModuleNotFoundError`.** Venv off. Redo Step 1.
2. **Wrong folder.** `cd project/ml_playground`.
3. **Plot never opens.** `unset ML_HEADLESS` on a laptop.
4. **You thought the dots came from `TICKET_TEXTS`.** They came from six hardcoded pairs.
5. **You called this RAG.** RAG fetches documents with a language-model embedding. This is a 9 × 9 count matrix.
6. **You expected `smashed` the adjective.** The toy word is `smash` (verb hub). Different string, different row.

---

## Knowledge check

Answer from the pairs list and the plot.

1. How many pairs, and how many unique words?
2. Why do `dented` and `crushed` overlap?
3. What two words sit with `refund`?
4. Does `PCA(2)` here use `true_group` or ticket labels?
5. Is this the same vector you would store in a Pack D RAG index?

<details>
<summary>Answers</summary>

1. Six pairs; nine words.
2. Both only co-occur with `smash`, so their rows of `M` match, so PCA maps them to the same 2D point.
3. `money` and `back`.
4. No. There is no label column. PCA fits on `M` only.
5. No. Different factory, different dimension, different purpose (toy geometry vs policy retrieval).

</details>

---

## Recap

- **You built** a co-occurrence map of nine warehouse words.
- **You understand** similar neighbors → similar rows → nearby dots; this is not RAG.
- **Next** you will mix two numbers with weights inside **one neuron**.

Next: `ml-27-neuron-layer`

---

## Stretch goal

If you already reverted Step 5, change both `+= 1` lines to `+= 2`. Rerun.

- **Expect:** three families remain; axis scale may change.
- Put `+= 1` back on both lines.

---

## Feedback

Could you redo this lab from memory? Note the **lesson id** (`ml-26`), the **step number**, what you **expected**, and what you **saw**.
