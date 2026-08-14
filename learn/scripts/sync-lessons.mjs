/**
 * Converts repo markdown (lessons/ + docs/) into VitePress pages.
 * Source of truth stays in the original files — generated output is gitignored.
 */
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath, pathToFileURL } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const LEARN_ROOT = path.resolve(__dirname, '..')
const REPO_ROOT = path.resolve(LEARN_ROOT, '..')
const LESSONS_SRC = path.join(REPO_ROOT, 'lessons')
const DOCS_SRC = path.join(REPO_ROOT, 'docs')
const LESSONS_OUT = path.join(LEARN_ROOT, 'lessons')
const REFERENCE_OUT = path.join(LEARN_ROOT, 'reference')

export const GITHUB_REPO = 'sardul3/agent-learn-adk'
export const GITHUB_BLOB = `https://github.com/${GITHUB_REPO}/blob/main`

const PACK_BY_N = {
  1: 'A', 2: 'A', 3: 'A', 4: 'A', 5: 'A', 6: 'A', 7: 'A',
  8: 'B', 9: 'B', 10: 'B', 11: 'B', 12: 'B',
  13: 'C', 14: 'C', 15: 'C', 16: 'C', 17: 'C',
  18: 'D', 19: 'D', 20: 'D', 21: 'D', 22: 'D',
  23: 'E', 24: 'E', 25: 'E', 26: 'E', 27: 'E', 42: 'E',
  28: 'F', 29: 'F', 30: 'F', 31: 'F', 32: 'F', 43: 'F', 44: 'F',
  33: 'G', 34: 'G', 35: 'G', 36: 'G', 37: 'G', 38: 'G', 39: 'G', 40: 'G',
  45: 'G', 46: 'G', 47: 'G', 48: 'G', 49: 'G', 50: 'G', 51: 'G',
  41: 'Ops',
}

function yamlEscape(value) {
  if (value == null) return '""'
  const s = String(value).replace(/\s+/g, ' ').trim()
  if (/[:#&*!|>%@`'"{}[\],]|^\s|\s$/.test(s) || s.length === 0) {
    return `"${s.replace(/\\/g, '\\\\').replace(/"/g, '\\"')}"`
  }
  return s
}

function field(raw, label) {
  const re = new RegExp(`\\*\\*${label}:\\*\\*\\s*(.+)`)
  const m = raw.match(re)
  return m ? m[1].replace(/\s+/g, ' ').trim() : ''
}

function firstGlance(body) {
  const m = body.match(/## At a glance\s+([\s\S]*?)(?:\n---|\n## )/i)
  if (!m) return ''
  const para = m[1]
    .replace(/\|[^\n]+\|/g, ' ')
    .replace(/[-*|`>#]/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()
  return para.slice(0, 220)
}

function convertCallouts(md) {
  return md.replace(
    /^> \*\*(Tip|Watch out|Note|Warning|Important|Caution):\*\*\s*(.+)$/gim,
    (_, kind, rest) => {
      const map = {
        tip: 'TIP',
        'watch out': 'WARNING',
        note: 'NOTE',
        warning: 'WARNING',
        important: 'IMPORTANT',
        caution: 'CAUTION',
      }
      const token = map[kind.toLowerCase()] || 'NOTE'
      const title = kind.toLowerCase() === 'watch out' ? ' Watch out' : ''
      return `> [!${token}]${title}\n> ${rest}`
    },
  )
}

function wrapAnswers(md) {
  const idx = md.search(/^### Answers\s*$/m)
  if (idx < 0) return md
  const after = md.slice(idx)
  const nextH2 = after.search(/\n## /)
  const block = (nextH2 >= 0 ? after.slice(0, nextH2) : after)
    .trim()
    .replace(/\n---\s*$/, '')
  const rest = nextH2 >= 0 ? after.slice(nextH2) : ''
  return `${md.slice(0, idx)}::: details Peek at answers — try the questions first\n${block}\n:::\n\n${rest}`
}

function stripNavigate(md) {
  return md.replace(/\n## Navigate\s*\n[\s\S]*$/, '\n')
}

function rewriteLinks(md) {
  return md.replace(/\[([^\]]+)\]\(([^)]+)\)/g, (full, text, href) => {
    if (/^(https?:|mailto:|#)/i.test(href)) return full

    const [pathPart, hash = ''] = href.split('#')
    const anchor = hash ? `#${hash}` : ''
    const cleaned = pathPart.replace(/\\/g, '/')

    const lessonMatch = cleaned.match(/(?:^|\/)(\d{2}-[a-z0-9-]+)\.md$/i)
    if (lessonMatch) {
      return `[${text}](/lessons/${lessonMatch[1]}${anchor})`
    }

    const docsMatch = cleaned.match(/(?:^|\/)docs\/([^)]+?)\.md$/i)
    if (docsMatch) {
      const slug = docsMatch[1].replace(/\.md$/i, '')
      return `[${text}](/reference/${slug}${anchor})`
    }

    const projectMatch = cleaned.match(/(?:^|\/)(project\/.+)$/i)
    if (projectMatch) {
      return `[${text}](${GITHUB_BLOB}/${projectMatch[1]}${anchor})`
    }

    if (cleaned.endsWith('.md')) {
      const base = path.basename(cleaned, '.md')
      if (/^(curriculum-roadmap|gap-analysis-sme|meridian-northstar|NATIVE-ADK)$/i.test(base)) {
        return `[${text}](/reference/${base}${anchor})`
      }
    }

    return full
  })
}

function transformLesson(filename, raw) {
  const slug = filename.replace(/\.md$/, '')
  const n = Number((slug.match(/^(\d+)/) || [0, 0])[1])
  const titleLine = (raw.match(/^#\s+(.+)$/m) || [, slug])[1]
  const title = titleLine.replace(/^Lesson\s+\d+\s+[—–-]\s+/, '').trim()
  const level = field(raw, 'Level')
  const duration = field(raw, 'Time').replace(/^~/, '')
  const prerequisites = field(raw, 'Prerequisites')
  const outcome = field(raw, 'Lab outcome')
  const pack = PACK_BY_N[n] || ''

  let body = raw.replace(/^#\s+.+\n+/, '')
  body = body.replace(
    /(\*\*(?:Level|Time|Prerequisites|Lab outcome|Standard):\*\*.+\n)+/,
    '',
  )
  body = body.replace(/^\n+---\n+/, '')
  body = convertCallouts(body)
  body = wrapAnswers(body)
  body = stripNavigate(body)
  body = rewriteLinks(body)
  body = body.replace(/\n{4,}/g, '\n\n\n')

  const description = firstGlance(raw) || outcome || title

  const fm = [
    '---',
    `title: ${yamlEscape(title)}`,
    `description: ${yamlEscape(description)}`,
    `outline: [2, 3]`,
    `lesson: ${n}`,
    `pack: ${yamlEscape(pack)}`,
    `level: ${yamlEscape(level)}`,
    `duration: ${yamlEscape(duration)}`,
    `prerequisites: ${yamlEscape(prerequisites)}`,
    `outcome: ${yamlEscape(outcome)}`,
    `editLink: true`,
    '---',
    '',
    `<!-- Generated from lessons/${filename}. Edit the source file, not this copy. -->`,
    '',
    `# ${titleLine}`,
    '',
  ].join('\n')

  return fm + body.trim() + '\n'
}

function transformDoc(filename, raw) {
  const slug = filename.replace(/\.md$/, '')
  const title = ((raw.match(/^#\s+(.+)$/m) || [, slug])[1] || slug).trim()
  let body = convertCallouts(raw)
  body = rewriteLinks(body)
  const fm = [
    '---',
    `title: ${yamlEscape(title)}`,
    `description: ${yamlEscape(title)}`,
    `outline: [2, 3]`,
    '---',
    '',
    `<!-- Generated from docs/${filename}. Edit the source file, not this copy. -->`,
    '',
  ].join('\n')
  return fm + body.replace(/^---\n[\s\S]*?\n---\n/, '')
}

function ensureDir(dir) {
  fs.mkdirSync(dir, { recursive: true })
}

function writeIfChanged(file, contents) {
  if (fs.existsSync(file) && fs.readFileSync(file, 'utf8') === contents) return false
  fs.writeFileSync(file, contents)
  return true
}

export function syncLessons() {
  ensureDir(LESSONS_OUT)
  ensureDir(REFERENCE_OUT)

  const lessonFiles = fs
    .readdirSync(LESSONS_SRC)
    .filter((f) => /^\d+-.+\.md$/.test(f))
    .sort()

  const keep = new Set(['index.md'])
  for (const file of lessonFiles) {
    const out = transformLesson(file, fs.readFileSync(path.join(LESSONS_SRC, file), 'utf8'))
    writeIfChanged(path.join(LESSONS_OUT, file), out)
    keep.add(file)
  }
  for (const existing of fs.readdirSync(LESSONS_OUT)) {
    if (existing.endsWith('.md') && !keep.has(existing)) {
      fs.unlinkSync(path.join(LESSONS_OUT, existing))
    }
  }

  const docKeep = new Set(['index.md'])
  if (fs.existsSync(DOCS_SRC)) {
    for (const file of fs.readdirSync(DOCS_SRC).filter((f) => f.endsWith('.md'))) {
      const out = transformDoc(file, fs.readFileSync(path.join(DOCS_SRC, file), 'utf8'))
      writeIfChanged(path.join(REFERENCE_OUT, file), out)
      docKeep.add(file)
    }
  }
  for (const existing of fs.readdirSync(REFERENCE_OUT)) {
    if (existing.endsWith('.md') && !docKeep.has(existing)) {
      fs.unlinkSync(path.join(REFERENCE_OUT, existing))
    }
  }

  return { lessons: lessonFiles.length }
}

export const watchRoots = [LESSONS_SRC, DOCS_SRC]

if (process.argv[1] && import.meta.url === pathToFileURL(path.resolve(process.argv[1])).href) {
  const { lessons } = syncLessons()
  console.log(`Synced ${lessons} lessons → learn/lessons and docs → learn/reference`)
}
