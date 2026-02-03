# 🜆 The Deep Prospecting Engine

A local, agentic application that leverages Gemini Deep Research to identify high-value AI/ML sales opportunities for specific clients, utilizing "silent" historical memory to improve recommendations over time.

## Architecture

```
User/UI → Input Processor → Gemini Deep Research API
                ↓
         Context Merger ← ChromaDB (Similar Verticals + Plays)
                ↓
         Competitor Scout (Case Studies)
                ↓
         Id8 Iteration Loop
           ├── Divergent (10+ Ideas)
           └── Convergent Refiner (Top 3)
                ↓
         Asset Generator (Pellera Voice)
                ↓
         Markdown Files (One-Pagers + Strategic Plans)
                ↓
         ChromaStore → ChromaDB (Feedback Loop)
```

## Stack

- **Orchestration:** LangGraph
- **LLM:** Google Gemini (Deep Research API)
- **Vector DB:** ChromaDB
- **UI:** Streamlit
- **Language:** Python 3.11+
- **Deployment:** Docker

## Quick Start

```bash
# Clone
git clone https://github.com/aquaregiaswarm-blip/deep-prospecting-engine.git
cd deep-prospecting-engine

# Setup
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env with your GEMINI_API_KEY

# Run
streamlit run src/app.py

# Test
pytest tests/ -v
```

## Project Structure

```
deep-prospecting-engine/
├── src/
│   ├── app.py                  # Streamlit UI
│   ├── graph/
│   │   ├── __init__.py
│   │   ├── state.py            # LangGraph state schema
│   │   ├── nodes/
│   │   │   ├── __init__.py
│   │   │   ├── input_processor.py
│   │   │   ├── deep_research.py
│   │   │   ├── context_merger.py
│   │   │   ├── competitor_scout.py
│   │   │   ├── ideation.py
│   │   │   └── asset_generator.py
│   │   └── workflow.py         # LangGraph workflow definition
│   ├── memory/
│   │   ├── __init__.py
│   │   ├── chroma_query.py
│   │   └── chroma_store.py
│   ├── prompts/
│   │   ├── __init__.py
│   │   ├── base_research.py
│   │   ├── pellera_voice.py
│   │   └── ideation.py
│   └── config.py               # Settings & env management
├── tests/
│   ├── __init__.py
│   ├── test_input_processor.py
│   ├── test_deep_research.py
│   ├── test_context_merger.py
│   ├── test_competitor_scout.py
│   ├── test_ideation.py
│   ├── test_asset_generator.py
│   ├── test_memory.py
│   └── test_workflow.py
├── output/                     # Generated markdown files
├── data/                       # ChromaDB persistent storage
├── .env.example
├── .gitignore
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── pyproject.toml
└── README.md
```

## Epics

1. **Core Infrastructure & Data Ingestion** — Environment, UI, API integration
2. **Deep Research & Competitive Analysis** — Gemini research, vertical ID, competitor scouting
3. **Silent Memory (Vector Knowledge Base)** — ChromaDB for learning from past wins
4. **Ideation Loop ("id8")** — Divergent/convergent idea generation
5. **Asset Generation & Voice** — Pellera-voiced markdown deliverables

## License

Proprietary — Pellera
