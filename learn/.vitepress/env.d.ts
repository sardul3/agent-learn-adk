/// <reference types="vitepress/client" />

declare module '*.vue' {
  import type { DefineComponent } from 'vue'
  const component: DefineComponent<object, object, unknown>
  export default component
}

declare module '*.mjs' {
  export function syncLessons(): { lessons: number }
  export const watchRoots: string[]
  export const GITHUB_REPO: string
}
