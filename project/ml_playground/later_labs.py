#!/usr/bin/env python3
"""M4–M12 labs: unsupervised, NLP, tiny nets, RNN, images, video, attention, LM, capstone."""

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
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.ensemble import IsolationForest
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import make_pipeline

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from meridian_data import TICKET_TEXTS, scan_times, skus, tickets  # noqa: E402


def lab_kmeans() -> None:
    df = skus()
    km = KMeans(n_clusters=3, n_init=10, random_state=0).fit(df[["length_cm", "weight_kg"]])
    fig, ax = plt.subplots()
    ax.scatter(df["length_cm"], df["weight_kg"], c=km.labels_, cmap="tab10")
    ax.scatter(*km.cluster_centers_.T, marker="x", s=80, color="k")
    ax.set_title("ml-19: three piles of SKUs (tiny / mid / bulky)")
    fig.tight_layout()
    plt.show()
    print("centers", np.round(km.cluster_centers_, 2))


def lab_pca() -> None:
    df = skus()
    X = df[["length_cm", "weight_kg"]].to_numpy()
    Xs = (X - X.mean(0)) / X.std(0)
    z = PCA(2).fit_transform(Xs)
    fig, ax = plt.subplots()
    ax.scatter(z[:, 0], z[:, 1], c=df["true_group"], cmap="tab10")
    ax.set_title("ml-20: PCA rotates so the spread is easy to see")
    ax.set_xlabel("pc1")
    ax.set_ylabel("pc2")
    fig.tight_layout()
    plt.show()


def lab_anomaly() -> None:
    t = scan_times()
    iso = IsolationForest(contamination=0.03, random_state=0).fit(t.reshape(-1, 1))
    flag = iso.predict(t.reshape(-1, 1)) == -1
    print("flagged indices", np.where(flag)[0], "values", t[flag])
    fig, ax = plt.subplots()
    ax.plot(t)
    ax.scatter(np.where(flag)[0], t[flag], color="C3", zorder=3)
    ax.set_title("ml-21: weird scan seconds")
    fig.tight_layout()
    plt.show()


def lab_tokens() -> None:
    text = TICKET_TEXTS[0][0]
    toks = text.lower().split()
    vocab = sorted(set(toks))
    print("text:", text)
    print("tokens:", toks)
    print("vocab:", vocab)


def lab_bow() -> None:
    texts = [t for t, _ in TICKET_TEXTS]
    v = CountVectorizer()
    X = v.fit_transform(texts)
    print("vocab", v.get_feature_names_out()[:12], "...")
    print("first row bag", X[0].toarray())


def lab_tfidf() -> None:
    texts = [t for t, _ in TICKET_TEXTS]
    v = TfidfVectorizer(ngram_range=(1, 2))
    X = v.fit_transform(texts)
    print("ngrams sample", list(v.get_feature_names_out())[:15])
    print("row0 nonzero", X[0].nnz)


def lab_nb() -> None:
    texts = [t for t, _ in TICKET_TEXTS]
    y = [lab for _, lab in TICKET_TEXTS]
    clf = make_pipeline(TfidfVectorizer(), MultinomialNB()).fit(texts, y)
    for q in ("where is my box", "I want my money back", "the carton is crushed"):
        print(q, "->", clf.predict([q])[0], np.round(clf.predict_proba([q])[0], 3))


def lab_vectors_words() -> None:
    # Tiny co-occurrence: words that sit together get similar 2D dots.
    pairs = [("refund", "money"), ("refund", "back"), ("smash", "dented"), ("smash", "crushed"), ("where", "order"), ("where", "tracking")]
    vocab = sorted({w for p in pairs for w in p})
    idx = {w: i for i, w in enumerate(vocab)}
    M = np.zeros((len(vocab), len(vocab)))
    for a, b in pairs:
        M[idx[a], idx[b]] += 1
        M[idx[b], idx[a]] += 1
    z = PCA(2).fit_transform(M)
    fig, ax = plt.subplots()
    ax.scatter(z[:, 0], z[:, 1])
    for w, (x, y) in zip(vocab, z):
        ax.text(x, y, w)
    ax.set_title("ml-26: nearby meaning ≈ nearby dots (toy)")
    fig.tight_layout()
    plt.show()


def _relu(z):
    return np.maximum(0, z)


def lab_neuron() -> None:
    x = np.array([2.0, 0.5])  # weight, delay
    w = np.array([1.5, -0.8])
    b = 0.2
    z = float(w @ x + b)
    print("z (mix) =", z, "relu =", max(0.0, z), "sigmoid ≈", 1 / (1 + np.exp(-z)))


def lab_relu_stack() -> None:
    rng = np.random.default_rng(0)
    X = rng.normal(size=(200, 2))
    y = ((X[:, 0] ** 2 + X[:, 1] ** 2) > 1.2).astype(float).reshape(-1, 1)
    W1 = rng.normal(scale=0.8, size=(2, 6))
    W2 = rng.normal(scale=0.8, size=(6, 1))
    lr = 0.15
    losses = []
    for _ in range(400):
        pre = X @ W1
        h = _relu(pre)
        z = h @ W2
        p = 1 / (1 + np.exp(-z))
        loss = float(np.mean((p - y) ** 2))
        losses.append(loss)
        dL_dp = 2.0 * (p - y) / len(y)
        dL_dz = dL_dp * p * (1 - p)
        dW2 = h.T @ dL_dz
        dL_dh = dL_dz @ W2.T
        dW1 = X.T @ (dL_dh * (pre > 0))
        W2 -= lr * dW2
        W1 -= lr * dW1
    fig, ax = plt.subplots()
    ax.plot(losses)
    ax.set_title("ml-28: stacked ReLU can bend a circle-ish rule (loss should fall)")
    ax.set_xlabel("step")
    fig.tight_layout()
    plt.show()
    print("start loss", losses[0], "end", losses[-1])


def lab_backprop() -> None:
    # One hidden ReLU, one output. Four numbers walked in the lesson.
    x, w1, w2, y = 2.0, 0.5, -0.4, 1.0
    h = max(0.0, w1 * x)
    yhat = w2 * h
    loss = 0.5 * (yhat - y) ** 2
    dloss_dyhat = yhat - y
    dloss_dw2 = dloss_dyhat * h
    dloss_dh = dloss_dyhat * w2
    dloss_dw1 = dloss_dh * (x if w1 * x > 0 else 0.0)
    print("forward h", h, "yhat", yhat, "loss", loss)
    print("dL/dw2", dloss_dw2, "dL/dw1", dloss_dw1)
    lr = 0.1
    print("new w2", w2 - lr * dloss_dw2, "new w1", w1 - lr * dloss_dw1)


def lab_dropout() -> None:
    rng = np.random.default_rng(1)
    n = 40
    x = np.linspace(-1, 1, n)
    y = np.sin(3 * x) + rng.normal(0, 0.15, n)
    # overfit poly
    c_hi = np.polyfit(x, y, 12)
    fig, ax = plt.subplots()
    xs = np.linspace(-1, 1, 100)
    ax.scatter(x, y)
    ax.plot(xs, np.polyval(c_hi, xs), label="memorizes (high variance)")
    ax.plot(xs, np.sin(3 * xs), label="true wave")
    ax.legend()
    ax.set_title("ml-30: dropout idea — do not trust one wiggly teammate")
    fig.tight_layout()
    plt.show()


def lab_numpy_net() -> None:
    rng = np.random.default_rng(2)
    X = rng.normal(size=(80, 2))
    y = (X[:, 0] + 0.5 * X[:, 1] > 0).astype(float)
    W = rng.normal(size=(2, 1)) * 0.1
    b = 0.0
    losses = []
    for _ in range(200):
        z = X @ W + b
        p = 1 / (1 + np.exp(-z)).ravel()
        loss = np.mean((p - y) ** 2)
        losses.append(loss)
        grad = ((p - y) * p * (1 - p)).reshape(-1, 1)
        W -= 0.5 * X.T @ grad / len(X)
        b -= 0.5 * float(grad.mean())
    print("loss start/end", losses[0], losses[-1])
    try:
        import torch
        from torch import nn

        net = nn.Linear(2, 1)
        opt = torch.optim.SGD(net.parameters(), lr=0.2)
        xt = torch.tensor(X, dtype=torch.float32)
        yt = torch.tensor(y, dtype=torch.float32).view(-1, 1)
        last = None
        for _ in range(200):
            opt.zero_grad()
            loss = nn.functional.mse_loss(torch.sigmoid(net(xt)), yt)
            loss.backward()
            opt.step()
            last = float(loss)
        print("torch cpu end loss", last)
    except Exception as e:
        print("torch skipped:", type(e).__name__, "— numpy path already trained.")


def lab_order() -> None:
    a = "late smashed"
    b = "smashed late"
    print("bag-of-words cannot tell these apart:", a, "vs", b)
    print("RNN / transformers can, because they read left to right (or with positions).")


def lab_rnn() -> None:
    rng = np.random.default_rng(0)
    # toy: codes like A1-B2
    vocab = list("ABC123-")
    stoi = {c: i for i, c in enumerate(vocab)}
    Wxh = rng.normal(scale=0.2, size=(len(vocab), 6))
    Whh = rng.normal(scale=0.2, size=(6, 6))
    h = np.zeros(6)
    text = "A1-B2"
    hs = []
    for ch in text:
        x = np.zeros(len(vocab))
        x[stoi[ch]] = 1
        h = np.tanh(x @ Wxh + h @ Whh)
        hs.append(h.copy())
    H = np.stack(hs)
    fig, ax = plt.subplots()
    ax.imshow(H.T, aspect="auto", cmap="coolwarm")
    ax.set_xticks(range(len(text)), list(text))
    ax.set_ylabel("hidden unit")
    ax.set_title("ml-33: hidden state as we read a location code")
    fig.tight_layout()
    plt.show()


def lab_lstm() -> None:
    print("LSTM gates (plain):")
    print("forget: how much old memory to drop")
    print("input: how much new fact to write")
    print("output: how much memory to show now")
    print("Vanishing: if you multiply 0.7 ten times you get", round(0.7**10, 4), "— early letters fade in a vanilla RNN.")


def _box(dent: bool, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    img = np.ones((16, 16)) * 0.85
    img[3:13, 3:13] = 0.6
    if dent:
        img[7:12, 8:14] = 0.25
    img += rng.normal(0, 0.03, img.shape)
    return np.clip(img, 0, 1)


def lab_pixels() -> None:
    img = _box(True, 0)
    print("shape", img.shape, "min/max", img.min(), img.max())
    fig, ax = plt.subplots()
    ax.imshow(img, cmap="gray", vmin=0, vmax=1)
    ax.set_title("ml-35: a dented box is just a grid of brightness")
    fig.tight_layout()
    plt.show()


def lab_conv() -> None:
    img = _box(True, 1)
    k = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]], dtype=float)  # vertical edge stamp
    out = np.zeros((14, 14))
    for i in range(14):
        for j in range(14):
            out[i, j] = np.sum(img[i : i + 3, j : j + 3] * k)
    fig, ax = plt.subplots(1, 2)
    ax[0].imshow(img, cmap="gray")
    ax[0].set_title("box")
    ax[1].imshow(out, cmap="coolwarm")
    ax[1].set_title("ml-36: stamp (vertical edges)")
    fig.tight_layout()
    plt.show()


def lab_pool() -> None:
    img = _box(True, 2)
    pooled = img.reshape(8, 2, 8, 2).max(axis=(1, 3))
    fig, ax = plt.subplots(1, 2)
    ax[0].imshow(img, cmap="gray")
    ax[1].imshow(pooled, cmap="gray")
    ax[0].set_title("16x16")
    ax[1].set_title("ml-37: 8x8 max-pool (keeps the dent, fewer numbers)")
    fig.tight_layout()
    plt.show()


def lab_dented() -> None:
    X = np.stack([_box(i % 2 == 1, i).ravel() for i in range(40)])
    y = np.array([i % 2 for i in range(40)])
    w = np.zeros(X.shape[1])
    for _ in range(80):
        pred = 1 / (1 + np.exp(-(X @ w)))
        w -= 0.4 * X.T @ (pred - y) / len(y)
    acc = ((X @ w > 0).astype(int) == y).mean()
    print("linear-on-pixels acc", acc, "(toy: dent is a dark patch — a stamp would be the real CNN idea)")


def lab_video_frames() -> None:
    frames = [_box(False, t) + 0.05 * t / 20 for t in range(8)]
    fig, axes = plt.subplots(1, 8, figsize=(10, 2))
    for ax, im in zip(axes, frames):
        ax.imshow(np.clip(im, 0, 1), cmap="gray")
        ax.axis("off")
    fig.suptitle("ml-39: video = pictures in time")
    fig.tight_layout()
    plt.show()


def lab_sample_k() -> None:
    print("30 fps * 10 seconds = 300 frames. CPU lab uses every 15th → 20 frames.")
    print("That is 'sample every k'. You keep the story, drop the blur of extras.")


def lab_jam() -> None:
    rng = np.random.default_rng(0)
    moving = np.stack([np.roll(_box(False, 0), t, axis=1) for t in range(12)])
    jammed = np.stack([_box(False, 0) for _ in range(12)])
    motion_m = np.mean(np.abs(np.diff(moving, axis=0)))
    motion_j = np.mean(np.abs(np.diff(jammed, axis=0)))
    print("mean frame-to-frame change  moving", round(motion_m, 4), "jammed", round(motion_j, 4))
    print("Rule: if change is tiny, Maya's chute is jammed.")


def lab_attn() -> None:
    rng = np.random.default_rng(0)
    # 4 tokens, 3 dim
    X = rng.normal(size=(4, 3))
    scores = X @ X.T
    # softmax rows
    e = np.exp(scores - scores.max(1, keepdims=True))
    A = e / e.sum(1, keepdims=True)
    print("attention weights (who looks at whom)")
    print(np.round(A, 2))
    fig, ax = plt.subplots()
    ax.imshow(A, cmap="magma")
    ax.set_xticks(range(4), list("ABCD"))
    ax.set_yticks(range(4), list("ABCD"))
    ax.set_title("ml-42: darker = more attention")
    fig.tight_layout()
    plt.show()


def lab_qkv() -> None:
    rng = np.random.default_rng(1)
    X = rng.normal(size=(4, 3))
    Wq = rng.normal(size=(3, 3))
    Wk = rng.normal(size=(3, 3))
    Wv = rng.normal(size=(3, 3))
    Q, K, V = X @ Wq, X @ Wk, X @ Wv
    print("Q query notebook shape", Q.shape, "K key", K.shape, "V value", V.shape)
    scale = np.sqrt(3)
    A = np.exp(Q @ K.T / scale)
    A = A / A.sum(1, keepdims=True)
    out = A @ V
    print("mixed values shape", out.shape)


def lab_pos() -> None:
    n, d = 8, 4
    pos = np.arange(n)[:, None]
    i = np.arange(d)[None, :]
    pe = np.sin(pos / (10000 ** (i / d)))
    fig, ax = plt.subplots()
    ax.imshow(pe, cmap="coolwarm")
    ax.set_title("ml-44: position tags so 'first word' ≠ 'last word'")
    fig.tight_layout()
    plt.show()


def lab_tiny_tf() -> None:
    rng = np.random.default_rng(0)
    vocab = "abc"
    stoi = {c: i for i, c in enumerate(vocab)}
    data = np.array([stoi[c] for c in "abcabcabc"])
    # next-char counts
    C = np.zeros((3, 3))
    for i in range(len(data) - 1):
        C[data[i], data[i + 1]] += 1
    P = C / np.maximum(C.sum(1, keepdims=True), 1)
    print("P[next|now] rows a,b,c")
    print(np.round(P, 2))
    print("This is a one-step transformer-shaped table. Real transformers mix with attention first.")


def lab_temp() -> None:
    logits = np.array([2.0, 1.0, 0.1])
    for T in (0.2, 1.0, 2.0):
        p = np.exp(logits / T)
        p = p / p.sum()
        print(f"T={T} probs", np.round(p, 3))
    print("Low T = pick the winner. High T = more random. T is not 'degrees outside'.")


def lab_three_ways() -> None:
    print("Prompt: write instructions, freeze the model.")
    print("Fine-tune: change weights on your texts (CPU: tiny model only).")
    print("RAG: keep weights, fetch Maya policy, then generate — this is Lesson 18 in the ADK track.")


def lab_tiny_gpt() -> None:
    rng = np.random.default_rng(4)
    text = "pack the box. scan the box. dock the van. pack the box. "
    chars = sorted(set(text))
    stoi = {c: i for i, c in enumerate(chars)}
    itos = {i: c for c, i in stoi.items()}
    data = [stoi[c] for c in text]
    W = rng.normal(scale=0.01, size=(len(chars), len(chars)))
    lr = 0.5
    for _ in range(200):
        loss = 0.0
        g = np.zeros_like(W)
        for i in range(len(data) - 1):
            logits = W[data[i]]
            e = np.exp(logits - logits.max())
            p = e / e.sum()
            y = data[i + 1]
            loss += -np.log(p[y] + 1e-8)
            dlogits = p
            dlogits[y] -= 1
            g[data[i]] += dlogits
        W -= lr * g / (len(data) - 1)
    # sample
    ix = stoi["p"]
    out = ["p"]
    for _ in range(40):
        p = np.exp(W[ix] - W[ix].max())
        p = p / p.sum()
        ix = int(rng.choice(len(chars), p=p))
        out.append(itos[ix])
    print("sample:", "".join(out))
    print("This is a bigram brain. A GPT stacks attention on top of the same next-char job.")


def lab_youbot() -> None:
    path = ROOT / "my_voice.txt"
    if not path.exists():
        path.write_text(
            "hey — yeah I can look that up.\n"
            "give me the order id and I'll check scans.\n"
            "ugh late again? I'll pull the policy.\n",
            encoding="utf-8",
        )
        print("Wrote a starter", path, "— replace with YOUR sentences, then rerun.")
    text = path.read_text(encoding="utf-8").lower()
    chars = sorted(set(text)) or [" "]
    stoi = {c: i for i, c in enumerate(chars)}
    itos = {i: c for c, i in stoi.items()}
    data = [stoi[c] for c in text]
    W = np.zeros((len(chars), len(chars)))
    for i in range(len(data) - 1):
        W[data[i], data[i + 1]] += 1
    W = W / np.maximum(W.sum(1, keepdims=True), 1)
    rng = np.random.default_rng(0)
    ix = data[0]
    out = [itos[ix]]
    for _ in range(80):
        ix = int(rng.choice(len(chars), p=W[ix] if W[ix].sum() else None))
        out.append(itos[ix])
    print("cousin-of-you sample:\n", "".join(out))
    print("Eval: would Maya send this to a customer? If no, do not ship it. Quality is 'cousin', not clone.")


def lab_q_vs_net() -> None:
    print("Tabular Q: one spreadsheet cell per (state, action). See project/rl_playground.")
    print("Neural policy: a net outputs action scores for states you have NEVER stored.")
    print("Same loop: act, reward, update. Different memory.")


def lab_capstone() -> None:
    df = tickets(40)
    texts = [t for t, _ in TICKET_TEXTS]
    y = [lab for _, lab in TICKET_TEXTS]
    clf = make_pipeline(TfidfVectorizer(), MultinomialNB()).fit(texts, y)
    img = _box(True, 9)
    dent_score = float((img < 0.4).mean())
    delay = float(df["delay_days"].iloc[0])
    intent = clf.predict(["the carton is crushed and I want a refund"])[0]
    print("intent", intent, "dent_score", round(dent_score, 3), "delay_days", delay)
    if intent == "damage" and dent_score > 0.02:
        print("suggested: open damage path, ask for photo — CPU models only, not Gemini.")
    else:
        print("suggested: check scans first.")
    print("ADK track: same ticket would call tools + Gemini. This capstone is the 'feel the parts' version.")


LABS = {
    "kmeans": lab_kmeans,
    "pca": lab_pca,
    "anomaly": lab_anomaly,
    "tokens": lab_tokens,
    "bow": lab_bow,
    "tfidf": lab_tfidf,
    "nb": lab_nb,
    "wvec": lab_vectors_words,
    "neuron": lab_neuron,
    "relustack": lab_relu_stack,
    "backprop": lab_backprop,
    "dropout": lab_dropout,
    "numpynet": lab_numpy_net,
    "order": lab_order,
    "rnn": lab_rnn,
    "lstm": lab_lstm,
    "pixels": lab_pixels,
    "conv": lab_conv,
    "pool": lab_pool,
    "dented": lab_dented,
    "vframes": lab_video_frames,
    "samplek": lab_sample_k,
    "jam": lab_jam,
    "attn": lab_attn,
    "qkv": lab_qkv,
    "pos": lab_pos,
    "tinytf": lab_tiny_tf,
    "temp": lab_temp,
    "threeways": lab_three_ways,
    "tinygpt": lab_tiny_gpt,
    "youbot": lab_youbot,
    "qvnet": lab_q_vs_net,
    "capstone": lab_capstone,
}


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("lab", choices=sorted(LABS))
    args = p.parse_args()
    LABS[args.lab]()


if __name__ == "__main__":
    main()
