# ml-46 — Next token and temperature

**Level:** Absolute beginner  
**Time:** ~50 minutes  
**Prerequisites:** ml-45 (next-token table); Setup from ml-00  
**Lab outcome:** You print three softmax distributions for logits `[2.0, 1.0, 0.1]` at T = 0.2, 1.0, and 2.0, and you can say what T is *not*

---

## At a glance

A model’s last layer spits out **logits**: raw scores, one per next token. They are not chances yet.

**Softmax** turns those scores into chances that add to 1. **Temperature T** divides the logits first:

```text
chances = softmax(logits / T)
```

You will run the lab and see, for logits `[2.0, 1.0, 0.1]`:

| T | Printed probs |
| --- | --- |
| **0.2** | `[0.993 0.007 0.   ]` |
| **1.0** | `[0.659 0.242 0.099]` |
| **2.0** | `[0.502 0.304 0.194]` |

Low T = almost always pick the winner. High T = more random. **T is not weather.**

---

## Why this matters

Maya’s intern asks the night-shift bot: “What is the next letter after `B` in the location code?” If T is tiny, the bot always says `C`. If T is huge, it sometimes says `A` because “creative.”

A refund reply is not a poem. Maya wants the winner. A brainstorm for SKU names can stand a higher T.

If you skip this lab, “turn temperature down” is a slogan. After this lab it is: divide the logits, then softmax, watch the **0.993** vs **0.502**.

---

## Concept primer

| Word | Plain English | Tonight’s numbers |
| --- | --- | --- |
| **Logit** | A raw score for one next token, before chances | `[2.0, 1.0, 0.1]` |
| **Softmax** | `exp(score)` then divide by the total, so shares add to 1 | At T=1.0: `[0.659 0.242 0.099]` |
| **Temperature T** | A divider on the logits. Smaller T = peakier chances | 0.2 vs 1.0 vs 2.0 |
| **Winner** | The token with the biggest logit | First slot, score `2.0` |

```text
logits  ──►  divide by T  ──►  exp  ──►  divide by sum  ──►  chances
```

Worked T = 1.0 (no divider):

```text
exp(2.0) ≈ 7.389
exp(1.0) ≈ 2.718
exp(0.1) ≈ 1.105
sum      ≈ 11.212

7.389 / 11.212 ≈ 0.659
2.718 / 11.212 ≈ 0.242
1.105 / 11.212 ≈ 0.099
```

That matches the print `[0.659 0.242 0.099]`.

> **Tip:** Softmax never makes a new winner. The biggest logit stays the biggest chance. T only changes *how sure* you look.

> **Watch out:** T is not degrees outside, not GPU heat, not “how angry the customer is.” It is a knob on the chance split. The lab’s last line says this on purpose.

---

## Setup

If your prompt does not show `(.venv)`, finish Setup in ml-00 first. This playground is **Python 3.14.6**, **numpy 2.5.2**, **scikit-learn 1.9.0**.

```bash
cd project/ml_playground
source .venv/bin/activate
```

- `source` runs the activate script in *this* terminal so `python` is the island’s Python.

**It worked when** `(.venv)` is at the front of the prompt.

---

## Hands-on

### Step 1 — Run the temperature lab

Why this command now: `temp` is the argparse name for `lab_temp`. The three printed vectors are the lesson.

```bash
python later_labs.py temp
```

`temp` is a lab name, not a dash-flag.

**It worked when** you see:

```text
T=0.2 probs [0.993 0.007 0.   ]
T=1.0 probs [0.659 0.242 0.099]
T=2.0 probs [0.502 0.304 0.194]
Low T = pick the winner. High T = more random. T is not 'degrees outside'.
```

- [ ] You ran `python later_labs.py temp`
- [ ] Your three vectors match (numpy 2.5.2 rounding to 3 decimals)

### Step 2 — Point at T = 0.2 out loud

Logits divided by 0.2 become `[10.0, 5.0, 0.5]`. `exp(10)` dwarfs the others.

> “At **T = 0.2**, the winner has chance **0.993**. Second place is **0.007**. Third prints as **0.** (it is about `0.00007`, rounded).”

Maya would ship that for “next letter after B.” Almost never a surprise.

Now T = 2.0: `[0.502 0.304 0.194]`.

> “At **T = 2.0**, the winner is only **0.502**. Second is **0.304**. Third is **0.194**. The intern is rolling a loose die.”

- [ ] You said both sentences with the printed numbers
- [ ] You can rank the three T values from peaky to flat: 0.2, then 1.0, then 2.0

### Step 3 — Walk the code (do not paste blindly)

Open `later_labs.py`. Find `lab_temp`.

1. `logits = np.array([2.0, 1.0, 0.1])` — three fake next-token scores. Think: `C`, `A`, `B` after a location letter, or three refund phrases.
2. The loop is `for T in (0.2, 1.0, 2.0):`.
3. Inside:

```text
p = exp(logits / T)
p = p / p.sum()
```

That is softmax with temperature. No sklearn. No GPU.

4. `np.round(p, 3)` is what you read. Third slot at T=0.2 rounds to `0.`
5. The last `print` is the sentence to steal: low T picks the winner; high T is more random; T is not degrees outside.

There is no plot. If a window does not open, that is correct.

> **Tip:** `exp` on a huge number can overflow in other code. This lab’s logits stay small. Real GPT code subtracts `logits.max()` first (you will see that in ml-48). Same chances, safer math.

> **Watch out:** T = 0 is illegal (divide by zero). Sampling code uses a tiny floor, or a separate “greedy” path that skips softmax and takes `argmax`.

### Step 4 — Mini experiment (do it)

In `lab_temp`, change the tuple to include a colder T:

```python
for T in (0.05, 0.2, 1.0, 2.0):
```

Save. Run again:

```bash
python later_labs.py temp
```

**Expect:** a new first line, even peakier than T=0.2. The winner should print as **1.0** (or `0.999` rounded to 3 decimals), and the others as **0.**

Put `(0.2, 1.0, 2.0)` back when you are done.

- [ ] You added `0.05`, reran, and saw the winner go to ~1.0
- [ ] You put the original tuple back

---

## How it works (deeper)

Chances must add to 1 so you can sample: roll a weighted die, pick one next token, feed it back, repeat. That loop is “the model is talking.”

T reshapes the die:

```text
T → 0   almost always argmax (greedy)
T = 1   softmax of the raw logits
T → ∞   closer to even (every token looks similar)
```

Maya’s CX bot:

- **Tracking ETA** — low T. Do not invent a second warehouse.
- **Brainstorm aisle names** — higher T. Weird words are allowed.

T does not change the **logits**. The recipe already scored `2.0` vs `0.1`. T only changes how sharply you turn scores into a pick.

ml-45 filled a table of chances by **counting**. This lesson starts from **scores** and makes chances with softmax. ml-48 will train scores, then sample with this same `exp / sum` step.

---

## Common pitfalls

1. **`ModuleNotFoundError: numpy`.** Venv not active. `cd project/ml_playground` then `source .venv/bin/activate`.
2. **You thought T = 0.2 meant 0.2°C.** Read the last printed line again.
3. **You thought high T “makes the model smarter.”** It makes the pick noisier. The scores did not get wiser.
4. **You expected third slot at T=0.2 to print `0.000`.** `np.round(..., 3)` prints `0.` for that tiny leftover.
5. **You set T = 0 in a copy-paste.** Division by zero. Use greedy `argmax` instead.

---

## Knowledge check

Answer from the stdout you ran, not from memory of ChatGPT’s slider.

1. What are the three logits in the lab?
2. At **T = 0.2**, what is the printed chance vector?
3. At **T = 1.0**, what is the printed chance vector?
4. At **T = 2.0**, what is the printed chance vector?
5. Does raising T change which token has the biggest chance?
6. In one sentence: T is not what?

<details>
<summary>Answers</summary>

1. `[2.0, 1.0, 0.1]`.
2. `[0.993 0.007 0.   ]`.
3. `[0.659 0.242 0.099]`.
4. `[0.502 0.304 0.194]`.
5. No. The first slot stays the winner at all three T values. The mass spreads.
6. Weather / degrees outside (or GPU heat). It is a divider on logits before softmax.

</details>

---

## Recap

- **You built** three chance vectors from the same logits at three temperatures.
- **You understand** softmax + T: low T is greedy, high T is noisier, T is not weather.
- **Next** you will name three ways to *change what the model does* without pretending this CPU folder replaces OrderOps: prompt, fine-tune, RAG.

Next: `ml-47-finetune-prompt-rag`

---

## Stretch goal

In `lab_temp`, change the logits to a tie for first place:

```python
logits = np.array([2.0, 2.0, 0.1])
```

Rerun `python later_labs.py temp`.

**Expect at T = 1.0:** the first two chances are equal (about `0.465` each) and the third is small. At T = 0.2 the first two still split the mass — a tie stays a tie. T does not break a tie; it only sharpens or flattens.

Put `[2.0, 1.0, 0.1]` back when you are done.

- [ ] You saw the first two slots share the win
- [ ] You reverted the logits

---

## Feedback

Could you redo this lab from memory? Note the **lesson id** (`ml-46`), the **step number**, what you **expected**, and what you **saw** (traceback or printed vectors).
