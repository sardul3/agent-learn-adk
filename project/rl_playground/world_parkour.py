"""World 2 — Jump the warehouse crates.

A side-scroller. The agent only needs to know: am I in the air, how soon is the next crate, how tall is it?
"""

from __future__ import annotations

import numpy as np
import pygame

from viz import DIRT, GOLD, GRASS, INK, NAVY, SKY


N_DIST = 8
N_H = 3


class ParkourWorld:
    name = "2  Jump the crates"
    concept = "Timing: the same jump is genius or suicide depending on distance."
    n_states = 2 * N_DIST * N_H
    n_actions = 2  # 0 stay/run, 1 jump

    def __init__(self, rng: np.random.Generator):
        self.rng = rng
        self.x = 0.0
        self.y = 0.0
        self.vy = 0.0
        self.air = False
        self.obstacles: list[tuple[float, int]] = []
        self.alive = True
        self.steps = 0
        self.cleared = 0
        self._credited: set[int] = set()

    def encode(self) -> int:
        nxt = self._next()
        if nxt is None:
            dist_bin, h = N_DIST - 1, 0
        else:
            ox, h = nxt
            dist = max(0.0, ox - self.x)
            dist_bin = min(N_DIST - 1, int(dist / 28))
        air = 1 if self.air else 0
        return (air * N_DIST + dist_bin) * N_H + h

    def _next(self) -> tuple[float, int] | None:
        ahead = [o for o in self.obstacles if o[0] + 28 >= self.x]
        if not ahead:
            return None
        return min(ahead, key=lambda o: o[0])

    def reset(self) -> int:
        self.x = 80.0
        self.y = 0.0
        self.vy = 0.0
        self.air = False
        self.alive = True
        self.steps = 0
        self.cleared = 0
        self._credited = set()
        self.obstacles = []
        cursor = 220.0
        for _ in range(12):
            cursor += float(self.rng.integers(90, 170))
            h = int(self.rng.integers(1, N_H))
            self.obstacles.append((cursor, h))
        return self.encode()

    def step(self, action: int) -> tuple[int, float, bool, dict]:
        if action == 1 and not self.air:
            self.vy = 11.0
            self.air = True
        self.x += 4.6
        if self.air:
            self.y += self.vy
            self.vy -= 0.72
            if self.y <= 0:
                self.y = 0
                self.vy = 0
                self.air = False
        self.steps += 1
        reward = 0.4
        for i, (ox, h) in enumerate(self.obstacles):
            crate_h = 28 * h
            if ox <= self.x <= ox + 26 and self.y < crate_h - 4:
                self.alive = False
                return self.encode(), -60.0, True, {"animating": True}
            if i not in self._credited and self.x > ox + 26 and self.y >= 0:
                reward += 8.0
                self.cleared += 1
                self._credited.add(i)
        if self.x > self.obstacles[-1][0] + 80:
            return self.encode(), 40.0, True, {"animating": True}
        if self.steps > 400:
            return self.encode(), -5.0, True, {"animating": True}
        return self.encode(), reward, False, {"animating": True}

    def draw(self, screen: pygame.Surface, font: pygame.font.Font, q_row: np.ndarray) -> None:
        pygame.draw.rect(screen, SKY, (0, 0, 800, 360))
        pygame.draw.rect(screen, GRASS, (0, 360, 800, 200))
        pygame.draw.rect(screen, DIRT, (0, 430, 800, 14))
        cam = self.x - 140
        for ox, h in self.obstacles:
            sx = int(ox - cam)
            crate_h = 28 * h
            pygame.draw.rect(screen, (160, 90, 50), (sx, 430 - crate_h, 26, crate_h), border_radius=3)
            pygame.draw.rect(screen, (120, 60, 30), (sx, 430 - crate_h, 26, crate_h), 2, border_radius=3)
        ax = int(self.x - cam)
        ay = int(430 - 18 - self.y)
        pygame.draw.circle(screen, (40, 80, 160), (ax, ay), 14)
        pygame.draw.circle(screen, GOLD, (ax + 4, ay - 3), 3)
        labels = ["run", "JUMP"]
        for i, lab in enumerate(labels):
            val = q_row[i]
            color = GOLD if i == int(np.argmax(q_row)) else INK
            screen.blit(font.render(f"{lab}: {val:6.1f}", True, color), (20, 16 + i * 22))
        screen.blit(font.render(f"crates cleared this run: {self.cleared}", True, NAVY), (20, 64))
