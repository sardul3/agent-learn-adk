<script setup lang="ts">
import { withBase } from 'vitepress'
import { computed } from 'vue'
import { data as lessons } from '../../data/lessons.data'
import { useProgress } from '../composables/progress'

const { lastSlug, completed } = useProgress()

const last = computed(() => lessons.find((l) => l.slug === lastSlug.value))
const nextOpen = computed(() => lessons.find((l) => !completed.value.includes(l.slug)))
const target = computed(() => last.value || nextOpen.value)
</script>

<template>
  <p v-if="target" class="continue-lane">
    <span>Resume the floor</span>
    <a :href="withBase(target.url)">
      Lesson {{ String(target.lesson).padStart(2, '0') }} — {{ target.title }}
    </a>
  </p>
</template>
