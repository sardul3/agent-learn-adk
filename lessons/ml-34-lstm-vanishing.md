# ml-34 — LSTM and vanishing memory

**Level:** Absolute beginner  
**Time:** ~40 minutes  
**Prerequisites:** ml-33; venv from **ml-00**  
**Lab outcome:** You name LSTM’s three gates in warehouse English, then type `0.7**10` yourself and watch early letters shrink to **0.0282**

---

## At a glance

A vanilla RNN (ml-33) **multiplies** old memory into new memory every step. If that mix is even a little small — say **0.7** — then ten steps later the first letter is almost gone: **0.0282**.

An **LSTM** (Long Short-Term Memory) adds **gates**: knobs that decide *keep*, *write*, and *show*. This lab does not train an LSTM. It prints the three jobs, then makes you feel the fade with arithmetic.

By the end you can explain, without hand-waving:

- forget / input / output in Maya’s words
- why `0.7 ** 10` is the vanishing-gradient cousin you can do on a calculator
- why a long location code can “forget aisle A” in a vanilla RNN

---

## Why this matters

Maya’s scan string is not five characters. A full tag can look like `A1-B2-C3-D4-E5`. If each RNN step keeps only 70% of the old note, the `A` at the front is a rumor by the time the robot reads `E`.

Wrong aisle → wrong chute → idle van. The “vanishing” in **vanishing gradient** is this same shrink, during training: the nudge for early letters becomes tiny, so the net never learns “start with A.”

If you skip typing `0.7**10`, the word *vanishing* stays a scary blog title.

---

## Concept primer

| Word | Plain English | In Maya’s warehouse |
| --- | --- | --- |
| **Gate** | A number (usually 0–1) that lets a fact through or blocks it | A latch on a memory bin |
| **Forget gate** | How much **old** memory to drop | “Erase last zone?” |
| **Input gate** | How much **new** fact to write | “Write this digit?” |
| **Output gate** | How much memory to **show** right now | “Say the current aisle out loud?” |
| **Cell / memory** | The LSTM’s longer note (separate from what it shows) | A clipboard that can survive many scans |
| **Vanishing** | Repeated multiply by a fraction → early signal ≈ 0 | `0.7` ten times → `0.0282` |
| **Vanilla RNN** | The ml-33 loop with no gates | `h = tanh(x@Wxh + h@Whh)` |

```
vanilla:   h ← 0.7 × h   (every letter)     → first letter fades
LSTM:      h ← forget⊙old  +  input⊙new      → can keep aisle A on purpose
```

(`⊙` means multiply slot-by-slot. You do not need to code it today.)

> **Tip:** “Long short-term memory” is a joke name: **short-term** notes that can last a **long** time if the forget gate stays open.

> **Watch out:** This function **prints English**. It does not build `Wxh`. Do not claim you trained LSTM-on-warehouse. You learned why gates exist.

---

## Setup

Reuse the **ml-00** venv. No new packages.

### Step 1 — Enter the playground

Why now: same script as the rest of this pack. Stay in the folder so the next lesson’s imports still work.

```bash
cd project/ml_playground
source .venv/bin/activate
```

- `cd` means “change directory.”
- `source` activates the island in this shell.

**It worked when** `(.venv)` shows and:

```bash
python --version
python -c "import numpy, sklearn; print(numpy.__version__, sklearn.__version__)"
```

```text
Python 3.14.6
2.5.2 1.9.0
```

No plot in this lab. Stdout is the whole show.

---

## Hands-on

### Step 2 — Run the LSTM lab

Why this command now: it is the frozen wording you will quote in the knowledge check. If you skip it, you will paraphrase the gates wrong.

```bash
python later_labs.py lstm
```

- `lstm` is a positional lab name, not `--lstm`.

**It worked when** you see **exactly**:

```text
LSTM gates (plain):
forget: how much old memory to drop
input: how much new fact to write
output: how much memory to show now
Vanishing: if you multiply 0.7 ten times you get 0.0282 — early letters fade in a vanilla RNN.
```

Count the gates: **three** lines after the header. Forget, input, output.

- [ ] You can point at `0.0282` on your screen
- [ ] You did not invent a fourth gate

### Step 3 — Walk `lab_lstm`

Open `later_labs.py`. Find `lab_lstm`.

1. Four `print`s name the three gates in plain English. No numpy yet.
2. The last `print` does the fade: `round(0.7**10, 4)`.
   - `**` is Python’s power: `0.7 ** 10` means 0.7×0.7×… ten times.
   - `round(..., 4)` keeps **four** digits after the decimal → **0.0282**.

That is the whole function. The “model” today is a sentence plus one power.

> **Tip:** `round(0.7**10, 4)` is how the lab prints a clean `0.0282`. The raw float has more junk digits. You will see them in Step 4.

> **Watch out:** `0.7**10` is **not** a learning rate. It is a story: “each step keeps 70% of the old letter.” Real RNNs use matrices, not one 0.7, but the shrink is the same shape.

### Step 4 — Type the fade yourself

Why now: reading `0.0282` is cheap. **Typing** the power makes the shrink yours.

`-c` means “run this Python code string and exit.”

```bash
python -c "print(0.7**10)"
```

**It worked when** you see:

```text
0.02824752489999998
```

Walk the number:

- Full float ≈ **0.02824752**
- Lab’s `round(..., 4)` → **0.0282**
- In warehouse English: after ten “keep 70%” steps, the first scan is about **3%** as loud as it started

Optional feel for “worse fade”:

```bash
python -c "print(0.5**10)"
```

**Expect:** `0.0009765625` — keep half each time and ten letters later the start is basically gone.

- [ ] You ran `print(0.7**10)` without copying from memory of a screenshot
- [ ] You can say how the lab got `0.0282` from that float (`round(..., 4)`)

### Step 5 — Connect it to ml-33

In ml-33, `h = tanh(x @ Wxh + h @ Whh)`. The `h @ Whh` piece is “old memory, remixed.” If that remix **shrinks** most slots, you are living `0.7**10` in six dimensions.

LSTM’s **forget gate** is the designed version of that remix: it can stay **near 1** for “remember aisle A” instead of being stuck at 0.7.

- [ ] You can point at `h @ Whh` in `lab_rnn` as the place vanilla memory can vanish
- [ ] You can name which printed gate would keep aisle A

---

## How it works (deeper)

**Vanishing gradient** (training word) and **vanishing activation** (today’s `0.7**10`) are cousins.

During training you send a blame signal **backward** through the same multiplies. If each step multiplies by 0.7, ten steps back the blame is 0.0282. The early `Wxh` rows barely move. The net never learns the first letter.

Gates help because a multiply-by-**almost-1** does not crush the past. Forget ≈ 1 → keep. Forget ≈ 0 → drop on purpose (Maya finished that aisle).

This lesson does **not** implement those multiplies. ml-33 already showed the loop. Today is the reason the next architecture in textbooks grows extra knobs.

```
0.7 ** 1  = 0.7
0.7 ** 2  = 0.49
0.7 ** 5  ≈ 0.168
0.7 ** 10 = 0.0282   ← lab
```

---

## Common pitfalls

1. **`ModuleNotFoundError`.** Venv off. `source .venv/bin/activate`.
2. **Wrong folder.** `cd project/ml_playground` first.
3. **`unrecognized arguments`.** `lstm` is positional. No dashes.
4. **You quoted `0.0282475` as the lab output.** The lab prints **`0.0282`**. The longer float is from your `-c` line.
5. **You said LSTM “solves language.”** It solves **keep/drop/show** on a memory tape. Transformers (ml-42+) are the other family. Both exist because of ml-32’s bag hole.

---

## Knowledge check

Answer from the prints you actually produced.

1. What are the three gate names, in the order the lab prints them, and the plain-English job of each?
2. What number does `python later_labs.py lstm` print after “you get”?
3. What does `python -c "print(0.7**10)"` print (the long float)?
4. How does the lab turn that float into `0.0282`? (Name the function and the `4`.)
5. In one sentence: why do early letters fade in a vanilla RNN?

<details>
<summary>Answers</summary>

1. forget — drop old memory; input — write a new fact; output — how much memory to show now.
2. `0.0282`
3. `0.02824752489999998`
4. `round(0.7**10, 4)`
5. Each step remixes (effectively multiplies) old memory by a fraction, so the first token’s effect shrinks toward zero.

</details>

---

## Recap

- **You ran** `lab_lstm` and typed `0.7**10` yourself.
- **You understand** three gates (forget / input / output) and why vanilla memory vanishes.
- **Next** Maya’s dented carton becomes a **grid of brightness**, not a sentence.

Next: `ml-35-pixels-as-numbers`

---

## Stretch goal

In `lab_lstm`, change `0.7**10` to `0.7**20` (still `round(..., 4)`). Save. Rerun:

```bash
python later_labs.py lstm
```

- **Expect:** the printed fade is **`0.0008`** (`round(0.7**20, 4)`). Twice the letters, much quieter first scan.
- Put **`10`** back when you are done so this lesson’s `0.0282` still matches.

Confirm with:

```bash
python -c "print(round(0.7**20, 4))"
```

---

## Feedback

Could you redo this lab from memory? Note the **lesson id** (`ml-34`), the **step number**, what you **expected**, and what you **saw** (traceback or printout).
