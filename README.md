# AutoApply

Autonomous AI job application agent. Give it your resume and a target role — it finds real job postings, scores your fit, writes tailored cover letters, and critiques them until they pass a strict quality checklist.

**Intelligence layer:** Claude Desktop via MCP. All reasoning, scoring, writing, and reviewing is done by Claude. The Python backend handles data storage only.

---

## How it works

```
You → Claude Desktop chat
         ↓
   AutoApply MCP tools
         ↓
   PostgreSQL + pgvector
```

1. Share your name and email → Claude creates your profile
2. Upload your resume PDF → Claude indexes it (RAG-ready, 384-dim embeddings)
3. Tell Claude your target role, location, and experience level
4. Claude searches for real job postings (greenhouse.io, lever.co, arc.dev, company career pages)
5. Claude scores each job against your resume (0–100 fit score)
6. Claude writes a cover letter for every APPLY-scored job, runs a self-check, and saves it
7. Claude critiques each letter and revises until approved
8. Approved letters are stored as embeddings — future letters improve with every session

---

## Stack

| Layer | Technology |
|---|---|
| Intelligence | Claude Desktop (MCP) |
| API | FastAPI |
| Database | PostgreSQL 16 + pgvector |
| Embeddings | sentence-transformers `all-MiniLM-L6-v2` (local, no API key) |
| Job search | Claude built-in web search (primary) · Tavily API (fallback) |
| Admin panel | SQLAdmin at `/admin` |
| ORM | SQLAlchemy 2.0 + Alembic |

---

## Setup

### 1. Prerequisites

- Python 3.12
- Docker (for PostgreSQL)
- Claude Desktop with MCP support

### 2. Install

```bash
git clone https://github.com/ZahraYasin2209/autoapply-ai.git
cd autoapply-ai
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r config/requirements/dev.txt
```

### 3. Configure environment

```bash
cp .env.example .env
# Edit .env — set DATABASE_URL, TAVILY_API_KEY, GROQ_API_KEY
```

### 4. Start the database

```bash
make db
make migrate
```

### 5. Start the API server

```bash
make run
```

- Admin panel: http://localhost:8000/admin
- Health check: http://localhost:8000/health

### 6. Connect Claude Desktop

Copy the config below to `%APPDATA%\Claude\claude_desktop_config.json` (update the path to match your machine):

```json
{
  "mcpServers": {
    "autoapply": {
      "command": "C:\\path\\to\\autoapply-ai\\venv\\Scripts\\python.exe",
      "args": ["C:\\path\\to\\autoapply-ai\\autoapply\\ai\\mcp_server\\mcp_server.py"],
      "env": {
        "PYTHONPATH": "C:\\path\\to\\autoapply-ai"
      }
    }
  }
}
```

Restart Claude Desktop. The hammer icon (🔨) in the chat toolbar confirms the MCP server is connected.

### 7. Start using AutoApply

Open Claude Desktop and say: **"Hi, I'm [Your Name]"**

Claude will walk you through the rest.

---

## Make commands

| Command | What it does |
|---|---|
| `make install` | Install Python dependencies |
| `make run` | Start FastAPI dev server |
| `make db` | Start PostgreSQL via Docker |
| `make migrate` | Run Alembic migrations |
| `make migration msg="describe change"` | Generate a new migration |
| `make test` | Run test suite |
| `make mcp` | Start MCP server directly |
| `make up` | Start DB + migrate + run server (one command) |

---

## Project structure

```
autoapply/
├── ai/
│   ├── prompts/          # All Claude behaviour and LLM prompt strings live here
│   │   ├── agent_instructions.py   # System-level instructions (always active)
│   │   ├── run_pipeline.py         # Full pipeline steps
│   │   ├── cover_letter.py         # Cover letter generation prompt
│   │   ├── fit_score.py            # Fit scoring prompt
│   │   ├── critic.py               # Critic + revision prompts
│   │   └── ...
│   ├── utils/            # Static-method classes for all backend logic
│   │   ├── ResumeUtils.py
│   │   ├── JobSearchUtils.py
│   │   ├── FitScorerUtils.py
│   │   ├── CoverLetterUtils.py
│   │   ├── CriticUtils.py
│   │   ├── SaveUtils.py
│   │   ├── MemoryUtils.py
│   │   ├── ContextUtils.py
│   │   ├── Embedder.py
│   │   └── TextChunker.py
│   └── mcp_server/
│       └── mcp_server.py           # 12 tools + 5 prompts, no prompt strings
├── models/               # SQLAlchemy models — one file per class
├── admin/                # SQLAdmin views — one file per view
└── main.py               # FastAPI app + SQLAdmin registration
config/
├── requirements/         # base.in, base.txt, dev.txt
└── settings/             # base.py (DATABASE_URL, API keys, constants)
alembic/versions/         # Database migrations
tests/                    # pytest suite — fully mocked, no real DB required
docs/                     # Implementation plan
```

---

## Environment variables

| Variable | Required | Description |
|---|---|---|
| `DATABASE_URL` | Yes | PostgreSQL connection string |
| `TAVILY_API_KEY` | No | Tavily job search (fallback — Claude web search is primary) |
| `GROQ_API_KEY` | No | Groq API key for server-side LLM utils |
| `SECRET_KEY` | No | App secret (for future auth) |
| `DEBUG` | No | Enable debug mode (default: False) |

---

## Cover letter quality rules

Every letter must pass:

- Zero em dashes or hyphens used as sentence dashes
- Zero buzzwords (dynamic, passionate, results-driven, leverage, synergy, etc.)
- Zero bullet points in the body
- Exactly 4 paragraphs, under 400 words
- Names the company and exact role in paragraph 1
- Two specific achievements with real numbers in paragraph 2
- Enforced deterministically by `CoverLetterUtils.clean_cover_letter()` after every generation
