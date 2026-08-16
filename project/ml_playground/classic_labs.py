#!/usr/bin/env python3
"""M1–M3: hygiene, regression, classification on Maya tickets/orders."""

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
from sklearn.linear_model import LinearRegression, LogisticRegression, Ridge
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    mean_squared_error,
    precision_score,
    recall_score,
)
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import PolynomialFeatures, StandardScaler
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.utils.class_weight import compute_class_weight

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from meridian_data import packing_orders, tickets  # noqa: E402


def lab_split() -> None:
    df = packing_orders(80)
    tr, te = train_test_split(df, test_size=0.25, random_state=0)
    print(f"train rows {len(tr)}  test rows {len(te)}")
    print("Never tune on test. Test is the exam you take once.")
    print(tr.head(3).to_string(index=False))


def lab_leak() -> None:
    dirty = tickets(200, leak=True)
    clean = tickets(200, leak=False)
    y = dirty["became_refund"]
    for name, cols in (
        ("LEAKY (includes refund_already_paid)", ["delay_days", "price_usd", "angry_words", "refund_already_paid"]),
        ("honest", ["delay_days", "price_usd", "angry_words"]),
    ):
        X = dirty[cols] if "refund" in cols[-1] else clean[cols]
        Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.3, random_state=1)
        clf = LogisticRegression(max_iter=200).fit(Xtr, ytr)
        print(f"{name:40} test acc {accuracy_score(yte, clf.predict(Xte)):.3f}")
    print("Leaky accuracy is a lie. The paid flag is the answer sheet.")


def lab_scale() -> None:
    df = packing_orders(80)
    X = df[["weight_kg", "hour"]].to_numpy()
    print("raw hour std", X[:, 1].std(), "weight std", X[:, 0].std())
    Xs = StandardScaler().fit_transform(X)
    print("after scale, both columns std ≈", Xs.std(axis=0))
    fig, ax = plt.subplots(1, 2, figsize=(8, 3))
    ax[0].scatter(X[:, 0], X[:, 1])
    ax[0].set_title("raw (hour dwarfs weight)")
    ax[1].scatter(Xs[:, 0], Xs[:, 1])
    ax[1].set_title("scaled")
    fig.suptitle("ml-08: scaling. Plots that stretch axes lie about 'importance'.")
    fig.tight_layout()
    plt.show()


def lab_bias_var() -> None:
    rng = np.random.default_rng(0)
    x = np.linspace(0, 1, 30)
    y = np.sin(2 * np.pi * x) + rng.normal(0, 0.15, size=30)
    fig, axes = plt.subplots(1, 3, figsize=(9, 3), sharey=True)
    for ax, deg, title in zip(axes, [1, 3, 12], ["high bias (too simple)", "just enough", "high variance (memorizes)"]):
        c = np.polyfit(x, y, deg)
        xs = np.linspace(0, 1, 80)
        ax.scatter(x, y, s=12)
        ax.plot(xs, np.polyval(c, xs), color="C1")
        ax.set_title(title)
    fig.suptitle("ml-09: dartboard idea — always-left vs scattered around the bull")
    fig.tight_layout()
    plt.show()


def lab_reg1() -> None:
    df = packing_orders(80)
    X = df[["weight_kg"]]
    y = df["pack_minutes"]
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.25, random_state=0)
    m = LinearRegression().fit(Xtr, ytr)
    pred = m.predict(Xte)
    print(f"sklearn m={m.coef_[0]:.3f} b={m.intercept_:.3f}  test MSE {mean_squared_error(yte, pred):.3f}")
    fig, ax = plt.subplots()
    ax.scatter(Xte["weight_kg"], yte, label="test truth")
    ax.scatter(Xte["weight_kg"], pred, marker="x", label="pred")
    ax.set_title("ml-10: one-feature line")
    ax.legend()
    fig.tight_layout()
    plt.show()


def lab_reg_many() -> None:
    df = packing_orders(80)
    X = df[["weight_kg", "zone", "hour"]]
    y = df["pack_minutes"]
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.25, random_state=0)
    m = LinearRegression().fit(Xtr, ytr)
    print("weights", dict(zip(X.columns, np.round(m.coef_, 3))), "b", round(m.intercept_, 3))
    print("test MSE", mean_squared_error(yte, m.predict(Xte)))
    resid = yte - m.predict(Xte)
    fig, ax = plt.subplots()
    ax.scatter(m.predict(Xte), resid)
    ax.axhline(0, color="k", lw=0.8)
    ax.set_xlabel("predicted hours-ish minutes")
    ax.set_ylabel("residual (truth - pred)")
    ax.set_title("ml-11: leftover error should look like a cloud, not a banana")
    fig.tight_layout()
    plt.show()


def lab_poly() -> None:
    df = packing_orders(80)
    x = df[["weight_kg"]]
    y = df["pack_minutes"]
    fig, ax = plt.subplots()
    ax.scatter(x, y, s=14, alpha=0.5)
    xs = np.linspace(float(x.min().iloc[0]), float(x.max().iloc[0]), 50).reshape(-1, 1)
    for d in (1, 4):
        pf = PolynomialFeatures(d, include_bias=False)
        m = LinearRegression().fit(pf.fit_transform(x), y)
        ax.plot(xs, m.predict(pf.transform(xs)), label=f"degree {d}")
    ax.legend()
    ax.set_title("ml-12: extra powers let the line bend — too far and it wiggles")
    fig.tight_layout()
    plt.show()


def lab_ridge() -> None:
    df = packing_orders(80)
    X = df[["weight_kg", "zone", "hour"]]
    y = df["pack_minutes"]
    for a in (0.0, 1.0, 50.0):
        m = Ridge(alpha=a).fit(X, y)
        print(f"alpha={a:5.1f}  weights {np.round(m.coef_, 3)}")
    print("Bigger alpha = shrink weights toward 0 = 'I refuse giant trust in one column.'")


def lab_logistic() -> None:
    df = tickets(200)
    X = df[["delay_days"]]
    y = df["became_refund"]
    clf = LogisticRegression().fit(X, y)
    grid = np.linspace(0, 10, 80).reshape(-1, 1)
    p = clf.predict_proba(grid)[:, 1]
    fig, ax = plt.subplots()
    ax.scatter(X, y, alpha=0.3, label="tickets (0/1)")
    ax.plot(grid, p, color="C1", label="P(refund)")
    ax.set_xlabel("delay_days")
    ax.set_title("ml-14: line, then squash into 0–1 (logistic)")
    ax.legend()
    fig.tight_layout()
    plt.show()


def lab_boundary() -> None:
    df = tickets(200)
    X = df[["delay_days", "angry_words"]]
    y = df["became_refund"]
    clf = LogisticRegression().fit(X, y)
    xx, yy = np.meshgrid(np.linspace(0, 10, 80), np.linspace(0, 12, 80))
    zz = clf.predict(np.c_[xx.ravel(), yy.ravel()]).reshape(xx.shape)
    fig, ax = plt.subplots()
    ax.contourf(xx, yy, zz, alpha=0.25)
    ax.scatter(X["delay_days"], X["angry_words"], c=y, cmap="coolwarm", s=18)
    ax.set_xlabel("delay_days")
    ax.set_ylabel("angry_words")
    ax.set_title("ml-15: decision boundary — two colors of warehouse tickets")
    fig.tight_layout()
    plt.show()


def lab_confusion() -> None:
    df = tickets(200)
    X, y = df[["delay_days", "price_usd", "angry_words"]], df["became_refund"]
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.3, random_state=2)
    clf = LogisticRegression(max_iter=200).fit(Xtr, ytr)
    pred = clf.predict(Xte)
    print("confusion [[tn fp][fn tp]]")
    print(confusion_matrix(yte, pred))
    print("precision", round(precision_score(yte, pred, zero_division=0), 3), "recall", round(recall_score(yte, pred, zero_division=0), 3))
    print("Maya: false positive = refunded a fine order. false negative = missed a smashed vase.")


def lab_trees() -> None:
    df = tickets(200)
    X, y = df[["delay_days", "price_usd", "angry_words"]], df["became_refund"]
    tree = DecisionTreeClassifier(max_depth=3, random_state=0).fit(X, y)
    forest = RandomForestClassifier(n_estimators=40, random_state=0).fit(X, y)
    print("tree acc", tree.score(X, y), "forest acc", forest.score(X, y))
    print("importances", dict(zip(X.columns, np.round(forest.feature_importances_, 3))))


def lab_imbalance() -> None:
    rng = np.random.default_rng(0)
    # 95% not-refund
    X = rng.normal(size=(200, 2))
    y = np.zeros(200, dtype=int)
    y[:10] = 1
    X[:10] += 2.5
    clf = LogisticRegression().fit(X, y)
    print("always-say-no acc", (y == 0).mean())
    print("naive model acc", clf.score(X, y), "positives predicted", clf.predict(X).sum())
    w = compute_class_weight("balanced", classes=np.array([0, 1]), y=y)
    clf2 = LogisticRegression(class_weight="balanced").fit(X, y)
    print("balanced weights", w, "positives predicted", clf2.predict(X).sum())


LABS = {
    "split": lab_split,
    "leak": lab_leak,
    "scale": lab_scale,
    "biasvar": lab_bias_var,
    "reg1": lab_reg1,
    "regmany": lab_reg_many,
    "poly": lab_poly,
    "ridge": lab_ridge,
    "logistic": lab_logistic,
    "boundary": lab_boundary,
    "confusion": lab_confusion,
    "trees": lab_trees,
    "imbalance": lab_imbalance,
}


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("lab", choices=sorted(LABS))
    args = p.parse_args()
    LABS[args.lab]()


if __name__ == "__main__":
    main()
