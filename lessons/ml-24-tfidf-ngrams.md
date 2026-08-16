# ml-24 — TF-IDF and ngrams

**Level:** Absolute beginner  
**Time:** ~50 minutes  
**Prerequisites:** ml-23; Python 3.14.6, numpy 2.5.2, sklearn 1.9.0 from the ml-00 venv  
**Lab outcome:** You fit a unigram+bigram TF-IDF table and read row 0’s 19 nonzero weights

---

## At a glance

**TF-IDF** is a recipe that still turns text into a row of numbers, but it **taxes common words** and **boosts rare ones**.

**Ngrams** are chunks of N tokens in a row. This lab uses `ngram_range=(1, 2)`: single words **and** two-word phrases.

By the end you can:

- read the ngrams sample that starts `'1048001'`, `'1048001 thanks'`, `'1048292'`, `'1048292 it'`, …
- point at `'arrived smashed'` as a bigram from a refund ticket
- say **row0 nonzero 19** and name why 19 ≠ 10

You will run `later_labs.py tfidf` and walk `lab_tfidf`.

---

## Why this matters

Maya’s tickets all say ordinary English: `is`, `the`, `my`. A raw count table (ml-23) treats `the` like `smashed`. That is a bad warehouse priority.

TF-IDF asks: “Does this word show up a lot **in this ticket** (TF) but rarely **across tickets** (IDF)?” `smashed` should outrank `the`.

Two-word phrases catch “arrived smashed” as one clue, not two lonely counts.

---

## Concept primer

| Word | Plain English | In Maya’s warehouse |
| --- | --- | --- |
| **TF (term frequency)** | How much this chunk appears in *this* ticket | `where` appears once in ticket 0 |
| **IDF (inverse document frequency)** | Down-weight chunks that appear in many tickets | `is` is common → smaller IDF |
| **TF-IDF** | TF mixed with IDF (sklearn’s default formula) | Rare damage words get bigger numbers |
| **Unigram** | One token | `thanks`, `smashed` |
| **Bigram** | Two tokens in a row | `1048001 thanks`, `arrived smashed` |
| **ngram_range=(1, 2)** | Keep unigrams **and** bigrams | Constructor on `TfidfVectorizer` |
| **nnz** | Number of nonzeros in a sparse row | Row 0 has **19** |

```text
10 tickets  →  TfidfVectorizer(ngram_range=(1, 2))  →  10 × 112 weighted table
```

> **Tip:** TF-IDF is still a bag. Order inside a bigram is kept (`arrived smashed` ≠ `smashed arrived`). Order of the whole sentence is still mostly gone.

> **Watch out:** `ngram_range` is **not** a CLI flag. It is an argument to `TfidfVectorizer`. `(1, 2)` means min 1, max 2 tokens per chunk.

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

### Step 2 — Run the TF-IDF lab

Why this command now: the sample list and the **19** are the facts this lesson hangs on.

```bash
python later_labs.py tfidf
```

`tfidf` is a lab name, not a flag.

**It worked when** you see:

```text
ngrams sample ['1048001', '1048001 thanks', '1048292', '1048292 it', 'and', 'and the', 'any', 'any scan', 'arrived', 'arrived smashed', 'attached', 'attached of', 'back', 'back now', 'been']
row0 nonzero 19
```

Walk the sample, in order:

| Chunk | Kind | Where it came from |
| --- | --- | --- |
| `1048001` | unigram | `eta for MC-1048001 thanks` |
| `1048001 thanks` | **bigram** | those two tokens in a row (after hyphen split) |
| `1048292` | unigram | Maya’s first order id |
| `1048292 it` | **bigram** | `...1048292 it has been...` |
| `arrived smashed` | **bigram** | `the vase arrived smashed` |
| `any scan` | **bigram** | `any scan since yesterday` |

Alphabetical again. Bigrams sit next to their first word.

- [ ] You found both `'1048001 thanks'` and `'arrived smashed'` in the sample
- [ ] `row0 nonzero` printed **19**

### Step 3 — Why 19, not 10

ml-23’s first row had **10** unigram counts. TF-IDF with (1, 2) keeps those unigrams **and** the adjacent pairs.

Ticket 0 unigrams (10):  
`1048292`, `been`, `days`, `has`, `is`, `it`, `mc`, `my`, `order`, `where`

Ticket 0 bigrams (9):  
`1048292 it`, `been days`, `has been`, `is my`, `it has`, `mc 1048292`, `my order`, `order mc`, `where is`

10 + 9 = **19**. That is `X[0].nnz`.

The digit `6` still dropped, so you do **not** get `been 6` or `6 days`. Crude tokenizer, same as ml-23.

Weights on this row are not all equal. Example: `is` ≈ **0.1994**, `where` ≈ **0.2346**. `is` appears in more tickets, so IDF shrinks it.

- [ ] You can add 10 + 9 and land on 19
- [ ] You know `6` still did not become a bigram partner

### Step 4 — Walk `lab_tfidf` (do not paste blindly)

Open `later_labs.py`. Find `lab_tfidf`.

1. `texts = [t for t, _ in TICKET_TEXTS]` — same ten sentences as ml-23. Labels unused.
2. `TfidfVectorizer(ngram_range=(1, 2))` — unigrams + bigrams, sklearn 1.9.0 default IDF.
3. `X = v.fit_transform(texts)` — 10 rows, **112** columns on this toy (57-ish unigrams plus bigrams; exact mix is 112).
4. `list(v.get_feature_names_out())[:15]` — first fifteen names. The lab wraps them as `ngrams sample`.
5. `X[0].nnz` — count of stored nonzeros in row 0, printed as `row0 nonzero 19`.

`ngram_range=(1, 2)`:

- first number **1** = shortest chunk (single token)
- second number **2** = longest chunk (two tokens)

`(1, 1)` would be “unigrams only,” like a TF-IDF version of ml-23. `(2, 2)` would be “bigrams only” and would drop lonely `smashed`.

> **Tip:** `nnz` is “number of nonzero.” It is a sparse-matrix field, not a flag you pass on the command line.

> **Watch out:** Do not compare these 112 names to Pack D **RAG embeddings**. RAG stores meaning vectors from a language model. This table is still counts-with-taxes plus adjacent pairs. Same warehouse tickets, different factory.

### Step 5 — Mini experiment (do it)

In `lab_tfidf`, change **one number**: `ngram_range=(1, 2)` to `ngram_range=(1, 1)`.

Save. Run:

```bash
python later_labs.py tfidf
```

**Expect:** sample list has no `'1048001 thanks'` or `'arrived smashed'`. `row0 nonzero` drops from **19** toward **10** (unigrams only).

Put `(1, 2)` back when you are done.

- [ ] Row 0 nonzero got smaller
- [ ] You put 2 back

---

## How it works (deeper)

sklearn’s default TF-IDF (simplified):

```text
for each chunk in this ticket:
    tf = count in this ticket, often smoothed / length-normalized
    idf = log( (1 + n_tickets) / (1 + n_tickets_that_contain_chunk) ) + 1
    value = tf * idf
then:
    scale the row so its length is 1  (L2 norm)
```

You do not need to memorize the exact log. You need the story: **common across tickets → smaller**; **specific to this ticket → larger**.

Bigrams are extra columns. They exist only if that pair appeared in the training texts. A new ticket that says `arrived dented` will not light up `arrived smashed` unless you also have a unigram `arrived`.

---

## Common pitfalls

1. **`ModuleNotFoundError`.** Venv off. Redo Step 1.
2. **Wrong folder.** `cd project/ml_playground`.
3. **You thought 19 meant 19 tickets.** It is nonzeros **in row 0**. There are still 10 tickets.
4. **You looked for `6 days` in the sample.** `6` was dropped at tokenize time.
5. **You called TF-IDF “the neural net.”** No hidden layer. It is arithmetic on counts.
6. **You set `ngram_range=(1, 6)` on real mail.** Phrase columns explode. This toy is 112 columns. Real logs get huge fast.

---

## Knowledge check

Answer from the printout you ran.

1. Copy the first four strings in `ngrams sample`.
2. Which sample entry is a damage/refund-style bigram about a broken arrival?
3. What is `row0 nonzero`, and how do you get 19 from 10 + 9?
4. What do the two numbers in `ngram_range=(1, 2)` mean?
5. Did TF-IDF use the ticket labels (`wismo` / `refund` / `damage`)?

<details>
<summary>Answers</summary>

1. `'1048001'`, `'1048001 thanks'`, `'1048292'`, `'1048292 it'`.
2. `'arrived smashed'`.
3. 19. Ten unigrams plus nine adjacent bigrams on ticket 0.
4. Keep chunks of length 1 through length 2 (words and two-word phrases).
5. No. Same `for t, _ in TICKET_TEXTS` pattern as ml-23.

</details>

---

## Recap

- **You built** a TF-IDF table with unigrams and bigrams; row 0 has 19 nonzeros.
- **You understand** IDF taxes common words; ngrams add phrases; this is not RAG embeddings.
- **Next** you will **classify** the ten tickets with naive Bayes.

Next: `ml-25-naive-bayes-tickets`

---

## Stretch goal

In `lab_tfidf`, change `ngram_range=(1, 2)` to `ngram_range=(2, 2)` (bigrams only). Rerun.

- **Expect:** sample starts with two-word chunks; `row0 nonzero` becomes **9** (the pairs only).
- Put `(1, 2)` back when you are done.

---

## Feedback

Could you redo this lab from memory? Note the **lesson id** (`ml-24`), the **step number**, what you **expected**, and what you **saw**.
