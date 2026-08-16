"""World 3 — Dock the delivery van.

A small warehouse grid. The van has a facing direction. You feel why 'state' must include heading.
"""

from __future__ import annotations

import numpy as np
import pygame

from viz import GOLD, INK, NAVY, PANEL


COLS, ROWS = 8, 6
# 0 east, 1 south, 2 west, 3 north
DX = [1, 0, -1, 0]
DY = [0, 1, 0, -1]


class DockWorld:
    name = "3  Dock the van"
    concept = "Grid + heading. The same square is different if you face the wrong way."
    n_states = COLS * ROWS * 4
    n_actions = 3  # 0 forward, 1 left, 2 right

    def __init__(self, rng: np.random.Generator):
        self.rng = rng
        self.x = 0
        self.y = 0
        self.h = 0
        self.goal = (6, 4)
        self.walls = {(3, 2), (3, 3), (4, 3), (1, 4), (5, 1)}
        self.steps = 0
        self.last_action = 0

    def encode(self) -> int:
        return (self.y * COLS + self.x) * 4 + self.h

    def reset(self) -> int:
        while True:
            self.x = int(self.rng.integers(0, COLS))
            self.y = int(self.rng.integers(0, ROWS))
            if (self.x, self.y) not in self.walls and (self.x, self.y) != self.goal:
                break
        self.h = int(self.rng.integers(0, 4))
        self.steps = 0
        return self.encode()

    def step(self, action: int) -> tuple[int, float, bool, dict]:
        self.last_action = action
        self.steps += 1
        if action == 1:
            self.h = (self.h - 1) % 4
            reward = -0.4
        elif action == 2:
            self.h = (self.h + 1) % 4
            reward = -0.4
        else:
            nx, ny = self.x + DX[self.h], self.y + DY[self.h]
            if nx < 0 or ny < 0 or nx >= COLS or ny >= ROWS or (nx, ny) in self.walls:
                reward = -8.0
            else:
                self.x, self.y = nx, ny
                reward = -0.3
        if (self.x, self.y) == self.goal and self.h == 0:
            return self.encode(), 50.0, True, {"animating": True}
        if self.steps >= 80:
            return self.encode(), -15.0, True, {"animating": True}
        return self.encode(), reward, False, {"animating": True}

    def draw(self, screen: pygame.Surface, font: pygame.font.Font, q_row: np.ndarray) -> None:
        pygame.draw.rect(screen, (210, 218, 228), (0, 0, 800, 560))
        cell = 70
        ox, oy = 40, 70
        for y in range(ROWS):
            for x in range(COLS):
                rect = pygame.Rect(ox + x * cell, oy + y * cell, cell - 4, cell - 4)
                if (x, y) in self.walls:
                    pygame.draw.rect(screen, PANEL, rect, border_radius=6)
                elif (x, y) == self.goal:
                    pygame.draw.rect(screen, (80, 160, 110), rect, border_radius=6)
                    screen.blit(font.render("DOCK >", True, INK), (rect.x + 8, rect.y + 22))
                else:
                    pygame.draw.rect(screen, (236, 240, 246), rect, border_radius=6)
        vx = ox + self.x * cell + 18
        vy = oy + self.y * cell + 18
        pygame.draw.rect(screen, (40, 80, 160), (vx, vy, 34, 34), border_radius=6)
        cx, cy = vx + 17, vy + 17
        pygame.draw.circle(screen, GOLD, (cx + DX[self.h] * 10, cy + DY[self.h] * 10), 5)
        names = ["FWD", "LEFT", "RIGHT"]
        for i, n in enumerate(names):
            color = GOLD if i == int(np.argmax(q_row)) else NAVY
            screen.blit(font.render(f"{n}: {q_row[i]:6.1f}", True, color), (40, 16 + i * 18))
        screen.blit(font.render("Must face EAST (>) on the dock bay.", True, NAVY), (280, 20))
