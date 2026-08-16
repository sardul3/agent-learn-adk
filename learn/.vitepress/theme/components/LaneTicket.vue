<script setup lang="ts">
import { useData } from 'vitepress'
import { computed } from 'vue'
import { lessonCode } from '../../curriculum'

const { frontmatter } = useData()

const visible = computed(() => Number.isFinite(Number(frontmatter.value.lesson)))
const pack = computed(() => String(frontmatter.value.pack || ''))
const code = computed(() => {
  const fromFm = String(frontmatter.value.code || '')
  if (fromFm) return fromFm
  const slug = String(frontmatter.value.slug || '')
  return lessonCode(slug, Number(frontmatter.value.lesson))
})
const level = computed(() => String(frontmatter.value.level || ''))
const duration = computed(() => String(frontmatter.value.duration || ''))
const prerequisites = computed(() => String(frontmatter.value.prerequisites || ''))
const outcome = computed(() => String(frontmatter.value.outcome || ''))
const track = computed(() => String(frontmatter.value.track || ''))
</script>

<template>
  <aside v-if="visible" class="lane-ticket" aria-label="Lesson ticket">
    <div class="lane-ticket__stub">
      <span class="lane-ticket__lane">Pack {{ pack }}</span>
      <span class="lane-ticket__sku">{{ code }}</span>
    </div>
    <dl class="lane-ticket__fields">
      <div v-if="track">
        <dt>Track</dt>
        <dd>{{ track === 'ml' ? 'ML from zero (CPU)' : 'Agents (ADK)' }}</dd>
      </div>
      <div v-if="level">
        <dt>Level</dt>
        <dd>{{ level }}</dd>
      </div>
      <div v-if="duration">
        <dt>Time</dt>
        <dd>{{ duration }}</dd>
      </div>
      <div v-if="prerequisites" class="lane-ticket__wide">
        <dt>Prerequisites</dt>
        <dd>{{ prerequisites }}</dd>
      </div>
      <div v-if="outcome" class="lane-ticket__wide">
        <dt>Lab outcome</dt>
        <dd>{{ outcome }}</dd>
      </div>
    </dl>
  </aside>
</template>
