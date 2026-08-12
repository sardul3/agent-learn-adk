<script setup lang="ts">
import { useRoute, withBase } from 'vitepress'
import { computed, watch } from 'vue'
import { data as lessons } from '../../data/lessons.data'
import { useProgress } from '../composables/progress'

const route = useRoute()
const { isDone, toggle, remember, countIn } = useProgress()

const slug = computed(() => {
  const m = route.path.match(/\/lessons\/([^/]+)/)
  return m ? m[1].replace(/\.html$/, '') : ''
})

const current = computed(() => lessons.find((l) => l.slug === slug.value))
const packLessons = computed(() =>
  lessons.filter((l) => l.pack === current.value?.pack).map((l) => l.slug),
)
const packDone = computed(() => countIn(packLessons.value))
const packTotal = computed(() => packLessons.value.length)
const done = computed(() => (slug.value ? isDone(slug.value) : false))

watch(
  slug,
  (value) => {
    if (value) remember(value)
  },
  { immediate: true },
)
</script>

<template>
  <div v-if="current" class="wave-progress">
    <p class="wave-progress__kicker">Wave {{ current.pack }}</p>
    <p class="wave-progress__count">
      {{ packDone }} / {{ packTotal }} picked
    </p>
    <div class="wave-progress__rail" aria-hidden="true">
      <span
        class="wave-progress__fill"
        :style="{ width: packTotal ? `${(packDone / packTotal) * 100}%` : '0%' }"
      />
    </div>
    <button type="button" class="wave-progress__btn" @click="toggle(slug)">
      {{ done ? 'Return to floor' : 'Mark lane complete' }}
    </button>
    <p class="wave-progress__hint">
      Saved in this browser only.
      <a :href="withBase('/packs/')">All waves</a>
    </p>
  </div>
</template>
