# ml-23 — Bag of words

**Level:** Absolute beginner  
**Time:** ~50 minutes  
**Prerequisites:** ml-22; Python 3.14.6, numpy 2.5.2, sklearn 1.9.0 from the ml-00 venv  
**Lab outcome:** You turn ten Meridian tickets into a count table and read the first row’s bag

---

## At a glance

A **bag of words** is a recipe that throws away order and **counts** how often each vocab token appears.

“Bag” means: you dumped the words on the table. `where is my order` and `order is where my` become the same counts.

By the end you can:

- read the first twelve vocab names: `1048001`, `1048292`, `and`, `any`, …
- read the first row bag (zeros and ones) and name which tokens are the ones
- explain why `MC-1048292` became **two** columns (`mc` and `1048292`) and why `'6'` vanished

You will run `later_labs.py bow` and walk `lab_bow`.

---

## Why this matters

Maya has ten toy tickets in `TICKET_TEXTS` (WISMO, refund, damage). Before a classifier can vote (ml-25), each sentence must become a **row of numbers**.

Counting is the honest first recipe. It is not “AI reading.” It is tally marks.

If you skip this lab, TF-IDF looks like a new religion. Tonight it is the same table with fancier weights.

---

## Concept primer

| Word | Plain English | In Maya’s warehouse |
| --- | --- | --- |
| **Vectorizer** | A recipe from text → numbers | sklearn `CountVectorizer` |
| **Bag of words** | Counts, no order | First ticket has a 1 under `where`, `order`, `1048292`, … |
| **Document** | One text you vectorize | One customer ticket |
| **Feature / column** | One vocab token | Column `refund` is “how many times `refund` appeared” |
| **Sparse row** | Mostly zeros | 57 vocab columns; first ticket uses **10** of them |
| **Default tokenizer** | sklearn’s split rule | Lowercase; chunks of 2+ letters/digits; hyphens split |

```text
10 tickets  →  CountVectorizer.fit_transform  →  10 × 57 count table
                     ↑
              learns vocab from these tickets, then counts
```

> **Tip:** `fit` = learn the vocab. `transform` = count with that vocab. `fit_transform` does both on the same list. New tickets later should only `transform` (ml-07 leakage still applies).

> **Watch out:** This splitter is **not** ml-22’s `lower().split()`. Hyphens break. One-character tokens drop. The digit `6` from “6 days” is gone.

---

## Setup (short)

You already made the virtual environment in **ml-00**. Reuse it. Do not recreate it. Do not pip-install anything new.

### Step 1 — Enter the playground and turn the island on

Why now: `later_labs.py` imports `TICKET_TEXTS` from the current folder.

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

### Step 2 — Run the bag-of-words lab

Why this command now: you need the real vocab head and the first row, not a sketch.

```bash
python later_labs.py bow
```

`bow` is a lab name, not a flag.

**It worked when** you see (wrapped the same way on your screen):

```text
vocab ['1048001' '1048292' 'and' 'any' 'arrived' 'attached' 'back' 'been'
 'bottle' 'box' 'carton' 'corner'] ...
first row bag [[0 1 0 0 0 0 0 1 0 0 0 0 0 1 0 0 0 0 0 0 1 0 1 1 0 0 0 1 0 0 1 0 0 0 1 0
  0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0]]
```

Read the vocab head left to right:

1. `1048001` — from ticket “eta for MC-**1048001** thanks”
2. `1048292` — from Maya’s first ticket’s order id
3. `and`
4. `any`
5. `arrived`
6. `attached`
7. `back`
8. `been`
9. `bottle`
10. `box`
11. `carton`
12. `corner`

Alphabetical. Numbers sort before letters. That is why ids lead the list.

The first row is ticket 0: `where is my order MC-1048292 it has been 6 days`.

- [ ] Vocab starts `1048001`, `1048292`, `and`, `any`
- [ ] First row is a long 0/1 vector, not the original sentence

### Step 3 — Decode the first row’s ones

The bag has **57** columns (full vocab). The first row has **10** ones. Those tokens are:

`1048292`, `been`, `days`, `has`, `is`, `it`, `mc`, `my`, `order`, `where`

Compare to ml-22’s crude tokens:

| ml-22 `split()` | CountVectorizer |
| --- | --- |
| `mc-1048292` (one token) | `mc` **and** `1048292` (two columns) |
| `6` kept | `6` **dropped** (default pattern wants 2+ characters) |
| `where` … `days` | same words, plus the split id |

The ones in the printed vector sit at those ten columns. Everything else in row 0 is 0: this ticket never said `smashed` or `refund`.

- [ ] You can name all ten nonzero tokens
- [ ] You can explain where `6` went

### Step 4 — Walk `lab_bow` (do not paste blindly)

Open `later_labs.py`. Find `lab_bow`. Open `TICKET_TEXTS` in `meridian_data.py`.

1. `texts = [t for t, _ in TICKET_TEXTS]` — ten sentences. The `_` throws away `wismo` / `refund` / `damage`. Counts do not use labels.
2. `v = CountVectorizer()` — default sklearn 1.9.0: lowercase on, token pattern `two or more letter-or-digit characters`, unigrams only.
3. `X = v.fit_transform(texts)` — learn vocab from all ten, then count. `X` is a **sparse** matrix (store the nonzero counts only).
4. `v.get_feature_names_out()[:12]` — first twelve column names, then `...`
5. `X[0].toarray()` — densify **row 0** so you can see the zeros. Do not densify a million-row matrix on a laptop; ten tickets is fine.

There is no extra CLI flag. `bow` is just the lab name.

> **Tip:** `[:12]` is a Python slice: “first twelve names.” It is not an sklearn flag. The `...` is printed by the lab so you know the list continues to 57.

> **Watch out:** `CountVectorizer` will happily count `the`, `is`, `it`. Those are real columns. They are weak clues. TF-IDF (ml-24) down-weights words that show up in every ticket.

### Step 5 — Mini experiment (do it)

In `lab_bow`, change **one number**: `[:12]` to `[:5]`.

Save. Run:

```bash
python later_labs.py bow
```

**Expect:** vocab print stops after `1048001`, `1048292`, `and`, `any`, `arrived`. The first row bag is unchanged.

Put `[:12]` back when you are done.

- [ ] You saw a shorter vocab head
- [ ] You put 12 back

---

## How it works (deeper)

For each ticket, the recipe is:

```text
lowercase
cut into tokens of 2+ [A-Za-z0-9_] chunks  (hyphen is a cutter)
for each vocab column:
    write how many times that token appeared
```

Ticket 0 used each of its ten tokens **once**, so the bag is 0/1, not 2s and 3s. A ticket that said `refund refund` would put **2** in the `refund` column.

Order is gone on purpose. That is the bug you will meet in ml-32 (`late smashed` vs `smashed late`). Tonight, counts are enough to *see* the table.

The ten labels sit unused. Bag-of-words is still just features. The classifier comes in ml-25.

---

## Common pitfalls

1. **`ModuleNotFoundError`.** Venv off. Redo Step 1.
2. **Wrong folder.** `cd project/ml_playground`.
3. **You expected `mc-1048292` as one column.** Hyphen splits. Columns are `mc` and `1048292`.
4. **You looked for `'6'` in the vocab.** Default token pattern drops one-character tokens.
5. **You thought the first row’s first `1` was `1048001`.** Column 0 is `1048001` and row 0 has **0** there. The first `1` is column `1048292`.
6. **You densified `X` in a huge corpus.** This lab’s `toarray()` is safe because n=10. Production logs are sparse for a reason.

---

## Knowledge check

Answer from the printout and Step 3.

1. What are the first four vocab names?
2. How many columns are in the bag (vocab size), and how many ones are in row 0?
3. Which ten tokens are the ones in the first row?
4. Why is `1048001` a column if ticket 0 never said it?
5. Did `lab_bow` use the `wismo` / `refund` / `damage` labels?

<details>
<summary>Answers</summary>

1. `1048001`, `1048292`, `and`, `any`.
2. 57 columns; 10 ones in row 0.
3. `1048292`, `been`, `days`, `has`, `is`, `it`, `mc`, `my`, `order`, `where`.
4. Vocab is learned from **all ten** tickets. Ticket 6 mentions `MC-1048001`. Every row gets that column; most rows put 0 there.
5. No. The `_` in `[t for t, _ in TICKET_TEXTS]` throws the labels away.

</details>

---

## Recap

- **You built** a 10 × 57 count table and read row 0’s bag.
- **You understand** bag = counts, no order; sklearn’s splitter ≠ `split()`; vocab is global.
- **Next** you will weight rare phrases and count **two-word** chunks (ngrams).

Next: `ml-24-tfidf-ngrams`

---

## Stretch goal

In `lab_bow`, change `CountVectorizer()` to `CountVectorizer(min_df=2)`. `min_df=2` means “drop tokens that appear in only one ticket.”

Rerun.

- **Expect:** shorter vocab; order ids that appear once may vanish. Row 0’s bag length changes.
- Put `CountVectorizer()` back (no `min_df`) when you are done.

(`min_df` is a constructor argument, not a CLI flag.)

---

## Feedback

Could you redo this lab from memory? Note the **lesson id** (`ml-23`), the **step number**, what you **expected**, and what you **saw**.
