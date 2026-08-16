<script setup lang="ts">
import { withBase } from 'vitepress'
import { computed, ref } from 'vue'
import { catalog, filterCatalog, POPULAR, type CatalogEntry } from '../../topics'
import type { LessonTrack } from '../../curriculum'

const q = ref('')
const track = ref<'all' | LessonTrack>('all')
const all = catalog()

const results = computed(() => filterCatalog(all, q.value, track.value))

const grouped = computed(() => {
  const map = new Map<string, CatalogEntry[]>()
  for (const row of results.value) {
    const key = `${row.pack} · ${row.packTitle}`
    if (!map.has(key)) map.set(key, [])
    map.get(key)!.push(row)
  }
  return [...map.entries()]
})

const searching = computed(() => q.value.trim().length > 0)

function setChip(term: string) {
  q.value = term
}

function setTrack(next: 'all' | LessonTrack) {
  track.value = next
}
</script>

<template>
  <div class="topic-finder">
    <label class="topic-finder__label" for="topic-q">Find a lesson</label>
    <input
      id="topic-q"
      v-model="q"
      class="topic-finder__input"
      type="search"
      placeholder="dropout, RAG, attention, eval, Q-learning…"
      autocomplete="off"
      spellcheck="false"
    />
    <p class="topic-finder__hint">
      Type a word. Or press <kbd>/</kbd> in the nav for full-text search across every page.
    </p>

    <div class="topic-finder__tracks" role="tablist" aria-label="Track">
      <button
        type="button"
        role="tab"
        :aria-selected="track === 'all'"
        :class="{ 'is-on': track === 'all' }"
        @click="setTrack('all')"
      >
        All
      </button>
      <button
        type="button"
        role="tab"
        :aria-selected="track === 'agents'"
        :class="{ 'is-on': track === 'agents' }"
        @click="setTrack('agents')"
      >
        Agents (ADK)
      </button>
      <button
        type="button"
        role="tab"
        :aria-selected="track === 'ml'"
        :class="{ 'is-on': track === 'ml' }"
        @click="setTrack('ml')"
      >
        ML from zero
      </button>
    </div>

    <div class="topic-finder__chips" aria-label="Popular topics">
      <button
        v-for="chip in POPULAR"
        :key="chip"
        type="button"
        class="topic-finder__chip"
        @click="setChip(chip)"
      >
        {{ chip }}
      </button>
    </div>

    <p class="topic-finder__count">
      {{ results.length }} lesson{{ results.length === 1 ? '' : 's' }}
      <template v-if="searching"> matching “{{ q.trim() }}”</template>
    </p>

    <p v-if="!results.length" class="topic-finder__empty">
      Nothing in the catalog for that. Try a shorter word, switch track, or use nav search
      (<kbd>/</kbd>) to scan lesson bodies.
    </p>

    <section v-for="[packLabel, rows] in grouped" :key="packLabel" class="topic-finder__pack">
      <h2>{{ packLabel }}</h2>
      <ol>
        <li v-for="row in rows" :key="row.slug">
          <a :href="withBase(`/lessons/${row.slug}`)">
            <code>{{ row.code }}</code>
            <span>{{ row.title }}</span>
          </a>
        </li>
      </ol>
    </section>
  </div>
</template>
