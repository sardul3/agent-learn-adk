# ml-49 — Chatbot that talks like you

**Level:** Absolute beginner  
**Time:** ~60 minutes  
**Prerequisites:** ml-48 (bigram sample); Setup from ml-00  
**Lab outcome:** You generate a cousin-of-you sample from `my_voice.txt`, answer Maya’s eval with **NO**, then replace the file with **your** sentences and judge again

---

## At a glance

Same **job** as ml-45 and ml-48: next character given this character.

This time the data is a local file:

```text
project/ml_playground/my_voice.txt
```

- **First run** may **write** a starter file if that path is missing, then sample from it.
- The starter sample is a **clumsy cousin**, not you:

```text
he agivecher ugi'li'l ck pordean? thanscan? i'l p.
ugi i'll an an? ive pulolansch
```

**Eval:** would Maya send this to a customer? **NO.**

You **must** replace `my_voice.txt` with your own sentences (no secrets, no PII, no card numbers), rerun, and judge again. Quality is **cousin**, not clone.

Do **not** deploy this as Meridian CX. Do **not** replace OrderOps with it.

---

## Why this matters

Maya’s intern fine-tunes “on my voice” and pastes the sample into a customer thread. The customer reads `ugi'li'l ck pordean?` and files a complaint.

This lab is the fun packed project **and** the humility check. A count table on a handful of sentences cannot be night-shift Maya.

If you skip replacing the file, you only proved the starter is clumsy. The point is: **your** sentences still fail Maya’s eval. That is the product lesson from ml-47 (voice → tiny local counts, not a shippable bot).

---

## Concept primer

| Word | Plain English | In `lab_youbot` |
| --- | --- | --- |
| **Voice file** | Plain text you wrote | `my_voice.txt` next to the lab |
| **Count table** | Like ml-45: tally next characters | `W[now, next] += 1` then row-normalize |
| **Cousin sample** | Same *alphabet habits*, not the same person | Clumsy shuffle of your letters |
| **Maya’s eval** | Would I send this to a customer? | **NO** for this CPU bot |

ml-48 **nudged random logits** for 200 steps. This lab **counts**, like ml-45, on whatever is in the file. No 200-step loop. No attention.

```text
read my_voice.txt
lowercase it
count (this char → next char)
softmax is not needed: rows already sum to 1
start at the first character
roll 80 more characters
print the cousin
ask Maya’s eval
```

> **Tip:** More *different* sentences beat pasting the same line 500 times. Repeats teach a loop, not a voice.

> **Watch out:** Keep the file **local**. Do not paste passwords, badge IDs, customer names, addresses, or card numbers. This folder is a homework playground.

---

## Setup

If your prompt does not show `(.venv)`, finish Setup in ml-00 first. This playground is **Python 3.14.6**, **numpy 2.5.2**, **scikit-learn 1.9.0**.

```bash
cd project/ml_playground
source .venv/bin/activate
```

- `source` runs the activate script in *this* terminal so `python` is the island’s Python.

**It worked when** `(.venv)` is at the front of the prompt.

You will edit **one file** in this folder: `my_voice.txt`. If it is missing, the lab writes a starter. If it is already there (common in this repo), you go straight to the sample — then you still replace the sentences.

---

## Hands-on

### Step 1 — Run you-bot once (starter or current file)

Why this command now: `youbot` is the argparse name for `lab_youbot`. You need the clumsy cousin on screen before you rewrite the file.

```bash
python later_labs.py youbot
```

`youbot` is a lab name, not a dash-flag.

**If `my_voice.txt` did not exist**, you also see a line like:

```text
Wrote a starter .../project/ml_playground/my_voice.txt — replace with YOUR sentences, then rerun.
```

**If the file already existed**, that write line is skipped. Either way, with the **starter sentences** (the three lines below), numpy generator seed **0**, you should see:

```text
cousin-of-you sample:
 he agivecher ugi'li'l ck pordean? thanscan? i'l p.
ugi i'll an an? ive pulolansch
Eval: would Maya send this to a customer? If no, do not ship it. Quality is 'cousin', not clone.
```

Starter text the lab writes (and what this screenshot used):

```text
hey — yeah I can look that up.
give me the order id and I'll check scans.
ugh late again? I'll pull the policy.
```

**About the leading space on the sample line:** `print("cousin-of-you sample:\n", "".join(out))` passes **two** arguments. Python inserts a space between them. The cousin **starts with `h`** (from `hey`), not with a space. The space is `print`, not the model.

- [ ] You ran `python later_labs.py youbot`
- [ ] You saw a clumsy cousin (starter sample matches if you still have the three starter lines)

### Step 2 — Maya’s eval (say it)

Look at `he agivecher ugi'li'l ck pordean?` (or your current cousin).

Say this out loud:

> “Would Maya send this to a customer? **No.** Do not ship it.”

That is the whole eval. Not BLEU. Not “it used an apostrophe so it is me.”

- [ ] You answered **NO**
- [ ] You did not paste the sample into a real ticket

### Step 3 — Walk the code (do not paste blindly)

Open `later_labs.py`. Find `lab_youbot`.

1. `path = ROOT / "my_voice.txt"` — `ROOT` is the `ml_playground` folder, so the file sits beside `later_labs.py`.
2. `if not path.exists():` writes the three starter sentences and prints `Wrote a starter`.
3. `text = path.read_text(...).lower()` — sampling is case-flattened.
4. `chars = sorted(set(text))` — vocab is **whatever characters you typed** (letters, punctuation, spaces, the em dash `—` in the starter).
5. Count loop: `W[data[i], data[i + 1]] += 1`, then divide each row by its sum. Same shape as ml-45’s `P`.
6. `rng = np.random.default_rng(0)` — sample is repeatable **for a given file**. Change the file, the cousin changes.
7. Start at `data[0]` (first character of the file), then 80 `rng.choice` steps using that row of `W`.
8. Last print is Maya’s eval, written into the lab so you cannot miss it.

> **Tip:** Empty file would make `chars` fall back to `[" "]` (`or [" "]`). Do not ship a blank voice file. Put real sentences.

> **Watch out:** `W[ix] if W[ix].sum() else None` — a character that never has a next (last unique leftover) can break sampling. Keep several sentences so every char you use appears as “now” at least once.

### Step 4 — Replace the file with YOUR sentences (required)

Open `project/ml_playground/my_voice.txt`. Delete the starter. Paste **your** lines.

Rules:

- Write how you actually talk in a chat to a coworker. Short sentences. Typos allowed.
- **No** secrets, **no** passwords, **no** customer names, **no** addresses, **no** card numbers, **no** badge IDs.
- At least five sentences. Different words. Include a question mark if you want to see `?` in the cousin.

Save. Rerun:

```bash
python later_labs.py youbot
```

**Expect:** a new clumsy cousin that uses *your* letters and punctuation. Still not a clone. Still not CX.

Judge again:

> “Would Maya send this to a customer?”

The honest answer is still **NO**. If you said yes, you are grading spelling crumbs, not a shippable agent.

- [ ] You replaced the starter with your own sentences
- [ ] You reran `youbot` and saw a different cousin
- [ ] You answered Maya’s eval **NO** the second time too

### Step 5 — Optional: prove the first-run write path

Only if you want to see `Wrote a starter` yourself:

```bash
mv my_voice.txt my_voice.bak
python later_labs.py youbot
```

- `-` is not a flag on `mv`; this renames the file so `path.exists()` is false.

**Expect:** the write line, a **new** starter `my_voice.txt`, and the starter cousin again.

Put your sentences back:

```bash
mv my_voice.bak my_voice.txt
```

Then rerun `youbot` so you are back on *your* voice file.

- [ ] (Optional) You saw `Wrote a starter` and restored your file

---

## How it works (deeper)

You-bot is **not** ChatGPT with a “talk like me” slider.

It is a **spreadsheet of letter habits**. If you often type `I'` then `l`, the cousin will spit `i'll` crumbs. It will also walk into `ugi'li'l` because each pick only looks at **one** previous character.

That is why ml-47 put voice in the **tiny local counts** bucket, not RAG:

- RAG would *fetch* a style guide paragraph and still need a strong generator.
- This lab *is* the generator, and it is a baby.

Production Meridian CX (Pack A / Pack D) still means: tools, Gemini, policy RAG, evals, a human when it is unsure. This file is homework.

---

## Common pitfalls

1. **`ModuleNotFoundError`.** Venv not active. `cd project/ml_playground` and `source .venv/bin/activate`.
2. **You skipped replacing the file.** The lesson is not done. Step 4 is required.
3. **You put a customer order id or a card number in `my_voice.txt`.** Delete it. Write fake warehouse chat instead.
4. **You said YES to Maya’s eval because you spotted one real word.** Cousin ≠ clone ≠ shippable.
5. **You planned to hook this up as the OrderOps reply agent.** Do not. Native ADK owns that path.

---

## Knowledge check

Answer from the run you did and the eval sentence.

1. With the starter file and seed 0, what does the cousin look like (first messy chunk is enough)?
2. Would Maya send that starter cousin to a customer?
3. What does the first run do if `my_voice.txt` is missing?
4. What must you never put in `my_voice.txt`?
5. After you pasted *your* sentences, did the eval become YES?
6. Is this lab a replacement for Meridian CX / OrderOps?

<details>
<summary>Answers</summary>

1. `he agivecher ugi'li'l ck pordean? thanscan? i'l p.` then `ugi i'll an an? ive pulolansch` (plus a `print` space after the label).
2. **No.**
3. It writes those three starter sentences and prints `Wrote a starter` with the path.
4. Secrets, passwords, PII, customer data, card numbers.
5. **No.** Still a cousin. Still do not ship.
6. **No.**

</details>

---

## Recap

- **You sampled** a clumsy cousin from `my_voice.txt` and failed Maya’s customer eval on purpose.
- **You understand** local character counts ≠ a CX bot; voice on this CPU is a homework table.
- **Next** leave the ML venv and watch **tabular Q-learning** in five cartoon worlds — then ml-50 will name why a table dies when the spreadsheet gets huge.

Next: `bonus-rl-visual-playground`

(ml-50 comes **after** that bonus. Do the window first.)

---

## Stretch goal

Add **one** extra sentence to `my_voice.txt` that uses a letter you almost never typed before (for example a `z` or `q` in a fake SKU like `SKU-Z9`). Save. Rerun `python later_labs.py youbot`.

**Expect:** that rare letter can now appear in the cousin. If it never shows, you only added it at the very end with no “next” pair — add it in the *middle* of a sentence.

You may **keep** your voice file (this is your data). You do not revert your real sentences. If you added a silly SKU only for the stretch, you can delete that one line after you have seen `z` or `q` appear.

- [ ] You reran after a real file edit and saw the cousin move

---

## Feedback

Could you redo this lab from memory? Note the **lesson id** (`ml-49`), the **step number**, what you **expected**, and what you **saw** (traceback, cousin text, or “I forgot to replace the file”).
