<script setup lang="ts">
import DefaultTheme from 'vitepress/theme-without-fonts'
import { useData, withBase } from 'vitepress'
import { nextTick, provide } from 'vue'
import LaneTicket from './components/LaneTicket.vue'
import WaveProgress from './components/WaveProgress.vue'
import MarkComplete from './components/MarkComplete.vue'
import LaneHero from './components/LaneHero.vue'
import FloorMeter from './components/FloorMeter.vue'

const { Layout } = DefaultTheme
const { isDark } = useData()

const enableTransitions = () =>
  typeof document !== 'undefined' &&
  'startViewTransition' in document &&
  window.matchMedia('(prefers-reduced-motion: no-preference)').matches

provide('toggle-appearance', async ({ clientX: x, clientY: y }: MouseEvent) => {
  if (!enableTransitions()) {
    isDark.value = !isDark.value
    return
  }

  const clipPath = [
    `circle(0px at ${x}px ${y}px)`,
    `circle(${Math.hypot(
      Math.max(x, innerWidth - x),
      Math.max(y, innerHeight - y),
    )}px at ${x}px ${y}px)`,
  ]

  await document.startViewTransition(async () => {
    isDark.value = !isDark.value
    await nextTick()
  }).ready

  document.documentElement.animate(
    { clipPath: isDark.value ? [...clipPath].reverse() : clipPath },
    {
      duration: 380,
      easing: 'ease-in',
      fill: 'forwards',
      pseudoElement: `::view-transition-${isDark.value ? 'old' : 'new'}(root)`,
    },
  )
})
</script>

<template>
  <Layout>
    <template #nav-bar-content-after>
      <ClientOnly>
        <FloorMeter />
      </ClientOnly>
    </template>
    <template #home-hero-image>
      <LaneHero />
    </template>
    <template #doc-before>
      <LaneTicket />
    </template>
    <template #aside-outline-before>
      <ClientOnly>
        <WaveProgress />
      </ClientOnly>
    </template>
    <template #doc-after>
      <ClientOnly>
        <MarkComplete />
      </ClientOnly>
    </template>
    <template #not-found>
      <div class="lane-404">
        <p class="lane-404__kicker">Empty lane</p>
        <h1>This ticket is not on the floor.</h1>
        <p>The URL does not match a shipped lesson. Return to the curriculum and pick a wave.</p>
        <p>
          <a :href="withBase('/')">Back to Meridian Learn</a>
        </p>
      </div>
    </template>
  </Layout>
</template>

<style>
::view-transition-old(root),
::view-transition-new(root) {
  animation: none;
  mix-blend-mode: normal;
}
::view-transition-old(root),
.dark ::view-transition-new(root) {
  z-index: 1;
}
::view-transition-new(root),
.dark ::view-transition-old(root) {
  z-index: 9999;
}
</style>
