<script setup lang="ts">
import { withBase, useData } from 'vitepress'
import { computed } from 'vue'
import { packs } from '../../curriculum'
import { data as lessons } from '../../data/lessons.data'
import { useProgress } from '../composables/progress'

const { params } = useData()
const { isDone, countIn } = useProgress()

const pack = computed(() => packs.find((p) => p.slug === params.value?.pack))
const shipped = computed(() => pack.value?.lessons.filter((l) => l.shipped) ?? [])
const planned = computed(() => pack.value?.lessons.filter((l) => !l.shipped) ?? [])
const cards = computed(() =>
  shipped.value
    .map((item) => lessons.find((l) => l.slug === item.slug))
    .filter((card): card is NonNullable<typeof card> => Boolean(card)),
)
const done = computed(() => countIn(shipped.value.map((l) => l.slug)))
</script>

<template>
  <div>
    <p v-if="shipped.length" class="wave-progress__kicker">
      {{ done }} / {{ shipped.length }} lessons complete in this browser
    </p>

    <h2>Shipped lanes</h2>
    <div
      v-for="card in cards"
      :key="card.slug"
      class="pack-board__wave"
      style="margin-bottom: 1rem"
    >
      <a class="pack-board__head" :href="withBase(card.url)">
        <span class="pack-board__letter">{{ String(card.lesson).padStart(2, '0') }}</span>
        <span>
          <strong>{{ card.title }}</strong>
          <em>{{ card.level }} · {{ card.duration }}</em>
        </span>
      </a>
      <p class="pack-board__empty">{{ card.outcome }}</p>
    </div>
    <p v-if="!shipped.length">No markdown in <code>lessons/</code> for this pack yet.</p>

    <h2>Still on the dock</h2>
    <ul v-if="planned.length">
      <li v-for="item in planned" :key="item.slug">
        <code>{{ String(item.n).padStart(2, '0') }}</code> {{ item.title }}
      </li>
    </ul>
    <p v-else>This wave is fully shipped. Next pack is in the sidebar.</p>
  </div>
</template>
