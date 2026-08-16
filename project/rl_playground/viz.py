"""Shared drawing helpers for the live training window."""

from __future__ import annotations

import pygame

from bitmap import BitmapFont


NAVY = (18, 24, 38)
PANEL = (28, 36, 54)
INK = (230, 234, 242)
MUTED = (150, 160, 180)
GREEN = (72, 201, 132)
GOLD = (245, 196, 72)
RED = (232, 93, 117)
SKY = (92, 168, 232)
GRASS = (46, 139, 87)
DIRT = (92, 64, 51)


def draw_panel(screen: pygame.Surface, font: BitmapFont, small: BitmapFont, lines: list[str], spark: list[float]) -> None:
    w, h = screen.get_size()
    panel_w = 280
    pygame.draw.rect(screen, PANEL, (w - panel_w, 0, panel_w, h))
    y = 16
    title = font.render("Training live", True, GOLD)
    screen.blit(title, (w - panel_w + 16, y))
    y = 52
    for line in lines:
        screen.blit(small.render(line, True, INK), (w - panel_w + 16, y))
        y += 22

    y += 12
    screen.blit(small.render("Reward (last 80 episodes)", True, MUTED), (w - panel_w + 16, y))
    y += 24
    box = pygame.Rect(w - panel_w + 16, y, panel_w - 32, 90)
    pygame.draw.rect(screen, NAVY, box, border_radius=6)
    if len(spark) >= 2:
        xs = [box.x + 4 + i * (box.w - 8) / (len(spark) - 1) for i in range(len(spark))]
        lo, hi = min(spark), max(spark)
        span = (hi - lo) or 1.0
        pts = [(xs[i], box.bottom - 6 - (spark[i] - lo) / span * (box.h - 12)) for i in range(len(spark))]
        pygame.draw.lines(screen, GREEN, False, pts, 2)

    y = box.bottom + 20
    keys = [
        "1-5  switch world",
        "SPACE pause",
        "G  greedy (show skill)",
        "R  wipe memory (Q=0)",
        "+ / -  speed",
        "ESC quit",
    ]
    for k in keys:
        screen.blit(small.render(k, True, MUTED), (w - panel_w + 16, y))
        y += 20
