import { useState, useEffect } from 'react'
import {
  BarChart, Bar,
  LineChart, Line,
  ScatterChart, Scatter,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from 'recharts'

const CITATION_STYLES = ['APA', 'MLA', 'Chicago', 'IEEE', 'Harvard']

const NODE_LABELS = {
  planner: 'Planning the approach',
  evidence_aggregation: 'Gathering evidence',
  tools: 'Searching the literature',
  analyst: 'Analyzing findings',
  synthesizer: 'Writing the report',
}

export default function App() {
  const [query, setQuery] = useState('')
  const [status, setStatus] = useState('idle') // idle | running | done | error
  const [phase, setPhase] = useState('')
  const [report, setReport] = useState('')
  const [analysis, setAnalysis] = useState(null)
  const [errorMsg, setErrorMsg] = useState('')
  const [exporting, setExporting] = useState('idle') // idle | saving | saved | failed
  const [citationStyle, setCitationStyle] = useState('APA')

  useEffect(() => {
    const handler = (event) => {
      switch (event.type) {
        case 'node_start':
          setPhase(NODE_LABELS[event.node] ?? event.node)
          break
        case 'message':
          if (event.node === 'synthesizer') setReport((prev) => prev + event.content)
          break
        case 'analysis':
          setAnalysis(event)
          break
        case 'done':
          setStatus('done')
          setPhase('')
          break
        case 'error':
          setErrorMsg(event.message)
          setStatus('error')
          setPhase('')
          break
        default:
          break
      }
    }
    window.agent.onEvent(handler)
    return () => window.agent.offEvent(handler)
  }, [])

  const submit = () => {
    const q = query.trim()
    if (!q || status === 'running') return
    setReport('')
    setAnalysis(null)
    setErrorMsg('')
    setPhase(NODE_LABELS.planner)
    setStatus('running')
    setExporting('idle')
    window.agent.query({ query: q, max_iterations: 3, citation_style: citationStyle })
  }

  const reset = () => {
    setStatus('idle')
    setReport('')
    setAnalysis(null)
    setErrorMsg('')
    setPhase('')
    setExporting('idle')
  }

  const exportPdf = async () => {
    if (exporting === 'saving') return
    setExporting('saving')
    try {
      const res = await window.agent.exportPdf(pdfName(query))
      if (res?.ok) setExporting('saved')
      else if (res?.canceled) setExporting('idle')
      else setExporting('failed')
    } catch {
      setExporting('failed')
    }
  }

  const onKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      submit()
    }
  }

  const idle = status === 'idle'

  return (
    <div style={styles.page}>
      <header className="no-print" style={styles.header}>
        <span style={styles.wordmark}>Research</span>
        {!idle && (
          <div style={styles.headerActions}>
            {status === 'done' && report && (
              <button
                style={styles.newBtn}
                onClick={exportPdf}
                disabled={exporting === 'saving'}
              >
                {EXPORT_LABELS[exporting]}
              </button>
            )}
            <button style={styles.newBtn} onClick={reset} disabled={status === 'running'}>
              New search
            </button>
          </div>
        )}
      </header>

      <main style={{ ...styles.main, justifyContent: idle ? 'center' : 'flex-start' }}>
        {idle && (
          <div style={styles.introBlock}>
            <h1 style={styles.introTitle}>What would you like to research?</h1>
            <p style={styles.introSub}>
              A question about the literature — the agent searches, weighs the evidence, and
              writes you a sourced report.
            </p>
          </div>
        )}

        <div className="no-print" style={styles.promptWrap}>
          <textarea
            style={styles.input}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={onKeyDown}
            placeholder="e.g. Is clinical psychedelic treatment effective for mental health disorders?"
            rows={idle ? 3 : 2}
            disabled={status === 'running'}
            autoFocus
          />
          <div style={styles.promptRow}>
            <label style={styles.selectLabel}>
              Citation style
              <select
                style={styles.select}
                value={citationStyle}
                onChange={(e) => setCitationStyle(e.target.value)}
                disabled={status === 'running'}
              >
                {CITATION_STYLES.map((s) => <option key={s} value={s}>{s}</option>)}
              </select>
            </label>
            <div style={styles.promptRowRight}>
              <span style={styles.hint}>Enter to search</span>
              <button
                style={{ ...styles.button, ...(canSubmit(query, status) ? {} : styles.buttonDisabled) }}
                onClick={submit}
                disabled={!canSubmit(query, status)}
              >
                {status === 'running' ? 'Researching…' : 'Research'}
              </button>
            </div>
          </div>
        </div>

        {status === 'running' && <StatusLine phase={phase} />}

        {status === 'error' && (
          <div style={styles.error} role="alert">
            <strong>Something went wrong.</strong> {errorMsg}
          </div>
        )}

        {(report || analysis) && (
          <article style={styles.report}>
            {report && <Markdown text={report} />}

            {analysis?.gaps?.length > 0 && (
              <section style={styles.section}>
                <h2 style={styles.h2}>Gaps &amp; open questions</h2>
                <ul style={styles.gapList}>
                  {analysis.gaps.map((g, i) => <li key={i} style={styles.gapItem}>{g}</li>)}
                </ul>
              </section>
            )}

            {analysis?.charts?.map((chart, i) => (
              <section key={i} style={styles.section}>
                <h2 style={styles.h2}>{chart.title}</h2>
                <ChartBlock chart={chart} />
              </section>
            ))}
          </article>
        )}
      </main>
    </div>
  )
}

function canSubmit(query, status) {
  return query.trim().length > 0 && status !== 'running'
}

function StatusLine({ phase }) {
  return (
    <div className="no-print" style={styles.statusLine} aria-live="polite">
      <span style={styles.dot} />
      <span>{phase || 'Working…'}</span>
    </div>
  )
}

const EXPORT_LABELS = {
  idle: 'Save as PDF',
  saving: 'Saving…',
  saved: 'Saved ✓',
  failed: 'Save failed — retry',
}

function pdfName(query) {
  const slug = query.trim().toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '')
  return `${(slug || 'research-report').slice(0, 60)}.pdf`
}

/* ---------- Minimal Markdown renderer (headings, lists, bold/italic/code, links) ---------- */

function Markdown({ text }) {
  return <>{parseBlocks(text)}</>
}

function parseBlocks(text) {
  const lines = text.replace(/\r\n/g, '\n').split('\n')
  const blocks = []
  let para = []
  let list = null // { ordered: bool, items: [] }

  const flushPara = () => {
    if (para.length) {
      blocks.push({ type: 'p', text: para.join(' ') })
      para = []
    }
  }
  const flushList = () => {
    if (list) {
      blocks.push({ type: 'ul', ordered: list.ordered, items: list.items })
      list = null
    }
  }

  for (const raw of lines) {
    const line = raw.trimEnd()
    const heading = line.match(/^(#{1,4})\s+(.*)$/)
    const bullet = line.match(/^\s*[-*]\s+(.*)$/)
    const numbered = line.match(/^\s*\d+\.\s+(.*)$/)

    if (heading) {
      flushPara(); flushList()
      blocks.push({ type: 'h', level: heading[1].length, text: heading[2] })
    } else if (bullet || numbered) {
      flushPara()
      const ordered = Boolean(numbered)
      if (!list || list.ordered !== ordered) { flushList(); list = { ordered, items: [] } }
      list.items.push((bullet || numbered)[1])
    } else if (line.trim() === '') {
      flushPara(); flushList()
    } else {
      flushList()
      para.push(line.trim())
    }
  }
  flushPara(); flushList()

  return blocks.map((b, i) => {
    if (b.type === 'h') {
      const style = b.level <= 1 ? styles.h1 : b.level === 2 ? styles.h2 : styles.h3
      const Tag = `h${Math.min(b.level + 1, 4)}`
      return <Tag key={i} style={style}>{renderInline(b.text)}</Tag>
    }
    if (b.type === 'ul') {
      const Tag = b.ordered ? 'ol' : 'ul'
      return (
        <Tag key={i} style={styles.list}>
          {b.items.map((it, j) => <li key={j} style={styles.li}>{renderInline(it)}</li>)}
        </Tag>
      )
    }
    return <p key={i} style={styles.p}>{renderInline(b.text)}</p>
  })
}

// inline: **bold**, *italic*, `code`, [text](url)
const INLINE_RE = /(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`|\[[^\]]+\]\([^)]+\))/g

function renderInline(text) {
  const parts = text.split(INLINE_RE).filter(Boolean)
  return parts.map((part, i) => {
    if (/^\*\*[^*]+\*\*$/.test(part)) return <strong key={i}>{part.slice(2, -2)}</strong>
    if (/^\*[^*]+\*$/.test(part)) return <em key={i}>{part.slice(1, -1)}</em>
    if (/^`[^`]+`$/.test(part)) return <code key={i} style={styles.code}>{part.slice(1, -1)}</code>
    const link = part.match(/^\[([^\]]+)\]\(([^)]+)\)$/)
    if (link) return <a key={i} href={link[2]} style={styles.link} target="_blank" rel="noreferrer">{link[1]}</a>
    return part
  })
}

/* ---------- Charts ---------- */

function ChartBlock({ chart }) {
  const data = chart.data.map((d) => ({ name: d.label, value: d.value }))
  const stroke = 'var(--color-accent)'
  const axes = (
    <>
      <CartesianGrid strokeDasharray="3 3" stroke="#EDEBE4" />
      <XAxis dataKey="name" tick={{ fontSize: 12, fill: '#6b6b66' }}
        label={{ value: chart.x_label, position: 'insideBottom', offset: -4, fontSize: 12, fill: '#6b6b66' }} />
      <YAxis tick={{ fontSize: 12, fill: '#6b6b66' }}
        label={{ value: chart.y_label, angle: -90, position: 'insideLeft', fontSize: 12, fill: '#6b6b66' }} />
      <Tooltip contentStyle={{ fontFamily: 'var(--font-body)', fontSize: 13, borderColor: '#E7E5DF' }} />
    </>
  )

  if (chart.chart_type === 'line') {
    return (
      <ResponsiveContainer width="100%" height={280}>
        <LineChart data={data} margin={{ top: 8, right: 16, bottom: 28, left: 36 }}>
          {axes}<Line type="monotone" dataKey="value" stroke={stroke} strokeWidth={2} dot={false} />
        </LineChart>
      </ResponsiveContainer>
    )
  }
  if (chart.chart_type === 'scatter') {
    return (
      <ResponsiveContainer width="100%" height={280}>
        <ScatterChart margin={{ top: 8, right: 16, bottom: 28, left: 36 }}>
          {axes}<Scatter data={data} fill={stroke} />
        </ScatterChart>
      </ResponsiveContainer>
    )
  }
  return (
    <ResponsiveContainer width="100%" height={280}>
      <BarChart data={data} margin={{ top: 8, right: 16, bottom: 28, left: 36 }}>
        {axes}<Bar dataKey="value" fill={stroke} radius={[3, 3, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  )
}

/* ---------- Styles ---------- */

const styles = {
  page: { minHeight: '100dvh', display: 'flex', flexDirection: 'column' },
  header: {
    display: 'flex', alignItems: 'center', justifyContent: 'space-between',
    padding: '16px 28px', borderBottom: '1px solid var(--color-hairline)',
  },
  wordmark: {
    fontFamily: 'var(--font-serif)', fontSize: 20, fontWeight: 600,
    letterSpacing: '0.01em', color: 'var(--color-fg)',
  },
  headerActions: { display: 'flex', alignItems: 'center', gap: 8 },
  newBtn: {
    fontFamily: 'var(--font-body)', fontSize: 13, color: 'var(--color-secondary)',
    background: 'transparent', border: '1px solid var(--color-hairline)',
    borderRadius: 'var(--radius)', padding: '6px 12px', cursor: 'pointer',
  },
  main: {
    flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center',
    width: '100%', maxWidth: 760, margin: '0 auto', padding: '40px 28px 80px',
  },
  introBlock: { textAlign: 'center', marginBottom: 28, maxWidth: '52ch' },
  introTitle: {
    fontFamily: 'var(--font-serif)', fontWeight: 600, fontSize: 34,
    lineHeight: 1.2, margin: '0 0 12px',
  },
  introSub: { fontSize: 16, color: 'var(--color-muted-fg)', margin: 0, lineHeight: 1.6 },

  promptWrap: {
    width: '100%', background: 'var(--color-surface)',
    border: '1px solid var(--color-hairline)', borderRadius: 10, padding: 14,
  },
  input: {
    width: '100%', border: 'none', outline: 'none', resize: 'none',
    fontFamily: 'var(--font-body)', fontSize: 17, lineHeight: 1.5,
    color: 'var(--color-fg)', background: 'transparent',
  },
  promptRow: {
    display: 'flex', alignItems: 'center', justifyContent: 'space-between',
    marginTop: 10, paddingTop: 10, borderTop: '1px solid var(--color-hairline)',
  },
  promptRowRight: { display: 'flex', alignItems: 'center', gap: 12 },
  hint: { fontSize: 12, color: 'var(--color-muted-fg)' },
  selectLabel: {
    display: 'flex', alignItems: 'center', gap: 8,
    fontSize: 12, color: 'var(--color-muted-fg)',
  },
  select: {
    fontFamily: 'var(--font-body)', fontSize: 13, color: 'var(--color-fg)',
    background: 'var(--color-surface)', border: '1px solid var(--color-hairline)',
    borderRadius: 'var(--radius)', padding: '5px 8px', cursor: 'pointer',
  },
  button: {
    fontFamily: 'var(--font-body)', fontSize: 15, fontWeight: 700,
    color: '#fff', background: 'var(--color-accent)', border: 'none',
    borderRadius: 'var(--radius)', padding: '9px 20px', cursor: 'pointer',
    transition: 'background 180ms ease',
  },
  buttonDisabled: { background: '#CBBFA3', cursor: 'not-allowed' },

  statusLine: {
    display: 'flex', alignItems: 'center', gap: 10, marginTop: 28,
    fontSize: 15, color: 'var(--color-secondary)', alignSelf: 'flex-start',
  },
  dot: {
    width: 9, height: 9, borderRadius: '50%', background: 'var(--color-accent)',
    animation: 'pulse 1.2s ease-in-out infinite',
  },

  error: {
    marginTop: 28, alignSelf: 'stretch', fontSize: 14, lineHeight: 1.6,
    color: 'var(--color-destructive)', background: '#FCF2F2',
    border: '1px solid #F0D5D5', borderRadius: 'var(--radius)', padding: '12px 14px',
  },

  report: { marginTop: 40, alignSelf: 'stretch', width: '100%', maxWidth: 'var(--measure)' },
  h1: { fontFamily: 'var(--font-serif)', fontWeight: 600, fontSize: 30, lineHeight: 1.25, margin: '0 0 16px' },
  h2: { fontFamily: 'var(--font-serif)', fontWeight: 600, fontSize: 23, lineHeight: 1.3, margin: '32px 0 12px' },
  h3: { fontFamily: 'var(--font-serif)', fontWeight: 600, fontSize: 19, lineHeight: 1.35, margin: '24px 0 8px' },
  p: { fontSize: 17, lineHeight: 1.7, margin: '0 0 16px', color: '#252525' },
  list: { margin: '0 0 16px', paddingLeft: 22 },
  li: { fontSize: 17, lineHeight: 1.7, marginBottom: 6, color: '#252525' },
  link: { color: 'var(--color-accent)', textDecorationThickness: '1px', textUnderlineOffset: '2px' },
  code: {
    fontFamily: 'ui-monospace, SFMono-Regular, Menlo, monospace', fontSize: '0.88em',
    background: '#F3F1EA', padding: '1px 5px', borderRadius: 4,
  },

  section: { marginTop: 8 },
  gapList: { margin: '0 0 16px', paddingLeft: 22 },
  gapItem: { fontSize: 16, lineHeight: 1.65, marginBottom: 6, color: '#252525' },
}
