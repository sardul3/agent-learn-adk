# ml-18 — Class imbalance

**Level:** Absolute beginner  
**Time:** ~45 minutes  
**Prerequisites:** ml-17  
**Lab outcome:** You see a 95% always-no accuracy, a naive model that barely says yes (7 positives), and a balanced model that says yes 19 times

---

## At a glance

If 95% of tickets are not refunds, **always say no** is 95% accurate and useless.

**Class weights** tax the common class so the rare class is seen.

Tonight’s toy: 200 points, **10** real yeses.

```text
always-say-no acc 0.95
naive model acc 0.985  positives predicted 7
balanced weights [0.526..., 10.0]  positives predicted 19
```

Count **predicted positives**, not only accuracy. Accuracy is the villain’s metric here.

---

## Why this matters

Fraud and damage are rare. Meridian will celebrate 0.985 while customers with smashed vases never enter the yes pile.

If you skip this, ml-16’s recall on the rare class will silently die in production.

---

## Concept primer

| Word | Plain English | Tonight |
| --- | --- | --- |
| **Imbalance** | One label dominates | 190 no vs 10 yes |
| **Always-no** | Dummy policy | acc **0.95** |
| **`class_weight='balanced'`** | Reweight the loss | yes-class weight **10.0** |
| **Predicted positives** | How often we said yes | naive **7** vs balanced **19** |

> **Tip:** Pair this with the confusion lesson. Accuracy is the trap.

> **Watch out:** Weights are not a substitute for more real rare examples.

---

## Setup

```bash
cd project/ml_playground
source .venv/bin/activate
```

---

## Hands-on

### Step 1 — Run the imbalance lab

Why now: you need to *see* 95% as a dummy, then count yeses.

```bash
python classic_labs.py imbalance
```

**It worked when** you see:

```text
always-say-no acc 0.95
naive model acc 0.985 positives predicted 7
balanced weights [ 0.52631579 10.        ] positives predicted 19
```

Story:

- 10 planted yeses (`y[:10] = 1`) shifted in feature space (`X[:10] += 2.5`).
- Always-no hits 0.95 by ignoring them.
- Naive logistic gets **0.985** while saying yes only **7** times (misses some rares, maybe extra fps — you would need a 2×2 to see which).
- Balanced: the yes class gets weight **10** (about `n / (2 × n_yes)`). It says yes **19** times — more recall-shaped, possibly more fps. Product choice.

### Step 2 — Walk `lab_imbalance`

Open `classic_labs.py`. Find `lab_imbalance`.

- Synthetic `X`, not `tickets()` — a clean 95% demo.
- `compute_class_weight("balanced", classes=[0, 1], y=y)`
- Two `LogisticRegression`s: default vs `class_weight="balanced"`.

There is no plot. The numbers are the lab.

### Step 3 — Mini experiment

Print `clf.predict(X).sum()` you already have. Also print `(clf.predict(X) == 1) & (y == 1)` count (true positives) for both models. Revert extra prints after.

- **Expect:** balanced should catch more of the 10 true yeses if the shift is learnable. Note both numbers.

- [ ] You refused to celebrate 0.95 / 0.985
- [ ] You compared 7 vs 19 predicted yeses
- [ ] You can say the yes-class weight was 10.0

---

## How it works (deeper)

Loss without weights treats each row equally, so 190 nos shout down 10 yeses. Balanced weights make a yes-row “louder” in the bowl (ml-05). You can also resample (repeat rare rows). Pick a metric that cares (recall on yes, or a confusion matrix).

---

## Common pitfalls

1. **Shipping 0.985.** Count yeses.
2. **Thinking 19 yeses is “too many.”** There are only 10 true yeses — extra yeses are fps. Still often better than missing rares. Use ml-16 to see the trade.
3. **Weights as a cure for 3 real damage tickets in a year.** You still need data.

---

## Knowledge check

1. Why is 95% accuracy a trap?
2. Name one fix in this lab.
3. How many positives did naive vs balanced predict?
4. What was the yes-class weight?

<details>
<summary>Answers</summary>

1. The majority class dominates; always-no gets 0.95 for free.
2. `class_weight="balanced"`.
3. 7 vs 19.
4. 10.0

</details>

---

## Recap

- **You refused** majority accuracy.
- **You counted** predicted yes.
- **Next** unsupervised piles of SKUs (no refund label).

Next: `ml-19-kmeans-skus`

---

## Stretch goal

Change `y[:10] = 1` to `y[:5] = 1` (rarer). Rerun. Revert.

- **Expect:** always-no acc 0.975; weights and predicted-yes counts move.

---

## Feedback

Could you redo this lab from memory? Note **ml-18**, 7 vs 19, expected vs saw.
