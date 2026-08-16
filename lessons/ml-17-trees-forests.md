# ml-17 — Trees and forests

**Level:** Absolute beginner  
**Time:** ~45 minutes  
**Prerequisites:** ml-16  
**Lab outcome:** You fit a depth-3 tree and a 40-tree forest, read importances, and you catch that tonight’s accuracies are **train** scores — not an exam

---

## At a glance

A **tree** asks yes/no questions (`delay > 4.5?`). A **forest** is many trees voting — less drama from one weird question.

Tonight (fit on **all 200** tickets, no split — that is the gotcha):

```text
tree acc 0.905
forest acc 1.0
importances  delay_days 0.446  price_usd 0.336  angry_words 0.218
```

Forest **1.0** on the rows it studied is not “solved refunds.” It is a memorizer smell until you split (ml-06).

**Importance** here is “how much did this question reduce mixing of labels?” Not a causal story. Not “Maya should only look at delay.”

---

## Why this matters

Maya already trains people with checklists. Trees look like checklists.

If you skip this, random forests are magic voting. After this, they are many short checklists averaged.

---

## Concept primer

| Word | Plain English | Tonight |
| --- | --- | --- |
| **`max_depth`** | How long the checklist can be | **3** |
| **`n_estimators`** | How many trees vote | **40** |
| **Importance** | Share of “how useful were splits on this column?” | Delay largest |

> **Tip:** Deep trees memorize. Forests average that away — still not magic.

> **Watch out:** These accuracies are `.score(X, y)` on the **same** `X, y` they fit. Homework, not exam.

---

## Setup

```bash
cd project/ml_playground
source .venv/bin/activate
```

---

## Hands-on

### Step 1 — Fit tree and forest

Why now: you have a fence (ml-15) and a 2×2 (ml-16). Checklists are the other warehouse-native recipe.

```bash
python classic_labs.py trees
```

**It worked when** you see:

```text
tree acc 0.905 forest acc 1.0
importances {'delay_days': 0.446, 'price_usd': 0.336, 'angry_words': 0.218}
```

Delay is the biggest slice of importance. That matches the generator’s `delay > 4.5` rule — plus price and angry words also create refunds, so they get the rest.

Forest 1.0: 40 trees can carve the 200 rows finely. Do not ship that number.

### Step 2 — Walk `lab_trees`

Open `classic_labs.py`. Find `lab_trees`.

- `DecisionTreeClassifier(max_depth=3, random_state=0)`
- `RandomForestClassifier(n_estimators=40, random_state=0)`
- `.score(X, y)` on the **training** matrix
- `forest.feature_importances_`

`random_state=0` freezes the shuffle inside the forest so your 0.905 / 1.0 / importances match.

### Step 3 — Mini experiment

Set `max_depth=1` on the tree. Rerun.

- **Expect:** tree accuracy drops (a stump: one question). Forest still near 1.0 on train.
- Put `max_depth=3` back.

- [ ] You treated forest 1.0 as a warning, not a trophy
- [ ] You can say importance is not causation
- [ ] You know `n_estimators=40` is “forty trees vote”

---

## How it works (deeper)

Each split tries to make child piles *purer* (more all-refund or all-fine). Depth limits how many questions. A forest trains trees on random row/column draws, then votes. Voting reduces one tree’s drama (variance, ml-09). It does not create new facts.

---

## Common pitfalls

1. **Quoting 1.0 in a review as test accuracy.** There was no test split.
2. **Dropping angry_words because importance is 0.218.** Smaller is not “zero.”
3. **Deeper tree ‘to beat 0.905’.** You will memorize (ml-30 smell).

---

## Knowledge check

1. What does `max_depth` limit?
2. What does a forest add?
3. What three importances printed?
4. Why is forest acc 1.0 not an exam score?

<details>
<summary>Answers</summary>

1. How long the checklist can be.
2. Many trees vote.
3. delay 0.446, price 0.336, angry words 0.218.
4. The lab scored the same 200 rows it fit on.

</details>

---

## Recap

- **You fitted** a shallow tree and a forest.
- **You treated** importance as a hint.
- **Next** the 95% always-no trap: class imbalance.

Next: `ml-18-class-imbalance`

---

## Stretch goal

Add `train_test_split` and print `.score(Xte, yte)` for both models. Revert or keep if you want an honest exam — then say so in your notes.

- **Expect:** forest test acc below 1.0.

---

## Feedback

Could you redo this lab from memory? Note **ml-17**, 0.905 vs 1.0, expected vs saw.
