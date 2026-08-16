<script setup lang="ts">
import { withBase } from 'vitepress'
import { computed } from 'vue'
import { packs, lessonCode, type LessonTrack } from '../../curriculum'
import { useProgress } from '../composables/progress'

const props = withDefaults(
  defineProps<{
    track?: 'all' | LessonTrack
  }>(),
  { track: 'all' },
)

const { countIn, isDone } = useProgress()

const waves = computed(() =>
  packs
    .filter((pack) => {
      if (props.track === 'all') return true
      if (props.track === 'ml') return pack.letter.startsWith('M')
      return !pack.letter.startsWith('M')
    })
    .map((pack) => {
      const shipped = pack.lessons.filter((l) => l.shipped)
      const slugs = shipped.map((l) => l.slug)
      const done = countIn(slugs)
      return {
        ...pack,
        shipped,
        done,
        total: shipped.length,
        pending: pack.lessons.filter((l) => !l.shipped).length,
      }
    }),
)
</script>

<template>
  <ol class="pack-board">
    <li v-for="wave in waves" :key="wave.slug" class="pack-board__wave">
      <a class="pack-board__head" :href="withBase(`/packs/${wave.slug}`)">
        <span class="pack-board__letter">{{ wave.letter }}</span>
        <span>
          <strong>{{ wave.title.replace(/^Bonus ML — /, 'ML — ') }}</strong>
          <em v-if="wave.total">{{ wave.done }}/{{ wave.total }} complete</em>
          <em v-else>Not shipped yet</em>
        </span>
      </a>
      <ol v-if="wave.shipped.length" class="pack-board__list">
        <li v-for="item in wave.shipped" :key="item.slug">
          <a
            :href="withBase(`/lessons/${item.slug}`)"
            :class="{ 'is-done': isDone(item.slug) }"
          >
            <span>{{ lessonCode(item.slug, item.n) }}</span>
            {{ item.title }}
          </a>
        </li>
      </ol>
      <p v-else class="pack-board__empty">
        {{ wave.pending }} lessons planned — they will appear here when the markdown lands in
        <code>lessons/</code>.
      </p>
    </li>
  </ol>
</template>
