import { packs } from '../.vitepress/curriculum'

export default {
  watch: ['../.vitepress/curriculum.ts'],
  paths() {
    return packs.map((pack) => ({
      params: {
        pack: pack.slug,
        letter: pack.letter,
        title: pack.title,
        summary: pack.summary,
      },
    }))
  },
}
