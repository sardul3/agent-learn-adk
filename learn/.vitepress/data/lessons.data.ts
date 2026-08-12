import { createContentLoader } from 'vitepress'
import { packForLesson } from '../curriculum'

export interface LessonCard {
  url: string
  slug: string
  title: string
  lesson: number
  pack: string
  packTitle: string
  level: string
  duration: string
  outcome: string
  description: string
  prerequisites: string
}

declare const data: LessonCard[]
export { data }

export default createContentLoader('lessons/*.md', {
  includeSrc: false,
  transform(raw): LessonCard[] {
    return raw
      .filter((page) => page.frontmatter.lesson)
      .map((page) => {
        const lesson = Number(page.frontmatter.lesson)
        const pack = packForLesson(lesson)
        const slug = page.url.replace(/\/lessons\/|\.html$/g, '').replace(/^\//, '')
        return {
          url: page.url,
          slug,
          title: String(page.frontmatter.title ?? ''),
          lesson,
          pack: String(page.frontmatter.pack ?? pack?.letter ?? ''),
          packTitle: pack?.title ?? '',
          level: String(page.frontmatter.level ?? ''),
          duration: String(page.frontmatter.duration ?? ''),
          outcome: String(page.frontmatter.outcome ?? ''),
          description: String(page.frontmatter.description ?? ''),
          prerequisites: String(page.frontmatter.prerequisites ?? ''),
        }
      })
      .sort((a, b) => a.lesson - b.lesson)
  },
})
