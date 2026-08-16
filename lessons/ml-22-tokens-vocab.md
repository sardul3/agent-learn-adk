# ml-22 — Tokens and vocab

**Level:** Absolute beginner  
**Time:** ~45 minutes  
**Prerequisites:** ml-21; Python 3.14.6, numpy 2.5.2, sklearn 1.9.0 from the ml-00 venv  
**Lab outcome:** You split Maya’s first ticket into tokens and a sorted vocab, and you see how crude `lower().split()` is

---

## At a glance

A **token** is a chunk of text you treat as one unit — usually a “word,” sometimes an order id.

A **vocab** (vocabulary) is the **sorted set** of unique tokens. Duplicates vanish. Order of the sentence is gone.

By the end you can:

- read the exact ticket `where is my order MC-1048292 it has been 6 days`
- list the ten tokens after `lower().split()`
- list the ten vocab entries in sorted order
- name two ways this splitter is crude (case, punctuation, the digit `6`)

You will run `later_labs.py tokens` and walk `lab_tokens`. No plot tonight.

---

## Why this matters

Maya’s night queue is sentences, not kilograms. “Where is my order MC-1048292 it has been 6 days” is a **WISMO** ticket: where-is-my-order.

A computer does not “read.” It needs a list of chunks before it can count, weigh, or classify (ml-23–ml-25). If you skip this lab, bag-of-words looks like a library trick. Tonight it is `split`.

---

## Concept primer

| Word | Plain English | In Maya’s warehouse |
| --- | --- | --- |
| **Text / ticket** | The raw sentence | `where is my order MC-1048292 it has been 6 days` |
| **Token** | One chunk after a split rule | `mc-1048292` is one token *with this* splitter |
| **Tokenize** | Apply that split rule | `text.lower().split()` |
| **Vocab** | Unique tokens, usually sorted | `['6', 'been', 'days', ...]` |
| **Case fold** | Force lowercase so `Where` = `where` | `MC-1048292` becomes `mc-1048292` |
| **Crude split** | A rule that is simple and leaky | `split()` on spaces; hyphens stay inside the token |

```text
sentence  →  lowercase  →  split on spaces  →  tokens (list, keeps order, keeps dupes)
                                              →  set → sorted list = vocab
```

> **Tip:** Tokens are a *choice*. Another recipe might split `mc-1048292` into `mc` and `1048292`. sklearn’s CountVectorizer does that in ml-23. Remember this mismatch.

> **Watch out:** Vocab order is **alphabetical**, not sentence order. `'6'` is first because the character `6` sorts before letters.

---

## Setup (short)

You already made the virtual environment in **ml-00**. Reuse it. Do not recreate it. Do not pip-install anything new.

### Step 1 — Enter the playground and turn the island on

Why now: `later_labs.py` imports `TICKET_TEXTS` from `meridian_data.py` in the current folder.

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

### Step 2 — Run the tokens lab

Why this command now: the printout *is* the lesson. If you skip it, you will guess the tokens.

```bash
python later_labs.py tokens
```

`tokens` is a lab name, not a flag.

**It worked when** you see exactly:

```text
text: where is my order MC-1048292 it has been 6 days
tokens: ['where', 'is', 'my', 'order', 'mc-1048292', 'it', 'has', 'been', '6', 'days']
vocab: ['6', 'been', 'days', 'has', 'is', 'it', 'mc-1048292', 'my', 'order', 'where']
```

Count them:

- **10** tokens (the sentence order, including the digit `6`)
- **10** vocab entries (same pieces, sorted, no duplicates — this sentence had no duplicate words)

Notice `MC-1048292` in the text vs `mc-1048292` in the tokens. Lowercase happened. The hyphen **stayed**.

- [ ] Your tokens list matches those ten strings
- [ ] Your vocab starts with `'6'` not `'where'`

### Step 3 — Say one Maya sentence with the chunks

Pick the order id token. Say:

> “The customer wrote **MC-1048292**. After `lower().split()` the computer holds **mc-1048292** as **one** token, not two.”

Then pick `'6'`:

> “**6** is a token because it had spaces around it. It is also a vocab entry. It is not the word ‘six.’”

- [ ] You said both sentences
- [ ] You did not call vocab “the sentence in order”

### Step 4 — Walk `lab_tokens` (do not paste blindly)

Open `later_labs.py`. Find `lab_tokens`. Open `meridian_data.py` and find `TICKET_TEXTS`.

1. `TICKET_TEXTS` is a list of ten `(sentence, label)` pairs. Labels are `wismo`, `refund`, or `damage`. Tonight you ignore the label.
2. `text = TICKET_TEXTS[0][0]` — first pair, first slot: the WISMO sentence above.
3. `toks = text.lower().split()` — lowercase the whole string, then split on **whitespace**. No extra flags. Default `split()` already collapses multiple spaces.
4. `vocab = sorted(set(toks))` — `set` drops duplicates; `sorted` makes a stable list.
5. Three `print`s: raw text, tokens, vocab.

That is the entire recipe. There is no sklearn in this function.

Crude, on purpose:

- **Punctuation:** none in this sentence, so you did not see `days.` vs `days`. A real ticket with a period would glue `days.` as a token.
- **Hyphens:** `mc-1048292` stays one piece here. ml-23’s CountVectorizer will split it.
- **Short tokens:** `'6'` survives `split()`. sklearn’s default token pattern in ml-23 **drops** one-character tokens. The digit will vanish there. Remember that.

> **Tip:** `lower()` does not know English. It only changes A–Z. Order ids that mix letters still fold: `MC-` → `mc-`.

> **Watch out:** `TICKET_TEXTS[0][0]` is “first ticket, the text.” `[0][1]` would be the label `'wismo'`. If you tokenize the label you will get a one-word vocab and a confused Maya.

### Step 5 — Mini experiment (do it)

In `lab_tokens`, change **one number**: `TICKET_TEXTS[0][0]` to `TICKET_TEXTS[2][0]`.

Index **2** is `"I want a refund the vase arrived smashed"` with label `refund`.

Save. Run:

```bash
python later_labs.py tokens
```

**Expect:** different text, tokens like `i`, `want`, `a`, `refund`, … and a vocab that starts with `'a'` (lowercase). Put `[0]` back when you are done so this lesson’s printout still matches.

- [ ] You saw the smashed-vase sentence
- [ ] You put index 0 back

---

## How it works (deeper)

The computer is not “understanding English.” It is cutting a string.

```text
s = "where is my order MC-1048292 it has been 6 days"
s.lower()  →  "where is my order mc-1048292 it has been 6 days"
.split()   →  10 pieces, in order
set(...)   →  the same 10, because none repeated
sorted(...)→  alphabetical, so "6" first
```

**Why sort the vocab?** So column 0 of a later table always means the same token on every machine. Unsorted sets have no stable order.

**Why keep a tokens list and a vocab?** Tokens are the sentence as a sequence (order still there, duplicates still there). Vocab is the inventory of types. Bag-of-words (ml-23) throws away order and counts how often each vocab item appeared.

Ten toy tickets live in `TICKET_TEXTS`. You will use all ten as soon as you vectorize. Tonight you only needed the first.

Preview of ml-23, so tonight’s list does not surprise you tomorrow:

- this lab: `mc-1048292` stays one token; `'6'` stays
- CountVectorizer: hyphen splits to `mc` + `1048292`; `'6'` drops

Same sentence. Two recipes. Both are choices, not “the one true English.”

---

## Common pitfalls

1. **`ModuleNotFoundError`.** Venv off. Redo Step 1.
2. **Wrong folder.** `cd project/ml_playground` first.
3. **You compared these tokens to CountVectorizer later and panicked.** Different splitters. This lab is `lower().split()`. ml-23 splits on non-letters and drops `'6'`.
4. **You thought vocab kept sentence order.** It is `sorted(set(...))`. `'where'` is last, not first.
5. **You tokenized the label** by using `[0][1]`. Labels are `wismo` / `refund` / `damage`, not customer text.

---

## Knowledge check

Answer from the printout you ran.

1. What is the exact raw `text:` line?
2. List the ten tokens in sentence order.
3. Why does vocab start with `'6'` instead of `'where'`?
4. What happened to `MC-1048292`, and did the hyphen stay?
5. If the sentence said `days days`, would vocab still have length 10?

<details>
<summary>Answers</summary>

1. `where is my order MC-1048292 it has been 6 days`
2. `where`, `is`, `my`, `order`, `mc-1048292`, `it`, `has`, `been`, `6`, `days`
3. Vocab is `sorted(...)`. The character `6` comes before letters.
4. Lowercased to `mc-1048292`. The hyphen stayed, because `split()` only cuts on whitespace.
5. No. Tokens would have length 11 (one extra `days`). Vocab would still have those same unique strings — length 10 — because `set` drops the duplicate.

</details>

---

## Recap

- **You built** a token list and a sorted vocab from Maya’s first WISMO ticket.
- **You understand** token = chunk; vocab = unique sorted chunks; `lower().split()` is crude.
- **Next** you will count those chunks across all ten tickets with CountVectorizer.

Next: `ml-23-bag-of-words`

---

## Stretch goal

Step 5 already switched you to ticket 2. For a second number: change `TICKET_TEXTS[0][0]` to `TICKET_TEXTS[1][0]` (`"package still not here tracking frozen"`). Rerun.

- **Expect:** six tokens, vocab of six, no order id.
- Put `[0]` back when you are done.

---

## Feedback

Could you redo this lab from memory? Note the **lesson id** (`ml-22`), the **step number**, what you **expected**, and what you **saw** (traceback or printout).
