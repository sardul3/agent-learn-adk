---
layout: home
hero:
  name: Meridian Learn
  text: One shop for agents and ML.
  tagline: Search a topic, open the lesson, run the lab. Maya’s warehouse is the through-line — from slope and loss to ADK tools, RAG, and evals.
  actions:
    - theme: brand
      text: Find a topic
      link: /topics
    - theme: alt
      text: Agents — lesson 01
      link: /lessons/01-agentic-foundations
    - theme: alt
      text: ML from zero — ml-00
      link: /lessons/ml-00-what-a-model-is
features:
  - icon:
      src: /icons/ticket.svg
      width: 32
      height: 32
    title: Find anything
    details: Type RAG, dropout, attention, eval, Q-learning. Catalog + full-text search (/) cover every shipped lesson.
    link: /topics
    linkText: Open the catalog
  - icon:
      src: /icons/scan.svg
      width: 32
      height: 32
    title: Agents (native ADK)
    details: Meridian OrderOps — tools, graphs, HITL, MCP, evals, deploy. Domain tools are yours. Alternate runtimes are not.
    link: /lessons/01-agentic-foundations
    linkText: Start Pack A
  - icon:
      src: /icons/eval.svg
      width: 32
      height: 32
    title: ML from zero (CPU)
    details: Slope through tiny GPT and a five-world RL playground. Laptop only. Honest quality labels.
    link: /lessons/ml-00-what-a-model-is
    linkText: Open ml-00
  - icon:
      src: /icons/graph.svg
      width: 32
      height: 32
    title: Packs you can finish
    details: Agents A→G, then M0–M12. Mark complete in this browser. Resume where you left off.
    link: /packs/
    linkText: See every pack
---

<ClientOnly>
  <ContinueLane />
</ClientOnly>

## Agents — Google ADK

Suggested order: **A → B → 41 → C → D → E → 42 → F → G**. Keep a real Meridian slice in flight.

<ClientOnly>
  <PackBoard track="agents" />
</ClientOnly>

## ML from zero — CPU labs

Optional beside Pack D if models still feel like magic. Start at [ml-00](/lessons/ml-00-what-a-model-is). Do not skip ADK safety.

<ClientOnly>
  <PackBoard track="ml" />
</ClientOnly>
