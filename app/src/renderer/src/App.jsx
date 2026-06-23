import { useState, useEffect, useRef } from 'react'

const NODE_LABELS = {
  planner: 'Planning',
  researcher: 'Researching',
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
      if (event.type === 'node_start') return  // suppress noise; only show messages
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
  if (event.type === 'done') {
    return <div style={styles.done}>Done</div>
  }
  if (event.type === 'error') {
    return <div style={styles.error}>Error: {event.message}</div>
  }
  return null
}

const styles = {
  root: {
    padding: '32px',
    maxWidth: '860px',
    margin: '0 auto',
    fontFamily: 'system-ui, sans-serif',
  },
  title: {
    margin: '0 0 24px',
    fontSize: '24px',
    fontWeight: 600,
  },
  inputRow: {
    display: 'flex',
    gap: '8px',
    marginBottom: '24px',
  },
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
  feed: {
    display: 'flex',
    flexDirection: 'column',
    gap: '12px',
  },
  card: {
    background: '#f8fafc',
    border: '1px solid #e2e8f0',
    borderRadius: '8px',
    padding: '14px 16px',
  },
  nodeLabel: {
    fontSize: '11px',
    fontWeight: 600,
    textTransform: 'uppercase',
    letterSpacing: '0.05em',
    color: '#64748b',
    marginBottom: '6px',
  },
  content: {
    fontSize: '14px',
    lineHeight: '1.6',
    whiteSpace: 'pre-wrap',
  },
  done: {
    fontSize: '13px',
    color: '#16a34a',
    fontWeight: 500,
  },
  error: {
    fontSize: '13px',
    color: '#dc2626',
    fontWeight: 500,
  },
}
