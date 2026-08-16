#!/usr/bin/env python3
"""M0 visuals: Maya packing minutes. Matplotlib only (no pygame.font).

    python m0_labs.py model
    python m0_labs.py slope
    python m0_labs.py vectors
    python m0_labs.py dot
    python m0_labs.py matrix
    python m0_labs.py bowl
    python m0_labs.py fit
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import matplotlib

if os.environ.get("ML_HEADLESS") == "1":
    matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.widgets import Slider

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from meridian_data import packing_orders  # noqa: E402


def lab_model() -> None:
    df = packing_orders(12)
    maya = 5 + 2 * df["weight_kg"]  # a human rule of thumb
    err = maya - df["pack_minutes"]
    print(df.assign(maya_guess=np.round(maya, 2), error=np.round(err, 2)).to_string(index=False))
    print()
    print(f"mean error (Maya minus truth): {err.mean():.2f} minutes")
    print("A model is any recipe that turns inputs into a guess. Maya's recipe is already a model.")
    fig, ax = plt.subplots()
    ax.scatter(df["weight_kg"], df["pack_minutes"], label="true pack minutes", zorder=3)
    ax.scatter(df["weight_kg"], maya, marker="x", label="Maya guess", zorder=3)
    ax.set_xlabel("weight_kg")
    ax.set_ylabel("minutes")
    ax.set_title("ml-00: two guesses per box")
    ax.legend()
    fig.tight_layout()
    plt.show()


def lab_slope() -> None:
    df = packing_orders(60)
    x = df["weight_kg"].to_numpy()
    y = df["pack_minutes"].to_numpy()
    fig, ax = plt.subplots()
    plt.subplots_adjust(bottom=0.25)
    ax.scatter(x, y, s=18, alpha=0.7)
    (line,) = ax.plot([], [], color="C1", lw=2)
    ax.set_xlabel("weight_kg")
    ax.set_ylabel("pack_minutes")
    ax.set_title("ml-01: drag slope (m) and intercept (b). Guess = m*weight + b")

    ax_m = fig.add_axes([0.15, 0.12, 0.7, 0.03])
    ax_b = fig.add_axes([0.15, 0.06, 0.7, 0.03])
    s_m = Slider(ax_m, "slope m", 0.0, 4.0, valinit=1.0)
    s_b = Slider(ax_b, "intercept b", -2.0, 12.0, valinit=2.0)

    def redraw(_=None) -> None:
        xs = np.linspace(x.min(), x.max(), 50)
        line.set_data(xs, s_m.val * xs + s_b.val)
        fig.canvas.draw_idle()

    s_m.on_changed(redraw)
    s_b.on_changed(redraw)
    redraw()
    plt.show()


def lab_vectors() -> None:
    fig, ax = plt.subplots()
    ax.set_xlim(-1, 8)
    ax.set_ylim(-1, 8)
    ax.set_aspect("equal")
    ax.grid(True, alpha=0.3)
    ax.set_xlabel("weight_kg (idea: first number)")
    ax.set_ylabel("delay_days (idea: second number)")
    ax.set_title("ml-02: a vector is an ordered list. Arrows add tip-to-tail.")
    a = np.array([3.0, 1.0])
    b = np.array([1.0, 4.0])
    ax.arrow(0, 0, *a, head_width=0.15, color="C0", length_includes_head=True, label="order A")
    ax.arrow(*a, *b, head_width=0.15, color="C1", length_includes_head=True, label="add delay vector")
    ax.arrow(0, 0, *(a + b), head_width=0.15, color="C2", length_includes_head=True, linestyle="--")
    ax.legend()
    print("length of A:", float(np.sqrt((a**2).sum())))
    print("A + B =", a + b)
    print("2 * A =", 2 * a)
    fig.tight_layout()
    plt.show()


def lab_dot() -> None:
    fig, ax = plt.subplots()
    plt.subplots_adjust(bottom=0.28)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 12)
    ax.set_xlabel("weight_kg")
    ax.set_ylabel("guessed pack minutes")
    x = packing_orders(40)["weight_kg"].to_numpy()
    y_true = packing_orders(40)["pack_minutes"].to_numpy()
    ax.scatter(x, y_true, s=16, alpha=0.6, label="truth")
    (line,) = ax.plot([], [], color="C3", lw=2, label="w0 + w1*weight")
    txt = ax.text(0.02, 0.95, "", transform=ax.transAxes, va="top")
    ax.legend(loc="lower right")
    ax.set_title("ml-03: dot product = mix. guess = w0*1 + w1*weight")

    ax0 = fig.add_axes([0.15, 0.14, 0.7, 0.03])
    ax1 = fig.add_axes([0.15, 0.08, 0.7, 0.03])
    s0 = Slider(ax0, "w0 intercept", -2, 10, valinit=4)
    s1 = Slider(ax1, "w1 weight mix", -1, 4, valinit=1.5)

    def redraw(_=None) -> None:
        xs = np.linspace(x.min(), x.max(), 40)
        ones = np.ones_like(xs)
        w = np.array([s0.val, s1.val])
        guess = ones * w[0] + xs * w[1]
        line.set_data(xs, guess)
        # same as dot: [1, weight] · [w0, w1]
        sample = np.array([1.0, float(x[0])])
        txt.set_text(f"first box dot = {float(sample @ w):.2f} minutes")
        fig.canvas.draw_idle()

    s0.on_changed(redraw)
    s1.on_changed(redraw)
    redraw()
    plt.show()


def lab_matrix() -> None:
    df = packing_orders(20)
    mat = df[["weight_kg", "zone", "hour"]].to_numpy()
    print("Rows = orders. Columns = features.")
    print(np.round(mat[:5], 2))
    fig, ax = plt.subplots()
    im = ax.imshow(mat, aspect="auto", cmap="magma")
    ax.set_xticks([0, 1, 2], ["weight", "zone", "hour"])
    ax.set_ylabel("order row")
    ax.set_title("ml-04: a matrix is a table of numbers")
    fig.colorbar(im, ax=ax, label="value")
    fig.tight_layout()
    plt.show()


def lab_bowl() -> None:
    # Error bowl for guess = m * 5kg  (one knob). True minutes around 13.
    m = np.linspace(-1, 5, 200)
    x = 5.0
    y = 13.0
    mse = (m * x - y) ** 2
    fig, ax = plt.subplots()
    ax.plot(m, mse)
    # gradient descent path
    mk = 0.0
    path_m = [mk]
    path_e = [(mk * x - y) ** 2]
    lr = 0.01
    for _ in range(25):
        grad = 2 * (mk * x - y) * x
        mk = mk - lr * grad
        path_m.append(mk)
        path_e.append((mk * x - y) ** 2)
    ax.plot(path_m, path_e, "o-", color="C1", label="nudges")
    ax.set_xlabel("slope m")
    ax.set_ylabel("squared error for one 5kg box")
    ax.set_title("ml-05: bowl of error. Each nudge follows the slope of the bowl.")
    ax.legend()
    print("started m=0, ended m=", round(mk, 3), "true m would be", y / x)
    fig.tight_layout()
    plt.show()


def lab_fit() -> None:
    df = packing_orders(80)
    x = df["weight_kg"].to_numpy()
    y = df["pack_minutes"].to_numpy()
    m, b = 0.0, 0.0
    lr = 0.01
    hist = []
    for step in range(400):
        pred = m * x + b
        err = pred - y
        m -= lr * (2 / len(x)) * np.sum(err * x)
        b -= lr * (2 / len(x)) * np.sum(err)
        if step % 40 == 0:
            hist.append((step, float(np.mean(err**2)), m, b))
    print("step  mse  m  b")
    for row in hist:
        print(f"{row[0]:4d}  {row[1]:7.3f}  {row[2]:6.3f}  {row[3]:6.3f}")
    print("Maya-ish truth was about m=1.8 b=4 plus zone. You only used weight.")
    fig, ax = plt.subplots()
    ax.scatter(x, y, s=14, alpha=0.6)
    xs = np.linspace(x.min(), x.max(), 40)
    ax.plot(xs, m * xs + b, color="C1", label=f"fit m={m:.2f} b={b:.2f}")
    ax.set_xlabel("weight_kg")
    ax.set_ylabel("pack_minutes")
    ax.set_title("M0 project: fit a line by nudging m and b. No sklearn.")
    ax.legend()
    fig.tight_layout()
    plt.show()


LABS = {
    "model": lab_model,
    "slope": lab_slope,
    "vectors": lab_vectors,
    "dot": lab_dot,
    "matrix": lab_matrix,
    "bowl": lab_bowl,
    "fit": lab_fit,
}


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("lab", choices=sorted(LABS))
    args = p.parse_args()
    LABS[args.lab]()


if __name__ == "__main__":
    main()
