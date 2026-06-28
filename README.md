# Agentic Research

An AI research assistant that searches academic literature, aggregates evidence, and synthesizes findings into structured reports with charts.

Built with LangGraph (Python) + Electron (React).

## How it works

A LangGraph agent loops through four nodes:

1. **Planner** — decides whether to search for more evidence or synthesize
2. **Evidence aggregation** — calls search tools and accumulates findings
3. **Analyst** — reviews evidence, identifies gaps, generates chart specs
4. **Synthesizer** — produces the final written report

The Electron app communicates with the Python backend over stdio (newline-delimited JSON), streaming results to the UI in real time.

## Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- An Anthropic API key

### Backend

```bash
cd agent
cp .env.example .env   # add your ANTHROPIC_API_KEY
pip install -e .
```

### Electron app

```bash
cd app
npm install
npm run dev
```

## Search tools

- **Google Scholar** via `scholarly`
- **Semantic Scholar** — free, no credentials required

## Project structure


