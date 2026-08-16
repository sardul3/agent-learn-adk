<script setup lang="ts">
import { withBase } from 'vitepress'
import { computed } from 'vue'
import { data as lessons } from '../../data/lessons.data'
import { lessonCode } from '../../curriculum'
import { useProgress } from '../composables/progress'

const { lastSlug, completed } = useProgress()

const last = computed(() => lessons.find((l) => l.slug === lastSlug.value))
const nextOpen = computed(() => lessons.find((l) => !completed.value.includes(l.slug)))
const target = computed(() => last.value || nextOpen.value)
const code = computed(() =>
  target.value ? lessonCode(target.value.slug, target.value.lesson) : '',
)
</script>

<template>
  <p v-if="target" class="continue-lane">
    <span>Resume where you left off</span>
    <a :href="withBase(target.url)"> {{ code }} — {{ target.title }} </a>
  </p>
</template>
