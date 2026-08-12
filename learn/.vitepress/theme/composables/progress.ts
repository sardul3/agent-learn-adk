import { useStorage } from './storage'

const COMPLETE_KEY = 'meridian-learn-complete'
const LAST_KEY = 'meridian-learn-last'

export function useProgress() {
  const completed = useStorage<string[]>(COMPLETE_KEY, [])
  const lastSlug = useStorage<string>(LAST_KEY, '')

  function isDone(slug: string) {
    return completed.value.includes(slug)
  }

  function toggle(slug: string) {
    if (isDone(slug)) {
      completed.value = completed.value.filter((s) => s !== slug)
    } else {
      completed.value = [...completed.value, slug]
    }
  }

  function mark(slug: string, done: boolean) {
    if (done && !isDone(slug)) completed.value = [...completed.value, slug]
    if (!done && isDone(slug)) completed.value = completed.value.filter((s) => s !== slug)
  }

  function remember(slug: string) {
    if (slug) lastSlug.value = slug
  }

  function countIn(slugs: string[]) {
    return slugs.filter((s) => isDone(s)).length
  }

  return { completed, lastSlug, isDone, toggle, mark, remember, countIn }
}
