# ml-16 — Confusion, precision, recall

**Level:** Absolute beginner  
**Time:** ~50 minutes  
**Prerequisites:** ml-15  
**Lab outcome:** You map `tn=5`, `fp=11`, `fn=0`, `tp=44` to Maya’s two mistake types, and you can say precision 0.8 vs recall 1.0 in warehouse words

---

## At a glance

A **confusion matrix** counts four stories:

```text
                 guessed no    guessed yes
really no           tn             fp
really yes          fn             tp
```

Tonight:

```text
[[ 5  11]
 [ 0  44]]
precision 0.8  recall 1.0
```

- **False positive (fp=11):** refunded a fine order (money)
- **False negative (fn=0):** missed a smashed vase (trust) — this run caught every real refund
- **Precision** = of guessed refunds, how many were real = `tp / (tp+fp) = 44/55 = 0.8`
- **Recall** = of real refunds, how many we caught = `tp / (tp+fn) = 44/44 = 1.0`

---

## Why this matters

Accuracy can look fine while you bleed the wrong way. Maya must pick which hurt is worse: paying refunds on good orders, or ignoring smashed vases.

If you skip this, “0.8 precision” is a slogan. After this, it is 11 fine orders you refunded by mistake.

---

## Concept primer

| Word | Maya sentence | Formula |
| --- | --- | --- |
| **tn** | Correctly left a fine order alone | — |
| **fp** | Refunded a fine order | — |
| **fn** | Missed a real refund | — |
| **tp** | Caught a real refund | — |
| **Precision** | When we say refund, how often are we right? | `tp/(tp+fp)` |
| **Recall** | Of real refunds, how many did we catch? | `tp/(tp+fn)` |

> **Tip:** Accuracy can look fine while recall on rare refunds is awful (ml-18).

> **Watch out:** Do not “optimize precision” by never predicting refund. Recall dies.

---

## Setup

```bash
cd project/ml_playground
source .venv/bin/activate
```

---

## Hands-on

### Step 1 — Print the 2×2 and the two scores

Why now: the fence in ml-15 did not tell you *which* mistakes you made.

```bash
python classic_labs.py confusion
```

**It worked when** you see:

```text
confusion [[tn fp][fn tp]]
[[ 5 11]
 [ 0 44]]
precision 0.8 recall 1.0
Maya: false positive = refunded a fine order. false negative = missed a smashed vase.
```

Say the four cells out loud with those numbers.

This split is `test_size=0.3`, `random_state=2`, features delay + price + angry words. 60 test rows: `5+11+0+44 = 60`.

### Step 2 — Walk `lab_confusion`

Open `classic_labs.py`. Find `lab_confusion`.

- `confusion_matrix(yte, pred)` — sklearn’s layout is exactly `[[tn, fp], [fn, tp]]` for binary 0/1.
- `precision_score` / `recall_score` with `zero_division=0` so a model that never says yes does not crash.

### Step 3 — Mini experiment

Print `accuracy_score(yte, pred)` as well (already imported in this file). Rerun.

- **Expect:** accuracy = `(5+44)/60 ≈ 0.817`. Same neighborhood as ml-07’s honest model — different seed/split, same lesson: accuracy hides the 11 fps.
- Remove the extra print when done.

- [ ] You mapped fp=11 to “refunded a fine order”
- [ ] You mapped fn=0 to “no missed smashed vase on this exam”
- [ ] You can compute 44/55 = 0.8 by hand

---

## How it works (deeper)

The default 0.5 cut (ml-14) produced this mix of mistakes. Raising the cut usually drops fp and recall together. That trade is a product choice, not a math law.

---

## Common pitfalls

1. **Reading the matrix as `[[tp, fp], ...]`.** sklearn binary default is **tn fp / fn tp**.
2. **Celebrating recall 1.0 as production-ready.** Toy 200 tickets, one split.
3. **Ignoring fp=11 because recall is perfect.** That is 11 refunds of fine orders.

---

## Knowledge check

1. Which cell is “refunded a fine order”?
2. Precision in one Maya sentence.
3. What four numbers printed in the matrix?
4. Why is recall 1.0 here?

<details>
<summary>Answers</summary>

1. False positive (11).
2. When we say refund, how often are we right? (0.8)
3. tn 5, fp 11, fn 0, tp 44.
4. `fn=0`: every real refund in this test slice was caught.

</details>

---

## Recap

- **You named** four cells with warehouse stories.
- **You understand** precision vs recall.
- **Next** trees and forests: checklists that vote.

Next: `ml-17-trees-forests`

---

## Stretch goal

Pass `class_weight="balanced"` into `LogisticRegression`. Rerun. Revert.

- **Expect:** the 2×2 and precision/recall move (ml-18’s idea). Note the new four numbers.

---

## Feedback

Could you redo this lab from memory? Note **ml-16**, the 2×2 you expected vs saw.
