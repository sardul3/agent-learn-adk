import { onMounted, ref, watch, type Ref } from 'vue'

export function useStorage<T>(key: string, fallback: T): Ref<T> {
  const state = ref(fallback) as Ref<T>
  let ready = false

  onMounted(() => {
    try {
      const raw = localStorage.getItem(key)
      if (raw != null) state.value = JSON.parse(raw) as T
    } catch {
      /* private mode / SSR */
    }
    ready = true
  })

  watch(
    state,
    (value) => {
      if (!ready) return
      try {
        localStorage.setItem(key, JSON.stringify(value))
      } catch {
        /* ignore quota */
      }
    },
    { deep: true },
  )

  return state
}
