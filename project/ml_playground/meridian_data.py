"""Synthetic Meridian warehouse numbers used by every bonus ML lab.

Plain English: fake but consistent orders so you never hunt for a Kaggle dump.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def packing_orders(n: int = 80, seed: int = 7) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    weight_kg = rng.uniform(0.4, 12.0, size=n)
    zone = rng.integers(1, 5, size=n)
    hour = rng.integers(6, 22, size=n)
    # True story Maya does not know: minutes ≈ 4 + 1.8*weight + 0.6*zone + noise
    minutes = 4.0 + 1.8 * weight_kg + 0.6 * zone + rng.normal(0, 0.8, size=n)
    return pd.DataFrame(
        {
            "weight_kg": np.round(weight_kg, 2),
            "zone": zone,
            "hour": hour,
            "pack_minutes": np.round(minutes, 2),
        }
    )


def tickets(n: int = 200, seed: int = 3, leak: bool = False) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    delay = rng.uniform(0, 10, size=n)
    price = rng.uniform(8, 180, size=n)
    words_angry = rng.integers(0, 12, size=n)
    refund = ((delay > 4.5) | (words_angry > 6) | (price > 140)).astype(int)
    refund = np.where(rng.random(n) < 0.08, 1 - refund, refund)
    paid_already = refund.copy()
    df = pd.DataFrame(
        {
            "delay_days": np.round(delay, 2),
            "price_usd": np.round(price, 2),
            "angry_words": words_angry,
            "became_refund": refund,
        }
    )
    if leak:
        df["refund_already_paid"] = paid_already
    return df


def skus(n: int = 90, seed: int = 11) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    # Three real groups: tiny, mid, bulky
    g = rng.integers(0, 3, size=n)
    length = np.where(g == 0, rng.uniform(4, 12, n), np.where(g == 1, rng.uniform(12, 28, n), rng.uniform(28, 60, n)))
    weight = np.where(g == 0, rng.uniform(0.1, 1.2, n), np.where(g == 1, rng.uniform(1, 6, n), rng.uniform(6, 22, n)))
    return pd.DataFrame({"sku": [f"SKU-{i:03d}" for i in range(n)], "length_cm": length, "weight_kg": weight, "true_group": g})


def scan_times(n: int = 120, seed: int = 5) -> np.ndarray:
    rng = np.random.default_rng(seed)
    times = rng.normal(2.4, 0.25, size=n)
    times[17] = 9.8
    times[88] = 0.05
    return times


TICKET_TEXTS = [
    ("where is my order MC-1048292 it has been 6 days", "wismo"),
    ("package still not here tracking frozen", "wismo"),
    ("I want a refund the vase arrived smashed", "refund"),
    ("please refund this late gift it missed the party", "refund"),
    ("box was crushed corner torn item dented", "damage"),
    ("outer carton wet and the bottle leaked", "damage"),
    ("eta for MC-1048001 thanks", "wismo"),
    ("money back now this is unacceptable", "refund"),
    ("photo attached of crushed foam", "damage"),
    ("any scan since yesterday", "wismo"),
]
