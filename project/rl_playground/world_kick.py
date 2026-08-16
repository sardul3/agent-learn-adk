"""World 1 — Kick the football.

One kick per episode. The 'situation' is wind + how high the goal sits.
The 'move' is angle + power. You watch the ball fly, then the spreadsheet updates.
"""

from __future__ import annotations

import math

import numpy as np
import pygame

from viz import DIRT, GOLD, GRASS, INK, SKY


N_WIND = 5
N_GOAL = 5
N_ANGLE = 8
N_POWER = 6


class KickWorld:
    name = "1  Kick the football"
    concept = "One-shot action: choose, then watch the whole consequence."
    n_states = N_WIND * N_GOAL
    n_actions = N_ANGLE * N_POWER

    def __init__(self, rng: np.random.Generator):
        self.rng = rng
        self.wind = 0
        self.goal_bin = 0
        self.ball = [120.0, 420.0]
        self.vel = [0.0, 0.0]
        self.phase = "aim"  # aim | flight | done
        self.scored = False
        self.pending_reward = 0.0
        self.last_action = 0
        self.t = 0

    def encode(self) -> int:
        return self.wind * N_GOAL + self.goal_bin

    def reset(self) -> int:
        self.wind = int(self.rng.integers(0, N_WIND))
        self.goal_bin = int(self.rng.integers(0, N_GOAL))
        self.ball = [120.0, 420.0]
        self.vel = [0.0, 0.0]
        self.phase = "aim"
        self.scored = False
        self.pending_reward = 0.0
        self.t = 0
        return self.encode()

    def _goal_y(self) -> float:
        # Lower bin = lower crossbar opening center.
        return 280.0 - self.goal_bin * 32.0

    def step(self, action: int) -> tuple[int, float, bool, dict]:
        self.last_action = action
        if self.phase == "aim":
            angle_i = action // N_POWER
            power_i = action % N_POWER
            angle = math.radians(28 + angle_i * 7)
            power = 9.5 + power_i * 1.6
            wind_force = (self.wind - 2) * 0.55
            self.vel = [power * math.cos(angle) + wind_force, -power * math.sin(angle)]
            self.phase = "flight"
            self.t = 0
            return self.encode(), 0.0, False, {"animating": True}

        # Integrate a few physics ticks per RL step so the ball is watchable.
        for _ in range(3):
            self.vel[1] += 0.35  # gravity
            self.ball[0] += self.vel[0]
            self.ball[1] += self.vel[1]
            self.t += 1

        gx, gy = 710.0, self._goal_y()
        bx, by = self.ball
        in_goal = (680 <= bx <= 760) and (gy - 42 <= by <= gy + 42)
        on_ground = by >= 430
        out = bx > 820 or bx < 40 or by < 20 or self.t > 180

        if in_goal:
            self.scored = True
            self.phase = "done"
            return self.encode(), 100.0, True, {"animating": False}
        if on_ground or out:
            dist = math.hypot(bx - gx, by - gy)
            reward = max(-40.0, 40.0 - dist / 8.0)
            self.phase = "done"
            return self.encode(), reward, True, {"animating": False}
        return self.encode(), 0.0, False, {"animating": True}

    def draw(self, screen: pygame.Surface, font: pygame.font.Font, q_row: np.ndarray) -> None:
        pygame.draw.rect(screen, SKY, (0, 0, 800, 360))
        pygame.draw.rect(screen, GRASS, (0, 360, 800, 200))
        pygame.draw.rect(screen, DIRT, (0, 430, 800, 12))

        gy = self._goal_y()
        pygame.draw.rect(screen, INK, (690, gy - 48, 10, 96), border_radius=2)
        pygame.draw.rect(screen, GOLD, (688, gy - 52, 70, 8), border_radius=2)
        pygame.draw.circle(screen, (250, 250, 250), (int(self.ball[0]), int(self.ball[1])), 10)
        pygame.draw.circle(screen, (40, 40, 40), (int(self.ball[0]) - 3, int(self.ball[1]) - 2), 2)

        # Kicker
        pygame.draw.circle(screen, (40, 80, 160), (100, 410), 16)
        pygame.draw.line(screen, (40, 80, 160), (100, 426), (100, 455), 6)

        wind_txt = ["<<<<", "<<<", "calm", ">>>", ">>>>"][self.wind]
        screen.blit(font.render(f"Wind {wind_txt}", True, INK), (24, 16))
        screen.blit(font.render("GOAL", True, GOLD), (700, int(gy) - 72))

        # Q heatmap: rows = angle (steep at top), cols = power
        grid = q_row.reshape(N_ANGLE, N_POWER)
        lo, hi = float(grid.min()), float(grid.max())
        span = (hi - lo) or 1.0
        ox, oy = 20, 48
        for r in range(N_ANGLE):
            for c in range(N_POWER):
                t = (grid[r, c] - lo) / span
                color = (int(30 + 200 * t), int(40 + 80 * (1 - t)), int(80 + 40 * (1 - t)))
                rect = pygame.Rect(ox + c * 18, oy + r * 14, 16, 12)
                pygame.draw.rect(screen, color, rect)
                if self.last_action == r * N_POWER + c:
                    pygame.draw.rect(screen, GOLD, rect, 2)
        screen.blit(font.render("Q: angle x power (gold = last kick)", True, INK), (20, 48 + N_ANGLE * 14 + 8))
