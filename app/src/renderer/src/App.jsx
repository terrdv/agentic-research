import { useState, useEffect, useRef } from 'react'
import {
  BarChart, Bar,
  LineChart, Line,
  ScatterChart, Scatter,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from 'recharts'

const NODE_LABELS = {
  planner: 'Planning',
  evidence_aggregation: 'Gathering Evidence',
  tools: 'Searching',
  synthesizer: 'Synthesizing',
}

export default function App() {
  const [query, setQuery] = useState('')
  const [events, setEvents] = useState([])
  const [running, setRunning] = useState(false)
  const bottomRef = useRef(null)

  useEffect(() => {
    const handler = (event) => {
      if (event.type === 'node_start') return
      setEvents((prev) => [...prev, event])
      if (event.type === 'done' || event.type === 'error') setRunning(false)
    }
    window.agent.onEvent(handler)
    return () => window.agent.offEvent(handler)
  }, [])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [events])

  const submit = () => {
    if (!query.trim() || running) return
    setEvents([])
    setRunning(true)
    window.agent.query({ query: query.trim(), max_iterations: 5 })
  }

  return (
    <div style={styles.root}>
      <h1 style={styles.title}>Research Agent</h1>

      <div style={styles.inputRow}>
        <input
          style={styles.input}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && submit()}
          placeholder="Enter a research question…"
          disabled={running}
        />
        <button style={styles.button} onClick={submit} disabled={running || !query.trim()}>
          {running ? 'Running…' : 'Research'}
        </button>
      </div>

      <div style={styles.feed}>
        {events.map((event, i) => (
          <EventBlock key={i} event={event} />
        ))}
        <div ref={bottomRef} />
      </div>
    </div>
  )
}

function EventBlock({ event }) {
  if (event.type === 'message') {
    return (
      <div style={styles.card}>
        <div style={styles.nodeLabel}>{NODE_LABELS[event.node] ?? event.node}</div>
        <div style={styles.content}>{event.content}</div>
      </div>
    )
  }

  if (event.type === 'analysis') {
    return <AnalysisBlock event={event} />
  }

  if (event.type === 'done') {
    return <div style={styles.done}>Done</div>
  }

  if (event.type === 'error') {
    return <div style={styles.error}>Error: {event.message}</div>
  }

  return null
}

function AnalysisBlock({ event }) {
  return (
    <div style={styles.analysisCard}>
      <div style={styles.nodeLabel}>Analysis</div>

      <p style={styles.summary}>{event.summary}</p>

      {event.gaps?.length > 0 && (
        <div style={styles.section}>
          <div style={styles.sectionTitle}>Gaps &amp; Open Questions</div>
          <ul style={styles.gapList}>
            {event.gaps.map((gap, i) => <li key={i}>{gap}</li>)}
          </ul>
        </div>
      )}

      {event.charts?.map((chart, i) => (
        <div key={i} style={styles.section}>
          <div style={styles.sectionTitle}>{chart.title}</div>
          <ChartBlock chart={chart} />
        </div>
      ))}
    </div>
  )
}

function ChartBlock({ chart }) {
  const data = chart.data.map((d) => ({ name: d.label, value: d.value }))

  const axes = (
    <>
      <CartesianGrid strokeDasharray="3 3" />
      <XAxis dataKey="name" label={{ value: chart.x_label, position: 'insideBottom', offset: -4 }} />
      <YAxis label={{ value: chart.y_label, angle: -90, position: 'insideLeft' }} />
      <Tooltip />
    </>
  )

  if (chart.chart_type === 'line') {
    return (
      <ResponsiveContainer width="100%" height={260}>
        <LineChart data={data} margin={{ top: 8, right: 16, bottom: 24, left: 32 }}>
          {axes}
          <Line type="monotone" dataKey="value" stroke="#2563eb" dot={false} />
        </LineChart>
      </ResponsiveContainer>
    )
  }

  if (chart.chart_type === 'scatter') {
    return (
      <ResponsiveContainer width="100%" height={260}>
        <ScatterChart margin={{ top: 8, right: 16, bottom: 24, left: 32 }}>
          {axes}
          <Scatter data={data} fill="#2563eb" />
        </ScatterChart>
      </ResponsiveContainer>
    )
  }

  return (
    <ResponsiveContainer width="100%" height={260}>
      <BarChart data={data} margin={{ top: 8, right: 16, bottom: 24, left: 32 }}>
        {axes}
        <Bar dataKey="value" fill="#2563eb" radius={[3, 3, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  )
}

const styles = {
  root: {
    padding: '32px',
    maxWidth: '860px',
    margin: '0 auto',
    fontFamily: 'system-ui, sans-serif',
  },
  title: { margin: '0 0 24px', fontSize: '24px', fontWeight: 600 },
  inputRow: { display: 'flex', gap: '8px', marginBottom: '24px' },
  input: {
    flex: 1,
    padding: '10px 14px',
    fontSize: '15px',
    border: '1px solid #d1d5db',
    borderRadius: '6px',
    outline: 'none',
  },
  button: {
    padding: '10px 20px',
    fontSize: '15px',
    background: '#2563eb',
    color: '#fff',
    border: 'none',
    borderRadius: '6px',
    cursor: 'pointer',
  },
  feed: { display: 'flex', flexDirection: 'column', gap: '12px' },
  card: {
    background: '#f8fafc',
    border: '1px solid #e2e8f0',
    borderRadius: '8px',
    padding: '14px 16px',
  },
  analysisCard: {
    background: '#f0f7ff',
    border: '1px solid #bfdbfe',
    borderRadius: '8px',
    padding: '16px 18px',
  },
  nodeLabel: {
    fontSize: '11px',
    fontWeight: 600,
    textTransform: 'uppercase',
    letterSpacing: '0.05em',
    color: '#64748b',
    marginBottom: '8px',
  },
  summary: { margin: '0 0 12px', fontSize: '14px', lineHeight: '1.6' },
  section: { marginTop: '16px' },
  sectionTitle: { fontSize: '13px', fontWeight: 600, color: '#1e40af', marginBottom: '8px' },
  gapList: { margin: 0, paddingLeft: '20px', fontSize: '14px', lineHeight: '1.7', color: '#374151' },
  content: { fontSize: '14px', lineHeight: '1.6', whiteSpace: 'pre-wrap' },
  done: { fontSize: '13px', color: '#16a34a', fontWeight: 500 },
  error: { fontSize: '13px', color: '#dc2626', fontWeight: 500 },
}
