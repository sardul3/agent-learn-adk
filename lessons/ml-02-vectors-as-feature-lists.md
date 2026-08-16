# ml-02 — Vectors as feature lists

**Level:** Absolute beginner  
**Time:** ~50 minutes  
**Prerequisites:** ml-01  
**Lab outcome:** You can add and scale a 2-number list and draw it as an arrow from the origin

---

## At a glance

A **vector** is an ordered list of numbers. `[weight, delay]` is a vector. An arrow from `(0, 0)` is the same list drawn on paper.

Two operations today:

- **Add** tip-to-tail (pair up the slots, add each pair)
- **Scale** (multiply every slot by the same number — stretch or shrink)

By the end you can explain why `[3, 1]` is not `[1, 3]`, and why linear algebra in this track is mostly “lists of features.”

---

## Why this matters

Maya never has only weight. She has weight **and** delay **and** zone. If you only know how to draw one number on a line (ml-01), you cannot hold two facts at once.

This lab gives those two facts a picture: arrows. Later, a **matrix** (ml-04) is just many vectors stacked as rows.

---

## Concept primer

| Word | Plain English | Warehouse |
| --- | --- | --- |
| **Vector** | Ordered list of numbers | `[3 kg, 1 day late]` |
| **Origin** | The zero point `(0, 0)` | “No weight, no delay” as a drawing start |
| **Add** | Add matching slots | `[3, 1] + [1, 4] = [4, 5]` |
| **Scale** | Multiply every slot | `2 × [3, 1] = [6, 2]` |
| **Length** | How far the arrow is from origin | For `[3, 4]`, length is 5 |

Length of `[3, 1]` in this lab: `sqrt(3² + 1²) ≈ 3.16`. You do not need the word “norm.” Length is “how far from zero.”

```
          delay
            ^
            |     * A+B (4, 5)
            |    /
            |   / B from the tip of A
            |  /
            | * A (3, 1)
            |/
            +--------> weight
```

> **Tip:** Order is meaning. Swap the slots and you swapped “kilos” with “days.” The arithmetic still runs. The warehouse breaks.

> **Watch out:** People say “vector” for both the list and the arrow. Same thing.

---

## Setup

```bash
cd project/ml_playground
source .venv/bin/activate
```

**It worked when** `(.venv)` shows in the prompt.

---

## Hands-on

### Step 1 — Run the arrows

Why now: addition is easy to memorize as a formula and still feel fake. The picture is tip-to-tail.

```bash
python m0_labs.py vectors
```

**It worked when** a square plot opens (equal axes, grid on) and the terminal prints:

```text
length of A: 3.1622776601683795
A + B = [4. 5.]
2 * A = [6. 2.]
```

On the plot:

- blue arrow **order A** = `[3, 1]` from the origin
- orange arrow starts at the *tip* of A and draws **B** = `[1, 4]`
- dashed green arrow is **A + B** = `[4, 5]` from the origin — same landing spot as walking A then B

Close the window after you trace origin → A-tip → A+B-tip with your finger.

### Step 2 — Redo the arithmetic

You already have the printout. Confirm it by hand:

- `3+1 = 4`, `1+4 = 5` → `[4, 5]`
- `2×3 = 6`, `2×1 = 2` → `[6, 2]`
- length: `sqrt(9+1) ≈ 3.16`

- [ ] Printout matched your hand arithmetic
- [ ] You can point at tip-to-tail on the figure

### Step 3 — Walk the code

Open `m0_labs.py`. Find `lab_vectors`.

- `a = np.array([3.0, 1.0])` and `b = np.array([1.0, 4.0])` — two lists.
- `a + b` is numpy adding **pairwise**. That is the whole of vector addition.
- `2 * a` scales.
- `np.sqrt((a**2).sum())` is length: square each slot, add, square-root.
- `ax.arrow(0, 0, *a, ...)` draws from the origin. `ax.arrow(*a, *b, ...)` draws B starting at A’s tip.

`*a` unpacks the two numbers as `x, y` for the arrow call.

### Step 4 — Mini experiment

Change `b` to `np.array([4.0, 0.0])` (pure extra weight, no extra delay). Save. Rerun.

- **Expect:** A + B lands at `[7, 1]`. The orange arrow is horizontal.
- Put `[1.0, 4.0]` back.

---

## How it works (deeper)

Numpy does not know “kg” vs “days.” It only knows slots.

```
[ a0, a1 ] + [ b0, b1 ] = [ a0+b0, a1+b1 ]
```

A **feature** is one slot with a name you remember. ml-04 stacks many such lists into a table. ml-03 mixes a list with knobs using a dot product.

---

## Common pitfalls

1. **Arrows look tiny or clip.** The axes are fixed `-1` to `8`. If you experiment with huge numbers, raise `set_xlim` / `set_ylim` too.
2. **You added `[3, 1] + [1, 4]` as `3+1+4` into one number.** That is not vector add. Two slots in, two slots out.
3. **You treated length as “the sum of the slots.”** Sum of `[3, 1]` is 4; length is ~3.16. Different jobs.

---

## Knowledge check

1. What is `[1, 2] + [3, 4]`?
2. What is `2 * [1, 3]`?
3. In this lab, what do the two slots of A mean?
4. Why is `[3, 1]` not the same vector as `[1, 3]`?

<details>
<summary>Answers</summary>

1. `[4, 6]`
2. `[2, 6]`
3. First slot is weight-in-kg (idea); second is delay-in-days (idea).
4. The features would be swapped. Order is meaning.

</details>

---

## Recap

- **You saw** arrows add tip-to-tail and print `A+B = [4. 5.]`.
- **You understand** a vector as an ordered feature list.
- **Next** you mix a list with knobs: the dot product.

Next: `ml-03-dot-product-weighted-mix`

---

## Stretch goal

Print `3 * b` in `lab_vectors` next to `2 * A` (`print("3 * B =", 3 * b)`).

- **Expect:** `[3, 12]`
- Remove the extra print when you are done.

---

## Feedback

Could you redo this lab from memory? Note **ml-02**, the step, expected vs saw.
