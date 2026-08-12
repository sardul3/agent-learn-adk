<script setup lang="ts">
import { useRoute, withBase } from 'vitepress'
import { computed } from 'vue'
import { data as lessons } from '../../data/lessons.data'
import { useProgress } from '../composables/progress'

const route = useRoute()
const { isDone, toggle } = useProgress()

const slug = computed(() => {
  const m = route.path.match(/\/lessons\/([^/]+)/)
  return m ? m[1].replace(/\.html$/, '') : ''
})

const index = computed(() => lessons.findIndex((l) => l.slug === slug.value))
const current = computed(() => (index.value >= 0 ? lessons[index.value] : undefined))
const next = computed(() => (index.value >= 0 ? lessons[index.value + 1] : undefined))
const done = computed(() => (slug.value ? isDone(slug.value) : false))
</script>

<template>
  <section v-if="current" class="mark-complete">
    <div class="mark-complete__row">
      <button type="button" class="mark-complete__btn" :data-done="done" @click="toggle(slug)">
        {{ done ? 'Completed — click to undo' : 'Mark this lesson complete' }}
      </button>
      <a v-if="next" class="mark-complete__next" :href="withBase(next.url)">
        Next: {{ String(next.lesson).padStart(2, '0') }} {{ next.title }}
      </a>
    </div>
  </section>
</template>
