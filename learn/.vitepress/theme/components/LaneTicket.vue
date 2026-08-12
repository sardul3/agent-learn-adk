<script setup lang="ts">
import { useData } from 'vitepress'
import { computed } from 'vue'

const { frontmatter } = useData()

const visible = computed(() => Number.isFinite(Number(frontmatter.value.lesson)))
const pack = computed(() => String(frontmatter.value.pack || ''))
const lesson = computed(() => String(frontmatter.value.lesson || '').padStart(2, '0'))
const level = computed(() => String(frontmatter.value.level || ''))
const duration = computed(() => String(frontmatter.value.duration || ''))
const prerequisites = computed(() => String(frontmatter.value.prerequisites || ''))
const outcome = computed(() => String(frontmatter.value.outcome || ''))
</script>

<template>
  <aside v-if="visible" class="lane-ticket" aria-label="Lesson ticket">
    <div class="lane-ticket__stub">
      <span class="lane-ticket__lane">Pack {{ pack }}</span>
      <span class="lane-ticket__sku">Lesson {{ lesson }}</span>
    </div>
    <dl class="lane-ticket__fields">
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
