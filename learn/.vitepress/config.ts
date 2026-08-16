import { defineConfig, type DefaultTheme } from 'vitepress'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import type { Plugin } from 'vite'
import { shippedLessons, agentPacks, mlPacks, lessonCode, type Pack } from './curriculum'
import { syncLessons, watchRoots } from '../scripts/sync-lessons.mjs'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const REPO = 'sardul3/agent-learn-adk'
const SITE = `https://sardul3.github.io/${REPO.split('/')[1]}/`
const base = process.env.VITEPRESS_BASE || '/'

syncLessons()

function lessonSyncPlugin(): Plugin {
  return {
    name: 'meridian-sync-lessons',
    buildStart() {
      syncLessons()
    },
    configureServer(server) {
      for (const root of watchRoots) {
        server.watcher.add(root)
      }
      const reload = (file: string) => {
        const resolved = path.resolve(file)
        if (watchRoots.some((root) => resolved.startsWith(root))) {
          syncLessons()
        }
      }
      server.watcher.on('change', reload)
      server.watcher.on('add', reload)
    },
  }
}

function packSidebar(
  subset: Pack[],
  opts: { collapsedAfter: number; titlePrefix?: (p: Pack) => string },
): DefaultTheme.SidebarItem[] {
  return subset
    .filter((p) => p.lessons.some((l) => l.shipped))
    .map((p, i) => ({
      text: opts.titlePrefix ? opts.titlePrefix(p) : `Pack ${p.letter} · ${p.title}`,
      collapsed: i > opts.collapsedAfter,
      items: p.lessons
        .filter((l) => l.shipped)
        .map((l) => ({
          text: `${lessonCode(l.slug, l.n)}  ${l.title}`,
          link: `/lessons/${l.slug}`,
        })),
    }))
}

function browseGroup(): DefaultTheme.SidebarItem {
  return {
    text: 'Browse',
    items: [
      { text: 'Find a topic', link: '/topics' },
      { text: 'All packs', link: '/packs/' },
      { text: 'How to study', link: '/study' },
    ],
  }
}

function sidebar(): DefaultTheme.Sidebar {
  const agents = [browseGroup(), ...packSidebar(agentPacks, { collapsedAfter: 0 })]
  const ml = [
    browseGroup(),
    {
      text: 'ML from zero',
      items: [
        { text: 'Start at ml-00', link: '/lessons/ml-00-what-a-model-is' },
        { text: 'RL five worlds', link: '/lessons/bonus-rl-visual-playground' },
        { text: 'CPU capstone', link: '/lessons/ml-51-meridian-cpu-capstone' },
      ],
    },
    ...packSidebar(mlPacks, {
      collapsedAfter: 0,
      titlePrefix: (p) => `${p.letter} · ${p.title.replace(/^Bonus ML — /, '')}`,
    }),
  ]
  return {
    '/lessons/ml-': ml,
    '/lessons/bonus-': ml,
    '/packs/m': ml,
    '/topics': ml,
    '/': agents,
  }
}

function nav(): DefaultTheme.NavItem[] {
  return [
    { text: 'Find a topic', link: '/topics' },
    {
      text: 'Agents',
      items: [
        { text: 'Start at lesson 01', link: '/lessons/01-agentic-foundations' },
        { text: 'All agent packs', link: '/packs/' },
        ...agentPacks.map((p) => ({
          text: `Pack ${p.letter} — ${p.title}`,
          link: `/packs/${p.slug}`,
        })),
      ],
    },
    {
      text: 'ML from zero',
      items: [
        { text: 'Start at ml-00', link: '/lessons/ml-00-what-a-model-is' },
        { text: 'RL five worlds', link: '/lessons/bonus-rl-visual-playground' },
        { text: 'CPU capstone', link: '/lessons/ml-51-meridian-cpu-capstone' },
        ...mlPacks.map((p) => ({
          text: `${p.letter} — ${p.title.replace(/^Bonus ML — /, '')}`,
          link: `/packs/${p.slug}`,
        })),
      ],
    },
    { text: 'How to study', link: '/study' },
    {
      text: 'Reference',
      items: [
        { text: 'Curriculum roadmap', link: '/reference/curriculum-roadmap' },
        { text: 'Meridian northstar', link: '/reference/meridian-northstar' },
        { text: 'Native ADK rule', link: '/reference/NATIVE-ADK' },
        { text: 'SME gap analysis', link: '/reference/gap-analysis-sme' },
        { text: 'AI engineering gap analysis', link: '/reference/gap-analysis-ai-engineering' },
        { text: 'Agent platform gap analysis', link: '/reference/gap-analysis-agent-platform' },
        { text: 'Capstone — agent platform curriculum', link: '/reference/capstone-agent-platform-curriculum' },
        { text: 'Reading list — SA/SWE arsenal', link: '/reference/ai-engineering-reading-list' },
      ],
    },
  ]
}

export default defineConfig({
  title: 'Meridian Learn',
  titleTemplate: ':title · Meridian Learn',
  description:
    'One shop for AI and ML: Google ADK agents plus a CPU ML track from slope to tiny GPT. Search any topic, walk the lab.',
  lang: 'en-US',
  base,
  cleanUrls: true,
  metaChunk: true,
  lastUpdated: true,
  ignoreDeadLinks: true,
  srcExclude: ['**/README.md'],
  sitemap: {
    hostname: SITE,
  },
  head: [
    ['link', { rel: 'icon', href: `${base}favicon.svg`, type: 'image/svg+xml' }],
    ['meta', { name: 'theme-color', content: '#1F7A74' }],
    ['meta', { property: 'og:type', content: 'website' }],
    ['meta', { property: 'og:site_name', content: 'Meridian Learn' }],
    ['meta', { name: 'twitter:card', content: 'summary_large_image' }],
  ],
  markdown: {
    lineNumbers: true,
    image: { lazyLoading: true },
    theme: {
      light: 'min-light',
      dark: 'material-theme-ocean',
    },
    container: {
      tipLabel: 'Tip',
      warningLabel: 'Watch out',
      infoLabel: 'Note',
      dangerLabel: 'Stop',
      detailsLabel: 'Details',
    },
    config(md) {
      const wrapRule = (name: string, tag: 'span' | 'div') => {
        const original = md.renderer.rules[name]
        if (!original) return
        md.renderer.rules[name] = (...args) => `<${tag} v-pre>${original(...args)}</${tag}>`
      }
      wrapRule('code_inline', 'span')
      wrapRule('code_block', 'div')
      wrapRule('fence', 'div')
    },
  },
  vite: {
    plugins: [lessonSyncPlugin()],
    build: {
      chunkSizeWarningLimit: 1000,
    },
    server: {
      fs: {
        allow: [path.resolve(__dirname, '../..')],
      },
    },
  },
  themeConfig: {
    logo: '/favicon.svg',
    siteTitle: 'Meridian Learn',
    externalLinkIcon: true,
    skipToContentLabel: 'Skip to lesson',
    sidebarMenuLabel: 'Curriculum',
    returnToTopLabel: 'Back to top of lesson',
    outlineTitle: 'On this lesson',
    darkModeSwitchLabel: 'Shift lighting',
    lightModeSwitchTitle: 'Switch to day shift',
    darkModeSwitchTitle: 'Switch to night shift',
    outline: [2, 3],
    nav: nav(),
    sidebar: sidebar(),
    socialLinks: [
      { icon: 'github', link: `https://github.com/${REPO}`, ariaLabel: 'Curriculum repository' },
    ],
    search: {
      provider: 'local',
      options: {
        detailedView: true,
        translations: {
          button: {
            buttonText: 'Search',
            buttonAriaLabel: 'Search all AI and ML lessons',
          },
          modal: {
            displayDetails: 'Show more',
            resetButtonTitle: 'Clear search',
            backButtonTitle: 'Close search',
            noResultsText: 'No lesson matched — try Find a topic',
            footer: {
              selectText: 'open',
              navigateText: 'move',
              closeText: 'close',
            },
          },
        },
        miniSearch: {
          searchOptions: {
            fuzzy: 0.2,
            prefix: true,
            boost: { title: 4, text: 2, titles: 3 },
          },
        },
      },
    },
    editLink: {
      pattern: ({ relativePath }) => {
        if (relativePath.startsWith('lessons/')) {
          return `https://github.com/sardul3/agent-learn-adk/edit/main/${relativePath}`
        }
        if (relativePath.startsWith('reference/')) {
          const file = relativePath.slice('reference/'.length)
          return `https://github.com/sardul3/agent-learn-adk/edit/main/docs/${file}`
        }
        return `https://github.com/sardul3/agent-learn-adk/edit/main/learn/${relativePath}`
      },
      text: 'Edit source on GitHub',
    },
    lastUpdated: {
      text: 'Source updated',
      formatOptions: { dateStyle: 'medium' },
    },
    docFooter: {
      prev: 'Previous lane',
      next: 'Next lane',
    },
    footer: {
      message: `${shippedLessons.length} shipped lessons · agents (ADK) + ML from zero · Meridian Commerce`,
      copyright: 'Search any topic. Labs live in the repo. This site is the reading room.',
    },
  },
  transformPageData(pageData) {
    const params = pageData.params as
      | { letter?: string; title?: string; summary?: string }
      | undefined
    if (params?.letter && params?.title) {
      pageData.title = `Pack ${params.letter} — ${params.title}`
      if (params.summary) pageData.description = params.summary
    }
    const title = pageData.title || 'Meridian Learn'
    const desc = pageData.description || ''
    pageData.frontmatter.head ??= []
    pageData.frontmatter.head.push(
      ['meta', { property: 'og:title', content: `${title} · Meridian Learn` }],
      ['meta', { property: 'og:description', content: desc }],
      ['meta', { name: 'description', content: desc }],
    )
  },
  transformHead({ assets }) {
    const font = assets.find((file) => /bricolage-grotesque.*\.woff2/.test(file))
    if (!font) return []
    return [
      [
        'link',
        {
          rel: 'preload',
          href: font,
          as: 'font',
          type: 'font/woff2',
          crossorigin: '',
        },
      ],
    ]
  },
})
