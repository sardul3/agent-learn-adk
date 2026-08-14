---
layout: home
hero:
  name: Meridian Learn
  text: Study the ADK track without splitting your editor.
  tagline: Lessons stay in markdown. This site is the reading room — search, outline, progress, and pack maps — while the lab code stays in the other window.
  actions:
    - theme: brand
      text: Open lesson 01
      link: /lessons/01-agentic-foundations
    - theme: alt
      text: How to study here
      link: /study
    - theme: alt
      text: GitHub
      link: https://github.com/sardul3/agent-learn-adk
features:
  - icon:
      src: /icons/ticket.svg
      width: 32
      height: 32
    title: One product, every lesson
    details: Meridian Commerce OrderOps — WISMO, inventory exceptions, refund HITL. No toy chatbots.
    link: /reference/meridian-northstar
    linkText: Read the northstar
  - icon:
      src: /icons/scan.svg
      width: 32
      height: 32
    title: Native ADK only
    details: Domain tools are yours. Alternate agent runtimes are not. The Native ADK rule is the floor.
    link: /reference/NATIVE-ADK
    linkText: Open the rule
  - icon:
      src: /icons/eval.svg
      width: 32
      height: 32
    title: Trajectories over prose
    details: Evals, judges, traces, canaries. A warm apology that skipped get_order is a failed run.
    link: /lessons/08-testing-evaluation
    linkText: Start Pack B
  - icon:
      src: /icons/graph.svg
      width: 32
      height: 32
    title: Packs are waves
    details: Finish a pack before the next. Suggested order is A → B → 41 → C → D → E → 42 → F.
    link: /packs/
    linkText: See the floor
---

<ClientOnly>
  <ContinueLane />
</ClientOnly>

## Fulfillment waves

Each pack is a wave. Completion is stored in this browser only — useful when you study on a laptop and keep `adk web` in another desktop.

<ClientOnly>
  <PackBoard />
</ClientOnly>
