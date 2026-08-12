<script setup lang="ts">
import { useData } from 'vitepress'
import { data as lessons } from '../../data/lessons.data'
import { useProgress } from '../composables/progress'

const { page } = useData()
const { countIn } = useProgress()
const total = lessons.length
const done = countIn(lessons.map((l) => l.slug))
</script>

<template>
  <p v-if="!page.isNotFound" class="floor-meter" aria-label="Curriculum progress">
    <span>{{ done }}</span>
    <small>/ {{ total }} lessons</small>
  </p>
</template>
