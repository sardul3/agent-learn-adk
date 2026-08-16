"""World 5 — Catch the falling packages.

A paddle under a warehouse chute. State is 'where am I' + 'where is the box' + 'how soon'.
"""

from __future__ import annotations

import numpy as np
import pygame

from viz import GOLD, GRASS, INK, NAVY, SKY


N_PADDLE = 7
N_COL = 7
N_ROW = 6


class CatchWorld:
    name = "5  Catch the packages"
    concept = "Tracking: you must move *now* for a box that is still high in the air."
    n_states = N_PADDLE * N_COL * N_ROW
    n_actions = 3  # left, stay, right

    def __init__(self, rng: np.random.Generator):
        self.rng = rng
        self.paddle = 3
        self.col = 3
        self.row = 0
        self.caught = 0
        self.missed = 0
        self.steps = 0
        self.flash = ""

    def encode(self) -> int:
        return (self.paddle * N_COL + self.col) * N_ROW + self.row

    def _spawn(self) -> None:
        self.col = int(self.rng.integers(0, N_COL))
        self.row = 0

    def reset(self) -> int:
        self.paddle = 3
        self.caught = 0
        self.missed = 0
        self.steps = 0
        self.flash = ""
        self._spawn()
        return self.encode()

    def step(self, action: int) -> tuple[int, float, bool, dict]:
        if action == 0:
            self.paddle = max(0, self.paddle - 1)
        elif action == 2:
            self.paddle = min(N_PADDLE - 1, self.paddle + 1)
        self.row += 1
        self.steps += 1
        reward = -0.05
        if self.row >= N_ROW - 1:
            if self.paddle == self.col:
                reward = 12.0
                self.caught += 1
                self.flash = "CATCH"
            else:
                reward = -14.0
                self.missed += 1
                self.flash = "MISS"
            self._spawn()
        if self.missed >= 8 or self.steps >= 180:
            return self.encode(), reward, True, {"animating": True}
        return self.encode(), reward, False, {"animating": True}

    def draw(self, screen: pygame.Surface, font: pygame.font.Font, q_row: np.ndarray) -> None:
        pygame.draw.rect(screen, SKY, (0, 0, 800, 360))
        pygame.draw.rect(screen, GRASS, (0, 360, 800, 200))
        left, top, size = 90, 40, 70
        for r in range(N_ROW):
            for c in range(N_COL):
                rect = pygame.Rect(left + c * size, top + r * size, size - 6, size - 6)
                pygame.draw.rect(screen, (236, 240, 246), rect, border_radius=6)
        bx = left + self.col * size + 12
        by = top + self.row * size + 12
        pygame.draw.rect(screen, (180, 90, 50), (bx, by, 40, 36), border_radius=4)
        px = left + self.paddle * size + 4
        pygame.draw.rect(screen, (40, 80, 160), (px, top + (N_ROW - 1) * size + 18, size - 14, 16), border_radius=8)
        names = ["LEFT", "STAY", "RIGHT"]
        for i, n in enumerate(names):
            color = GOLD if i == int(np.argmax(q_row)) else INK
            screen.blit(font.render(f"{n}: {q_row[i]:6.1f}", True, color), (20, 16 + i * 20))
        screen.blit(font.render(f"caught {self.caught}   missed {self.missed}   {self.flash}", True, NAVY), (280, 16))
