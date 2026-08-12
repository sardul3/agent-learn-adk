---
title: How to study
description: Use Meridian Learn as the reading room and keep the lab codebase for hands-on work.
outline: [2, 3]
---

# How to study without splitting your brain

This site is generated from `lessons/*.md`. Edit a lesson in the repo, save, and the local preview reloads. You do not maintain a second copy of the curriculum.

## Daily loop

1. Read the lesson here (search, outline, collapsed answers).
2. Switch to the repo only when a **Task** says to create or change files.
3. Come back here for the knowledge check. Peek at answers only after you try.

> [!TIP]
> Keep this site on a second monitor or a browser tab group named “Learn”. Keep the IDE on `project/`.

> [!WARNING] Watch out
> If you cannot teach the knowledge-check answers without the page, you are not done — even if the pytest is green.

## Run it locally

::: code-group

```sh [npm]
cd learn
npm install
npm run dev
```

```sh [pnpm]
cd learn
pnpm install
pnpm dev
```

:::

The preview is at `http://localhost:5173`. The converter watches `lessons/` and `docs/` and regenerates VitePress pages on save.

::: info What the converter does
- Adds frontmatter (level, time, pack, outcome) for the ticket header and search
- Turns `> **Tip:**` / `> **Watch out:**` into GitHub-flavored alerts
- Wraps **Answers** in a collapsed details block
- Rewrites lesson/doc links to site routes
- Points `project/...` links at GitHub so you can read lab files without leaving the lesson
:::

## Site features worth using

| Feature | Where |
|---|---|
| Local full-text search (`/` or the search box) | Nav bar — MiniSearch, works offline |
| Lesson ticket (pack, time, outcome) | Top of every lesson |
| On this lesson | Right outline |
| Mark complete | Right rail + bottom of the lesson |
| Previous / next lane | Footer of each lesson |
| Edit source on GitHub | Bottom of the page — edits `lessons/`, not the generated copy |
| Day / night shift | Appearance toggle (view-transition wipe if the browser allows it) |

<Badge type="tip" text="VitePress 1.6" /> Local search detailed view, `metaChunk` for faster loads, GitHub alerts, markdown region includes, and `createContentLoader` for the pack board are all first-party.

## Knowledge checks

Answers ship collapsed:

::: details Example — this is what a lesson does
You should see a **Peek at answers** block at the bottom of each shipped lesson. Open it only after you write your own answers.
:::

## GitHub Pages

Pushes to `main` that touch lessons, docs, or `learn/` build this site to `https://sardul3.github.io/agent-learn-adk/`.

In the repo: **Settings → Pages → Source = GitHub Actions**.

## When a lesson is missing

Packs F and G still have unpublished numbers. They show on the [pack board](/packs/) as planned. When the markdown lands in `lessons/`, the next `npm run dev` (or Pages deploy) picks it up — no site rewrite required.
