#!/usr/bin/env python3
"""Live window: watch five tiny agents learn by trial and error.

Run from this folder:

    python play.py
"""

from __future__ import annotations

import sys

import numpy as np
import pygame

from rl_core import QHyper, TabularQAgent
from bitmap import FONT, SMALL
from viz import NAVY, draw_panel
from world_balance import BalanceWorld
from world_catch import CatchWorld
from world_dock import DockWorld
from world_kick import KickWorld
from world_parkour import ParkourWorld

WORLDS = [KickWorld, ParkourWorld, DockWorld, BalanceWorld, CatchWorld]


def make_pair(idx: int, rng: np.random.Generator):
    world = WORLDS[idx](rng)
    hyper = QHyper()
    if idx == 0:
        hyper = QHyper(alpha=0.25, gamma=0.0, epsilon_decay=0.995)
        # gamma=0: a kick has no "next situation" that matters. Only this reward counts.
    if idx == 3:
        hyper = QHyper(alpha=0.12, gamma=0.98, epsilon_decay=0.999)
    agent = TabularQAgent(world.n_states, world.n_actions, rng, hyper)
    return world, agent


def main() -> None:
    pygame.init()
    pygame.display.set_caption("RL playground — watch the spreadsheet fill in")
    screen = pygame.display.set_mode((1080, 560))
    clock = pygame.time.Clock()
    font, small = FONT, SMALL

    rng = np.random.default_rng(7)
    world_i = 0
    world, agent = make_pair(world_i, rng)
    state = world.reset()
    paused = False
    greedy = False
    speed = 2  # RL decisions per frame-group
    episode = 0
    ep_reward = 0.0
    history: list[float] = []
    last_action = 0

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type != pygame.KEYDOWN:
                continue
            if event.key == pygame.K_ESCAPE:
                running = False
            if event.key == pygame.K_SPACE:
                paused = not paused
            if event.key == pygame.K_g:
                greedy = not greedy
            if event.key == pygame.K_r:
                agent.reset_brain()
                state = world.reset()
                ep_reward = 0.0
                history.clear()
                episode = 0
            if event.key in (pygame.K_EQUALS, pygame.K_PLUS):
                speed = min(20, speed + 1)
            if event.key == pygame.K_MINUS:
                speed = max(1, speed - 1)
            if event.unicode in "12345":
                world_i = int(event.unicode) - 1
                world, agent = make_pair(world_i, rng)
                state = world.reset()
                episode = 0
                ep_reward = 0.0
                history.clear()
                greedy = False

        steps_this_frame = 0 if paused else speed
        for _ in range(steps_this_frame):
            action = agent.act(state, greedy=greedy)
            last_action = action
            next_state, reward, done, _info = world.step(action)
            agent.learn(state, action, reward, next_state, done)
            ep_reward += reward
            state = next_state
            if done:
                history.append(ep_reward)
                if len(history) > 80:
                    history.pop(0)
                episode += 1
                agent.decay_epsilon()
                state = world.reset()
                ep_reward = 0.0

        screen.fill(NAVY)
        q_row = agent.q[state]
        world.draw(screen, font, q_row)
        avg = float(np.mean(history)) if history else 0.0
        lines = [
            world.name,
            world.concept[:42],
            f"episode {episode}",
            f"epsilon (randomness) {agent.epsilon:.2f}",
            f"greedy demo {'ON' if greedy else 'off'}",
            f"paused {'yes' if paused else 'no'}",
            f"speed {speed}",
            f"avg reward (80) {avg:7.1f}",
            f"last action {last_action}",
        ]
        draw_panel(screen, font, small, lines, history)
        pygame.display.flip()
        clock.tick(30)

    pygame.quit()
    sys.exit(0)


if __name__ == "__main__":
    main()
