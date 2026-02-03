# 🜆 The Deep Prospecting Engine

A local, agentic application that leverages Gemini Deep Research to identify high-value AI/ML sales opportunities for specific clients, utilizing "silent" historical memory to improve recommendations over time.

## Architecture

```
┌──────────────────────┐      ┌──────────────────────────────┐
│   Next.js Frontend   │◄────►│     FastAPI Backend (API)    │
│   (Port 3000)        │ SSE  │     (Port 8000)              │
└──────────────────────┘      └──────────┬───────────────────┘
                                         │
                               ┌─────────▼─────────┐
                               │  LangGraph Pipeline │
                               └─────────┬─────────┘
                                         │
         ┌───────────────────────────────┤
         │                               │
    ┌────▼────┐                    ┌─────▼─────┐
    │ ChromaDB │                    │ Gemini API │
    │ (Memory) │                    │  (Research)│
    └─────────┘                    └───────────┘
```

### Pipeline Flow

```
Input Processor → Gemini Deep Research → Context Merger (ChromaDB) →
Competitor Scout → Divergent Ideation (10+ ideas) →
Convergent Refinement (Top 3) → Asset Generator (Pellera Voice) →
Knowledge Capture → ChromaDB
```

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/prospect` | Start a new prospecting run |
| `GET` | `/api/prospect/{run_id}/status` | Get run status & results |
| `GET` | `/api/prospect/{run_id}/stream` | SSE stream for real-time progress |
| `GET` | `/api/runs` | List all runs |
| `GET` | `/api/health` | Health check |

## Stack

- **Backend:** FastAPI + Uvicorn
- **Orchestration:** LangGraph
- **LLM:** Google Gemini (Deep Research API)
- **Vector DB:** ChromaDB
- **Frontend:** Next.js 14 + Tailwind CSS + TypeScript
- **Language:** Python 3.11+ / TypeScript
- **Deployment:** Docker (multi-service)

## Quick Start

### Backend

```bash
# Clone
git clone https://github.com/aquaregiaswarm-blip/deep-prospecting-engine.git
cd deep-prospecting-engine

# Setup Python
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env with your GEMINI_API_KEY

# Run API server
uvicorn src.api.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
# → http://localhost:3000
```

### Docker (Production)

```bash
docker compose up --build
# API: http://localhost:8000
# UI:  http://localhost:3000
```

### Tests

```bash
source .venv/bin/activate
pytest tests/ -v
```

## Project Structure

```
deep-prospecting-engine/
├── src/
│   ├── api/
│   │   ├── __init__.py
│   │   ├── main.py             # FastAPI application
│   │   ├── models.py           # Request/response schemas
│   │   └── run_store.py        # In-memory run state management
│   ├── graph/
│   │   ├── __init__.py
│   │   ├── state.py            # LangGraph state schema
│   │   ├── nodes/
│   │   │   ├── input_processor.py
│   │   │   ├── deep_research.py
│   │   │   ├── context_merger.py
│   │   │   ├── competitor_scout.py
│   │   │   ├── ideation.py
│   │   │   └── asset_generator.py
│   │   └── workflow.py         # LangGraph workflow definition
│   ├── memory/
│   │   ├── chroma_query.py
│   │   └── chroma_store.py
│   ├── prompts/
│   │   ├── base_research.py
│   │   ├── pellera_voice.py
│   │   └── ideation.py
│   └── config.py               # Settings & env management
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx
│   │   │   ├── page.tsx              # Dashboard
│   │   │   └── prospect/
│   │   │       ├── new/page.tsx      # New prospect form
│   │   │       └── [runId]/page.tsx  # Run detail + live progress
│   │   ├── components/
│   │   │   ├── sidebar.tsx
│   │   │   ├── theme-provider.tsx
│   │   │   ├── pipeline-progress.tsx
│   │   │   ├── run-card.tsx
│   │   │   └── ui/                   # Reusable UI primitives
│   │   └── lib/
│   │       ├── api.ts                # API client
│   │       └── utils.ts
│   ├── package.json
│   ├── tailwind.config.ts
│   └── Dockerfile
├── tests/
│   ├── test_api.py             # API endpoint tests
│   ├── test_input_processor.py
│   ├── test_deep_research.py
│   ├── test_context_merger.py
│   ├── test_competitor_scout.py
│   ├── test_ideation.py
│   ├── test_asset_generator.py
│   ├── test_memory.py
│   └── test_workflow.py
├── docker-compose.yml          # Multi-service orchestration
├── Dockerfile                  # All-in-one image
├── Dockerfile.api              # API-only image
├── requirements.txt
└── README.md
```

## Features

- **Real-time progress** — SSE streams pipeline node status as it runs
- **Dark mode** — Full dark mode support
- **Downloadable assets** — One-pagers and strategic plans as markdown
- **Pellera branding** — Professional, authoritative UI
- **Silent memory** — ChromaDB learns from past runs to improve future recommendations
- **Background execution** — Pipeline runs asynchronously; poll or stream for updates

## License

Proprietary — Pellera
