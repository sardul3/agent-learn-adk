"""World 4 — Balance the coffee tray.

A waiter on a skateboard. Tiny leans grow. This is the classic 'stay upright' problem with a face.
"""

from __future__ import annotations

import math

import numpy as np
import pygame

from viz import GOLD, INK, NAVY, SKY


# Bins kept small so tabular Q-learning can fill the spreadsheet in minutes, not hours.
NX, NV, NTH, NW = 5, 5, 7, 5


class BalanceWorld:
    name = "4  Balance the tray"
    concept = "Delayed disaster: a tiny tilt now is a crash three beats later."
    n_states = NX * NV * NTH * NW
    n_actions = 2

    def __init__(self, rng: np.random.Generator):
        self.rng = rng
        self.x = 0.0
        self.v = 0.0
        self.th = 0.0
        self.w = 0.0
        self.steps = 0
        self.last_action = 0

    def _bin(self, val: float, lo: float, hi: float, n: int) -> int:
        t = (val - lo) / (hi - lo)
        return int(np.clip(math.floor(t * n), 0, n - 1))

    def encode(self) -> int:
        ix = self._bin(self.x, -2.2, 2.2, NX)
        iv = self._bin(self.v, -1.8, 1.8, NV)
        ith = self._bin(self.th, -0.28, 0.28, NTH)
        iw = self._bin(self.w, -1.6, 1.6, NW)
        return ((ix * NV + iv) * NTH + ith) * NW + iw

    def reset(self) -> int:
        self.x = float(self.rng.uniform(-0.15, 0.15))
        self.v = 0.0
        self.th = float(self.rng.uniform(-0.04, 0.04))
        self.w = 0.0
        self.steps = 0
        return self.encode()

    def step(self, action: int) -> tuple[int, float, bool, dict]:
        self.last_action = action
        force = 1.0 if action == 1 else -1.0
        # Cartoon physics, same *shape* as cart-pole: force moves the cart, gravity tips the pole.
        self.v += force * 0.12
        self.x += self.v * 0.04
        self.w += (math.sin(self.th) * 0.9 + force * 0.08) * 0.04
        self.th += self.w * 0.04
        self.steps += 1
        fallen = abs(self.th) > 0.26 or abs(self.x) > 2.1
        if fallen:
            return self.encode(), -40.0, True, {"animating": True}
        if self.steps >= 220:
            return self.encode(), 20.0, True, {"animating": True}
        return self.encode(), 1.0, False, {"animating": True}

    def draw(self, screen: pygame.Surface, font: pygame.font.Font, q_row: np.ndarray) -> None:
        pygame.draw.rect(screen, SKY, (0, 0, 800, 560))
        pygame.draw.rect(screen, (80, 80, 90), (40, 430, 720, 8))
        cx = int(400 + self.x * 140)
        pygame.draw.rect(screen, (40, 80, 160), (cx - 40, 410, 80, 22), border_radius=6)
        pygame.draw.circle(screen, NAVY, (cx - 28, 434), 8)
        pygame.draw.circle(screen, NAVY, (cx + 28, 434), 8)
        pole_len = 140
        tx = cx + math.sin(self.th) * pole_len
        ty = 410 - math.cos(self.th) * pole_len
        pygame.draw.line(screen, (90, 50, 30), (cx, 410), (tx, ty), 6)
        pygame.draw.rect(screen, (240, 230, 210), (tx - 28, ty - 10, 56, 16), border_radius=4)
        pygame.draw.circle(screen, (180, 80, 60), (int(tx - 12), int(ty - 4)), 5)
        pygame.draw.circle(screen, (180, 80, 60), (int(tx + 12), int(ty - 4)), 5)
        names = ["LEFT", "RIGHT"]
        for i, n in enumerate(names):
            color = GOLD if i == int(np.argmax(q_row)) else INK
            screen.blit(font.render(f"{n}: {q_row[i]:6.1f}", True, color), (20, 16 + i * 22))
        screen.blit(font.render(f"balanced for {self.steps} ticks", True, INK), (20, 64))
