# ml-25 — Naive Bayes tickets

**Level:** Absolute beginner  
**Time:** ~55 minutes  
**Prerequisites:** ml-24; Python 3.14.6, numpy 2.5.2, sklearn 1.9.0 from the ml-00 venv  
**Lab outcome:** You fit a TF-IDF + MultinomialNB pipeline on ten toy tickets and read three Maya-style guesses

---

## At a glance

**Naive Bayes** is a classifier: it turns a bag of word weights into a **label guess** plus **probabilities**.

**Naive** means: it pretends words are independent (“`crushed` does not change what `carton` means”). That is false in English and often **good enough** on short tickets.

By the end you can:

- name sklearn’s class order: **alphabetical** `damage`, `refund`, `wismo`
- read `where is my box -> wismo [0.283 0.271 0.445]`
- read `I want my money back -> refund [0.242 0.41 0.347]`
- read `the carton is crushed -> damage [0.385 0.308 0.307]`
- say the pipeline is **TfidfVectorizer then MultinomialNB** on **ten** toy sentences

You will run `later_labs.py nb` and walk `lab_nb`.

---

## Why this matters

Maya’s queue is not a scatter plot tonight. It is sentences. She needs a first-pass sort: WISMO vs refund vs damage, before a human (or an ADK tool call) spends time.

Ten labeled examples are a toy. They are enough to *see* the pipeline. They are not enough to ship to production.

If you skip this lab, “the model predicted wismo” is a black box. Tonight you can point at the three probabilities and the alphabetical columns.

---

## Concept primer

| Word | Plain English | In Maya’s warehouse |
| --- | --- | --- |
| **Label / class** | The bucket you want | `wismo`, `refund`, `damage` |
| **Classifier** | Recipe from features → class | Naive Bayes on TF-IDF rows |
| **Pipeline** | Glue: step1 then step2 | `TfidfVectorizer` then `MultinomialNB` |
| **MultinomialNB** | Bayes on count-like features | Right sklearn neighbor for word tables |
| **classes_** | sklearn’s column order for `predict_proba` | **Alphabetical:** damage, refund, wismo |
| **predict** | The winning class | `wismo` for “where is my box” |
| **predict_proba** | Three numbers that sum to ~1 | `[0.283 0.271 0.445]` |

```text
ten (text, label) pairs
        →  TfidfVectorizer  →  numbers
        →  MultinomialNB    →  class + three probabilities
```

> **Tip:** Always read `predict_proba` with `classes_`. Index 0 is **not** “the first label you thought of.” It is `damage` here because `d` < `r` < `w`.

> **Watch out:** These three test questions are **not** in the ten training sentences (close, but not copies). A 0.445 is a lean, not a court verdict.

---

## Setup (short)

You already made the virtual environment in **ml-00**. Reuse it. Do not recreate it. Do not pip-install anything new.

### Step 1 — Enter the playground and turn the island on

Why now: `lab_nb` imports `TICKET_TEXTS` from the current folder.

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

### Step 2 — Run the naive Bayes lab

Why this command now: the three printed lines *are* the knowledge check later. You need them on your screen.

```bash
python later_labs.py nb
```

`nb` is a lab name, not a flag.

**It worked when** you see:

```text
where is my box -> wismo [0.283 0.271 0.445]
I want my money back -> refund [0.242 0.41  0.347]
the carton is crushed -> damage [0.385 0.308 0.307]
```

Map every bracket to **damage, refund, wismo** in that order:

| Query | Winner | damage | refund | wismo |
| --- | --- | --- | --- | --- |
| where is my box | **wismo** | 0.283 | 0.271 | **0.445** |
| I want my money back | **refund** | 0.242 | **0.410** | 0.347 |
| the carton is crushed | **damage** | **0.385** | 0.308 | 0.307 |

No plot. Close nothing. Read the numbers.

- [ ] All three winners match the table
- [ ] You can say “index 2 is wismo” without guessing

### Step 3 — Look at the ten toy sentences

Open `meridian_data.py`. Find `TICKET_TEXTS`. There are **exactly ten** pairs:

| Text (short) | Label |
| --- | --- |
| where is my order MC-1048292 it has been 6 days | wismo |
| package still not here tracking frozen | wismo |
| I want a refund the vase arrived smashed | refund |
| please refund this late gift it missed the party | refund |
| box was crushed corner torn item dented | damage |
| outer carton wet and the bottle leaked | damage |
| eta for MC-1048001 thanks | wismo |
| money back now this is unacceptable | refund |
| photo attached of crushed foam | damage |
| any scan since yesterday | wismo |

Four wismo, three refund, three damage. Tiny. The queries in Step 2 rhyme with these but are not copies (`box` vs `order`, `money back` vs `refund` + `money back`, `carton` + `crushed`).

- [ ] You counted ten rows
- [ ] You saw why “where is my box” can still lean wismo

### Step 4 — Walk `lab_nb` (do not paste blindly)

Open `later_labs.py`. Find `lab_nb`.

1. `texts = [t for t, _ in TICKET_TEXTS]` — the ten strings.
2. `y = [lab for _, lab in TICKET_TEXTS]` — the ten labels. **Now** the labels are used.
3. `make_pipeline(TfidfVectorizer(), MultinomialNB())` — vectorizer first, Bayes second. Default TF-IDF is unigrams only (`ngram_range` is not set, so `(1, 1)`).
4. `.fit(texts, y)` — learn vocab + IDF from the ten texts, then learn class word weights from `y`.
5. Loop three queries. For each:
   - `clf.predict([q])[0]` — winning class (needs a **list**; one string would look like a list of characters — a famous foot-gun).
   - `clf.predict_proba([q])[0]` — three probabilities, rounded to 3 decimals.

sklearn 1.9.0 stores classes in **sorted** order. Confirm anytime with:

```bash
python -c "
from sklearn.pipeline import make_pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from meridian_data import TICKET_TEXTS
texts = [t for t,_ in TICKET_TEXTS]
y = [lab for _,lab in TICKET_TEXTS]
clf = make_pipeline(TfidfVectorizer(), MultinomialNB()).fit(texts, y)
print(clf.named_steps['multinomialnb'].classes_)
"
```

`-c` means “run this string as Python.”

**Expect:**

```text
['damage' 'refund' 'wismo']
```

> **Tip:** `make_pipeline` names steps from the class: `tfidfvectorizer`, `multinomialnb`. That is why `named_steps['multinomialnb']` works.

> **Watch out:** `predict(['where is my box'])` is correct. `predict('where is my box')` would treat each letter as a document. The lab already wraps `[q]`. Do not “simplify” that.

### Step 5 — Mini experiment (do it)

In `lab_nb`, change **one number**: `MultinomialNB()` to `MultinomialNB(alpha=10)`.

`alpha` is Laplace smoothing: add a little count to every word/class so unseen words do not zero a probability. Default is `1.0`. **10** is a heavy smooth — probabilities get closer together.

Save. Run:

```bash
python later_labs.py nb
```

**Expect:** the same winners are likely, but the three numbers in each bracket move toward each other (less confident). Put `MultinomialNB()` back when you are done.

- [ ] You saw the probabilities flatten
- [ ] You put the default `MultinomialNB()` back

---

## How it works (deeper)

Bayes, in one warehouse sentence:

> “Given these word weights, how common is this ticket among **damage** tickets vs **refund** vs **wismo**?”

**Naive** part: multiply per-word clues as if words did not help each other. `carton` and `crushed` both nudge damage even if the pair is the real phrase.

```text
for each class in [damage, refund, wismo]:
    score = prior(class) × product of word likelihoods
then:
    turn scores into three probabilities that sum to 1
    predict = argmax
```

`MultinomialNB` is the sklearn tool that does this on TF-IDF / count rows. You did not write the product. You still have to read `classes_`.

This is **not** a neural net. No ReLU. No backprop. Ten sentences. CPU. Maya can still override every guess.

---

## Common pitfalls

1. **`ModuleNotFoundError`.** Venv off. Redo Step 1.
2. **Wrong folder.** `cd project/ml_playground`.
3. **You mapped `[0.283 0.271 0.445]` as wismo, refund, damage.** Reverse of sklearn. Alphabetical: damage, refund, wismo.
4. **You thought 0.445 meant 44.5% of customers.** It is this model’s lean on **this** string, trained on **ten** toys.
5. **You passed a raw string to `predict`.** Always a list of documents: `[q]`.
6. **You shipped this to the refund path.** Toy data. Use it to learn the pipeline, not to move money.

---

## Knowledge check

Answer from the printout and `classes_`.

1. What is sklearn’s class order, and why that order?
2. For “where is my box,” what is the winner and the three probabilities?
3. For “I want my money back,” which number is the refund probability?
4. For “the carton is crushed,” which class wins, and by how much vs the second place?
5. How many training sentences are in `TICKET_TEXTS`, and what are the two pipeline steps?
6. If a probability vector is `[0.385 0.308 0.307]`, which index is wismo?

<details>
<summary>Answers</summary>

1. `damage`, `refund`, `wismo` — alphabetical (`classes_`).
2. wismo; `[0.283 0.271 0.445]` = damage 0.283, refund 0.271, wismo 0.445.
3. **0.41** (middle slot). The print may show `0.41` with extra space before `0.347`.
4. damage at 0.385; refund is second at 0.308 (gap 0.077). wismo is 0.307.
5. Ten. `TfidfVectorizer` then `MultinomialNB`.
6. Index 2 (0.307).

</details>

---

## Recap

- **You built** a ten-ticket intent classifier and read three probability rows.
- **You understand** naive = independent words; `classes_` is alphabetical; pipeline = TF-IDF then NB.
- **Next** you will put words on a 2D map from **who sits with whom** (toy co-occur, not RAG).

Next: `ml-26-word-vectors`

---

## Stretch goal

In the `for q in (...)` tuple, you could change a string — that is not a number. Change `MultinomialNB(alpha=10)` from Step 5 if you already reverted, **or** change rounding: `np.round(..., 3)` to `np.round(..., 2)`.

Rerun.

- **Expect:** same winners; probabilities print as two decimals (e.g. wismo `0.45` instead of `0.445`).
- Put `3` back when you are done.

---

## Feedback

Could you redo this lab from memory? Note the **lesson id** (`ml-25`), the **step number**, what you **expected**, and what you **saw**.
