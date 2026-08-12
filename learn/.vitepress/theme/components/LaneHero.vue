<script setup lang="ts">
import { withBase } from 'vitepress'
</script>

<template>
  <svg
    class="lane-hero"
    viewBox="0 0 420 320"
    role="img"
    aria-label="OrderOps ticket flowing through a router to specialist lanes"
  >
    <rect class="lane-hero__sheet" x="16" y="16" width="388" height="288" rx="2" />
    <text class="lane-hero__mono" x="36" y="48">MERIDIAN COMMERCE  ·  ORDEROPS</text>
    <text class="lane-hero__mono lane-hero__dim" x="36" y="68">TICKET  TCK-9001  ·  WAVE A</text>
    <line class="lane-hero__rule" x1="36" y1="84" x2="384" y2="84" />
    <text class="lane-hero__body" x="36" y="118">Customer ticket / ops alert</text>
    <path class="lane-hero__flow" d="M 210 128 L 210 152" />
    <rect class="lane-hero__node" x="148" y="152" width="124" height="36" />
    <text class="lane-hero__mono" x="176" y="175">ROUTER</text>
    <path class="lane-hero__flow" d="M 210 188 L 210 208" />
    <path class="lane-hero__flow" d="M 80 208 L 340 208" />
    <path class="lane-hero__flow" d="M 80 208 L 80 228" />
    <path class="lane-hero__flow" d="M 210 208 L 210 228" />
    <path class="lane-hero__flow" d="M 340 208 L 340 228" />
    <rect class="lane-hero__chip" x="36" y="228" width="88" height="28" />
    <rect class="lane-hero__chip" x="166" y="228" width="88" height="28" />
    <rect class="lane-hero__chip" x="296" y="228" width="88" height="28" />
    <text class="lane-hero__mono" x="54" y="247">ORDER</text>
    <text class="lane-hero__mono" x="175" y="247">INVENTORY</text>
    <text class="lane-hero__mono" x="314" y="247">REFUND</text>
    <text class="lane-hero__dim" x="36" y="280">HITL + audit  ·  native ADK only</text>
    <a :href="withBase('/lessons/01-agentic-foundations')">
      <text class="lane-hero__cta" x="36" y="298">Open lane 01 →</text>
    </a>
  </svg>
</template>
