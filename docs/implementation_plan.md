# AutoApply — Implementation Plan

**Author:** Zahra Yasin
**Version:** 5.0 (updated June 2026)
**Stack:** FastAPI · PostgreSQL + pgvector · sentence-transformers · Claude Desktop (MCP) · Tavily API · Groq (server-side LLM utils)

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Architecture: Claude Desktop as Intelligence Layer](#2-architecture-claude-desktop-as-intelligence-layer)
3. [Tech Stack](#3-tech-stack)
4. [Project Structure](#4-project-structure)
5. [Database Schema](#5-database-schema)
6. [Prompts Folder — All AI Behaviour Lives Here](#6-prompts-folder--all-ai-behaviour-lives-here)
7. [MCP Server — Tools](#7-mcp-server--tools)
8. [RAG Memory Layer](#8-rag-memory-layer)
9. [Job Search Strategy](#9-job-search-strategy)
10. [Admin Panel](#10-admin-panel)
11. [Conversation Flow](#11-conversation-flow)
12. [Cover Letter Rules](#12-cover-letter-rules)
13. [Environment Variables](#13-environment-variables)
14. [Running the System](#14-running-the-system)
15. [Tests](#15-tests)
16. [What Is Complete](#16-what-is-complete)
17. [Remaining Work](#17-remaining-work)

---

## 1. Project Overview

AutoApply is an autonomous AI job application system. Given a resume and preferences, it:

1. Finds real job postings via web search
2. Scores each job for fit against the user's resume (Claude)
3. Writes tailored, human-sounding cover letters (Claude)
4. Critiques and revises its own letters until they pass a strict checklist (Claude)
5. Stores every approved letter as an embedding — future letters improve over time (RAG)

**Core differentiator:** Claude Desktop is the primary intelligence layer via MCP. The Python backend fetches and stores data — Claude does all reasoning, scoring, writing, and reviewing. The system learns from every approved cover letter via pgvector RAG.

The backend also contains Groq-powered util classes (`CoverLetterUtils`, `FitScorerUtils`, `CriticUtils`) that implement the same pipeline server-side — kept as a reference implementation and potential REST API backend.

---

## 2. Architecture: Claude Desktop as Intelligence Layer

```
User ──► Claude Desktop chat
              │
              ├── reads: AGENT_INSTRUCTIONS (system-level, always active)
              │          from autoapply/ai/prompts/agent_instructions.py
              │
              ├── reads: MCP prompts (greet_user, profile_creation, resume_uploaded,
              │          run_pipeline, improve_cover_letter)
              │          from autoapply/ai/prompts/*.py
              │
              └── calls: MCP tools (create_user, upload_resume_text, search_jobs,
                         store_job_manually, get_fit_context, save_fit_score_tool,
                         get_cover_letter_context_tool, save_cover_letter_tool,
                         save_critic_review_tool, get_application_status,
                         retrieve_past_memory)
                              │
                              └── reads/writes: PostgreSQL + pgvector
```

**Key principle:** MCP tools are pure data I/O. Claude does all scoring, writing, and reviewing itself. No LLM calls happen inside the MCP tool handlers.

---

## 3. Tech Stack

| Component | Choice | Notes |
|---|---|---|
| Web framework | FastAPI | Admin panel mount + `/health` endpoint |
| Primary intelligence | Claude Desktop via MCP | All LLM reasoning in the MCP flow |
| MCP SDK | FastMCP (`mcp` package) | Exposes tools + prompts to Claude Desktop |
| Server-side LLM | Groq `llama-3.3-70b-versatile` via `langchain-groq` | Used in util classes (`CoverLetterUtils`, `FitScorerUtils`, `CriticUtils`) |
| Job discovery | Claude's built-in web search | Primary. Finds real postings on greenhouse.io, lever.co, arc.dev etc. |
| Job search fallback | Tavily API | Secondary. Filters out job board listing pages. |
| Embeddings | `sentence-transformers` `all-MiniLM-L6-v2` | Local, 384 dims, no API key, singleton pattern |
| Database | PostgreSQL 16 + pgvector | Single DB for relational + vector storage |
| ORM | SQLAlchemy 2.0 (sync) | Mapped columns, relationships |
| Migrations | Alembic | `pgvector.sqlalchemy` import required in migration |
| Admin panel | SQLAdmin | Auto CRUD at `/admin` — explicit `column_details_list` on every view |
| Settings | python-decouple | `.env` file, no hardcoded secrets |
| PDF parsing | pypdf | Resume text extraction |
| Chunking | custom `chunk_text()` in `TextChunker.py` | 500 char chunks, 50 char overlap |

---

## 4. Project Structure

```
AutoApply/
├── .env
├── alembic.ini
│
├── config/
│   └── settings/
│       └── base.py              # DATABASE_URL, TAVILY_API_KEY, GROQ_API_KEY,
│                                # EMBEDDING_MODEL, MEMORY_TOP_K, CRITIC_MAX_REVISIONS etc.
│
├── autoapply/
│   ├── main.py                  # FastAPI app + SQLAdmin registration + /health
│   ├── database.py              # SQLAlchemy engine + SessionLocal + check_db_connection()
│   │
│   ├── models/                  # One file per class, CamelCase filenames
│   │   ├── __init__.py          # Imports all models so SQLAlchemy resolves relationships
│   │   ├── Base.py              # Base, TimeStampedModel (id, created_at, updated_at)
│   │   ├── User.py
│   │   ├── Resume.py
│   │   ├── ResumeChunk.py
│   │   ├── SearchPreference.py
│   │   ├── Job.py
│   │   ├── JobChunk.py
│   │   ├── Application.py
│   │   ├── CoverLetter.py
│   │   ├── CriticReview.py
│   │   ├── ApplicationOutcome.py
│   │   ├── Feedback.py
│   │   └── MemoryEntry.py
│   │
│   ├── admin/                   # One file per SQLAdmin view, CamelCase filenames
│   │   ├── __init__.py
│   │   ├── UserAdmin.py
│   │   ├── ResumeAdmin.py
│   │   ├── SearchPreferenceAdmin.py
│   │   ├── JobAdmin.py
│   │   ├── ApplicationAdmin.py
│   │   ├── CoverLetterAdmin.py
│   │   ├── CriticReviewAdmin.py
│   │   ├── ApplicationOutcomeAdmin.py
│   │   ├── FeedbackAdmin.py
│   │   └── MemoryEntryAdmin.py
│   │
│   └── ai/
│       ├── prompts/             # ALL AI behaviour lives here — nothing in mcp_server.py
│       │   ├── __init__.py      # exports all constants
│       │   ├── agent_instructions.py  # AGENT_INSTRUCTIONS — onboarding, pipeline,
│       │   │                          # cover letter rules, general rules
│       │   ├── greet_user.py          # GREET_PROMPT
│       │   ├── profile_creation.py    # PROFILE_CREATED_PROMPT
│       │   ├── resume_uploaded.py     # RESUME_UPLOADED_PROMPT
│       │   ├── run_pipeline.py        # PIPELINE_PROMPT — full pipeline steps
│       │   ├── improve_cover_letter.py# IMPROVE_PROMPT — refine a cover letter
│       │   ├── cover_letter.py        # COVER_LETTER_PROMPT — server-side LLM generation
│       │   ├── fit_score.py           # FIT_PROMPT — server-side fit scoring
│       │   └── critic.py              # CRITIC_PROMPT, REVISION_PROMPT — server-side critic
│       │
│       ├── utils/               # Static-method classes for all backend logic
│       │   ├── __init__.py
│       │   ├── Embedder.py      # Embedder.embed_text(), embed_texts() — singleton model
│       │   ├── TextChunker.py   # chunk_text() — 500 char chunks, 50 char overlap
│       │   ├── ResumeUtils.py   # extract_text_from_pdf(), ingest_resume(), ingest_resume_from_text()
│       │   ├── JobSearchUtils.py# search_and_store_jobs(), store_job_from_text()
│       │   │                    # Filters job board domains, urlparse for URL parsing
│       │   ├── ContextUtils.py  # get_fit_context(), get_cover_letter_context()
│       │   │                    # Both use pgvector cosine search for relevant chunks
│       │   ├── FitScorerUtils.py# score_job_fit() — Groq LLM, returns Job with scores set
│       │   ├── CoverLetterUtils.py # generate_cover_letter(), clean_cover_letter()
│       │   │                       # clean_cover_letter() strips em dashes, bullets, double commas
│       │   ├── CriticUtils.py   # critique_and_revise() — Groq LLM, loops up to CRITIC_MAX_REVISIONS
│       │   ├── SaveUtils.py     # save_fit_score(), save_cover_letter(), save_critic_review()
│       │   │                    # save_critic_review auto-stores to RAG on APPROVE
│       │   └── MemoryUtils.py   # store_memory(), retrieve_memory(), store_approved_cover_letter()
│       │
│       └── mcp_server/
│           ├── mcp_server.py          # FastMCP server — 5 prompts + 12 tools
│           │                          # No prompt strings here — imports from ai/prompts/
│           └── mcp_server_client.py   # Lists available tools and prompts (no smoke test code)
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py              # Shared fixtures: mock_db, sample_user/job/resume/application/cover_letter
│   ├── test_TextChunker.py
│   ├── test_Embedder.py
│   ├── test_JobSearchUtils.py
│   ├── test_ContextUtils.py
│   ├── test_ResumeUtils.py
│   ├── test_FitScorerUtils.py
│   ├── test_CoverLetterUtils.py
│   ├── test_CriticUtils.py
│   ├── test_SaveUtils.py
│   └── test_MemoryUtils.py
│
├── alembic/
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│       └── 90ccc1235d52_initial_schema.py
│
└── docs/
    └── implementation_plan.md
```

### Key structural rules

- **One file per model, CamelCase filename** — matches class name exactly (`Job.py` contains only `Job`).
- **One file per admin view, CamelCase filename** — `JobAdmin.py` contains only `JobAdmin`.
- **All utils are static-method classes** — no standalone module-level functions (except `chunk_text` in `TextChunker.py`).
- **All AI behaviour (instructions, prompts, rules) lives in `autoapply/ai/prompts/`** — `mcp_server.py` contains no prompt strings.
- **All LLM prompt strings live in `autoapply/ai/prompts/`** — utils import them, never define them inline.

---

## 5. Database Schema

All models inherit `TimeStampedModel` → UUID PK, `created_at`, `updated_at`.

### USER
```
id       UUID PK
name     VARCHAR(255)
email    VARCHAR(255) UNIQUE NOT NULL
```

### RESUME
```
id          UUID PK
user_id     UUID FK → users.id CASCADE   UNIQUE (one resume per user)
file_path   VARCHAR(500)    # set if PDF uploaded from disk; NULL for chat uploads
raw_text    TEXT            # full extracted text
```

### RESUME_CHUNK
```
id          UUID PK
resume_id   UUID FK → resumes.id CASCADE
chunk_text  TEXT NOT NULL
embedding   VECTOR(384)     # sentence-transformers all-MiniLM-L6-v2
chunk_index INTEGER NOT NULL
```
Not shown in admin — debug via parent Resume.

### SEARCH_PREFERENCE
```
id                  UUID PK
user_id             UUID FK → users.id CASCADE
target_role         VARCHAR(255)
location            VARCHAR(255)
seniority_level     VARCHAR(50)
excluded_companies  TEXT
keywords            TEXT
```

### JOB
```
id              UUID PK
title           VARCHAR(255) NOT NULL
company         VARCHAR(255) NOT NULL
url             VARCHAR(1000) UNIQUE NOT NULL   # manual jobs use manual://<uuid> prefix
description     TEXT
fit_score       FLOAT           # 0–100, set by Claude
recommendation  VARCHAR(10)     # APPLY or SKIP
fit_reasoning   TEXT
scraped_at      TIMESTAMP
```

### JOB_CHUNK
```
id          UUID PK
job_id      UUID FK → jobs.id CASCADE
chunk_text  TEXT NOT NULL
embedding   VECTOR(384)
chunk_index INTEGER NOT NULL
```
Not shown in admin.

### APPLICATION
```
id          UUID PK
user_id     UUID FK → users.id CASCADE
job_id      UUID FK → jobs.id CASCADE
status      VARCHAR(20)    # draft / ready / needs_review / applied / interview / rejected / offer
applied_at  TIMESTAMP
UNIQUE (user_id, job_id)
```

### COVER_LETTER
```
id                UUID PK
application_id    UUID FK → applications.id CASCADE   UNIQUE
draft_text        TEXT       # initial draft
final_text        TEXT       # set on APPROVE (may equal draft if no revision needed)
resume_bullets    TEXT       # resume excerpts used during generation
revision_count    INTEGER DEFAULT 0
critic_approved   BOOLEAN DEFAULT FALSE
generated_at      TIMESTAMP
```

### CRITIC_REVIEW
```
id                UUID PK
application_id    UUID FK → applications.id CASCADE
verdict           VARCHAR(10)    # APPROVE or REVISE
feedback_text     TEXT
attempt_number    INTEGER NOT NULL
reviewed_at       TIMESTAMP
```

### APPLICATION_OUTCOME
```
id                UUID PK
application_id    UUID FK → applications.id CASCADE   UNIQUE
outcome           VARCHAR(20)    # applied / interview / rejected / offer
outcome_date      TIMESTAMP
notes             TEXT
```

### FEEDBACK
```
id                UUID PK
application_id    UUID FK → applications.id CASCADE
rating            VARCHAR(10)    # good / needs_work
comment           TEXT
```

### MEMORY_ENTRY
```
id              UUID PK
user_id         UUID FK → users.id CASCADE
entry_type      VARCHAR(50)    # approved_cover_letter
content         TEXT NOT NULL
embedding       VECTOR(384)
source_outcome  VARCHAR(20)    # approved
stored_at       TIMESTAMP
```

---

## 6. Prompts Folder — All AI Behaviour Lives Here

`autoapply/ai/prompts/` is the single source of truth for everything Claude thinks and does, and for every LLM prompt string used server-side.

### MCP prompts (Claude Desktop flow)

| File | Constant | Used by |
|---|---|---|
| `agent_instructions.py` | `AGENT_INSTRUCTIONS` | FastMCP `instructions` — always active |
| `greet_user.py` | `GREET_PROMPT` | `greet_user` MCP prompt |
| `profile_creation.py` | `PROFILE_CREATED_PROMPT` | `profile_created` MCP prompt |
| `resume_uploaded.py` | `RESUME_UPLOADED_PROMPT` | `resume_uploaded` MCP prompt |
| `run_pipeline.py` | `PIPELINE_PROMPT` | `run_pipeline` MCP prompt |
| `improve_cover_letter.py` | `IMPROVE_PROMPT` | `improve_cover_letter` MCP prompt |

### Server-side LLM prompts (Groq utils flow)

| File | Constant(s) | Used by |
|---|---|---|
| `cover_letter.py` | `COVER_LETTER_PROMPT` | `CoverLetterUtils.generate_cover_letter()` |
| `fit_score.py` | `FIT_PROMPT` | `FitScorerUtils.score_job_fit()` |
| `critic.py` | `CRITIC_PROMPT`, `REVISION_PROMPT` | `CriticUtils.critique_and_revise()` |

`__init__.py` exports all 9 constants.

---

## 7. MCP Server — Tools

**File:** `autoapply/ai/mcp_server/mcp_server.py`

Contains only tool registrations and prompt wrappers. No prompt strings. Imports everything from `autoapply.ai.prompts`.

### 5 Prompts

| Prompt | Parameters | Purpose |
|---|---|---|
| `greet_user` | `user_name` | First contact — intro + ask for email |
| `profile_created` | `user_name, email` | After email shared — create user + ask for resume |
| `resume_uploaded` | `user_name, user_id` | After PDF upload — process + collect preferences |
| `run_pipeline` | `user_name, user_id, target_role, location, keywords, seniority` | Full pipeline |
| `improve_cover_letter` | `application_id, feedback` | Refine a specific letter |

### 12 Tools

| Tool | Purpose |
|---|---|
| `create_user(name, email)` | Create user or return existing by email |
| `upload_resume(user_id, file_path)` | Ingest PDF from local file path |
| `upload_resume_text(user_id, resume_text)` | Ingest resume from raw text (chat upload) |
| `search_jobs(user_id, target_role, location, keywords, seniority, max_results)` | Tavily search — fallback; seniority included in query strings |
| `store_job_manually(title, company, description, url)` | Store any job from web search or user paste |
| `get_fit_context(user_id, job_id)` | Resume excerpts + job description for Claude to score |
| `save_fit_score_tool(job_id, fit_score, recommendation, reasoning)` | Persist Claude's score |
| `get_cover_letter_context_tool(user_id, job_id)` | Resume + job + RAG memory for Claude to write |
| `save_cover_letter_tool(user_id, job_id, cover_letter_text)` | Save Claude's draft |
| `save_critic_review_tool(application_id, verdict, feedback, revised_text)` | Save verdict; auto-stores to RAG on APPROVE |
| `get_application_status(application_id)` | Full application + cover letter state |
| `retrieve_past_memory(user_id, query, entry_type, top_k)` | Semantic search over memory |

---

## 8. RAG Memory Layer

### Write path

On `save_critic_review_tool` with `verdict=APPROVE`:
```
cover_letter.final_text = approved text
cover_letter.critic_approved = True
application.status = "ready"
MemoryUtils.store_memory(
    user_id=...,
    entry_type="approved_cover_letter",
    content="Approved cover letter for [title] at [company]:\n\n[final_text]",
    source_outcome="approved"
)
  → Embedder.embed_text(content)   # sentence-transformers, 384 dims
  → INSERT INTO memory_entries
```

### Read path — resume chunks (fit scoring + cover letter writing)

`get_fit_context` and `get_cover_letter_context_tool` both retrieve the most relevant resume sections for the job:

```sql
SELECT chunk_text
FROM resume_chunks
WHERE resume_id = :resume_id
ORDER BY embedding <=> CAST(:embedding AS vector)   -- cosine similarity
LIMIT 3
```

Query embedding = job description text. Returns the 3 resume chunks most relevant to that specific job.

### Read path — past approved letters (cover letter writing)

`get_cover_letter_context_tool` also retrieves past letters as style reference:

```sql
SELECT content
FROM memory_entries
WHERE user_id = :user_id AND entry_type = 'approved_cover_letter'
ORDER BY embedding <=> CAST(:embedding AS vector)
LIMIT 2
```

### Embedding model
```
Model:      all-MiniLM-L6-v2 (sentence-transformers, local)
Dimensions: 384
Operator:   <=> (cosine similarity, pgvector)
Top-K:      3 (MEMORY_TOP_K in settings)
Singleton:  model loaded once at module level in Embedder.py — not per request
Isolation:  every query filters by user_id
```

---

## 9. Job Search Strategy

### Primary — Claude's built-in web search

`AGENT_INSTRUCTIONS` and `PIPELINE_PROMPT` instruct Claude to use its own web search to find 5 specific, real job postings before calling any tools. The search query includes seniority level:

```
"{seniority} {target_role} {location} site:greenhouse.io OR site:lever.co"
e.g. "senior machine learning engineer remote site:greenhouse.io"
```

For each posting found, Claude calls `store_job_manually(title, company, description, url)`.

### Secondary — Tavily API (`search_jobs` tool)

- `search_depth="advanced"` for more content per result
- `seniority` prepended to role in all query strings
- Year dynamically set via `datetime.now().year`
- `_JOB_BOARD_DOMAINS` class attribute on `JobSearchUtils` — results from linkedin, indeed, glassdoor, turing, dice etc. are skipped
- URL domain extraction via `urllib.parse.urlparse` (no regex)
- Company name parser avoids returning job board names as company

If Tavily returns 0 results, the tool returns a message telling Claude to fall back to web search + `store_job_manually`.

---

## 10. Admin Panel

**URL:** `http://localhost:8000/admin`

Every view uses explicit `column_details_list` — required because SQLAdmin's default detail view loads all relationships, which pulls in `VECTOR(384)` columns that cannot be serialized, causing 500 errors.

| View | Notes |
|---|---|
| Users | id, name, email, created_at |
| Resumes | List: metadata only. Detail: shows `raw_text` (first 2000 chars). `file_path` shows "(uploaded via chat)" when null. |
| Search Preferences | role, location, seniority, keywords |
| Jobs | title, company, fit_score, recommendation. Detail includes description and fit_reasoning. |
| Applications | user_id, job_id, status, applied_at |
| Cover Letters | application_id, revision_count, critic_approved. Detail shows draft_text and final_text. |
| Critic Reviews | verdict, attempt_number. Detail shows feedback_text. |
| Application Outcomes | outcome, outcome_date, notes |
| Feedback | rating, comment |
| Memory Entries | entry_type, source_outcome, stored_at. Detail shows content. |

`ResumeChunk` and `JobChunk` not exposed — vector data has no human-readable purpose in admin.

No authentication for portfolio build. Add `sqladmin`'s `AuthenticationBackend` before public deployment.

---

## 11. Conversation Flow

```
User:  "Hi, I'm Zahra Yasin"
       ↓
Claude: [AGENT_INSTRUCTIONS active]
        "Hi Zahra! I'm AutoApply...
         To set up your profile, what is your email address?"
        [does NOT call create_user yet — no email yet]

User:  "zahrayasin2209@gmail.com"
       ↓
Claude: calls create_user(name="Zahra Yasin", email="zahrayasin2209@gmail.com")
        • New user  → "Profile set! Please upload your resume PDF using the + button."
        • Returning → "Welcome back, Zahra! Upload a new resume or jump to job search?"

User:  [uploads resume PDF]
       ↓
Claude: calls upload_resume_text(user_id=..., resume_text="[full PDF text]")
        Summarises profile: skills, experience, standout metrics, best-fit roles.
        "What role are you targeting? And where?"

User:  "Associate AI Engineer, remote, Python LangChain LangGraph"
       ↓
Claude: "Got it. What experience level are you targeting?
         junior, mid-level, senior, lead, or open to any?"

User:  "junior to mid-level"
       ↓
Claude: [PIPELINE]
        Uses web search: "junior associate AI engineer remote site:greenhouse.io"
        Finds 5 specific postings → calls store_job_manually(...) for each
        → for each job: get_fit_context → scores → save_fit_score_tool
        → shows fit summary table
        → for APPLY jobs: get_cover_letter_context_tool → writes letter → save_cover_letter_tool
        → critic review → save_critic_review_tool
        → shows approved letter, waits for confirmation

User:  "Can you make the opening stronger?"
       ↓
Claude: calls get_application_status → rewrites letter → save_critic_review_tool(verdict=REVISE)
        Shows updated letter.
```

---

## 12. Cover Letter Rules

Enforced in `AGENT_INSTRUCTIONS`, `PIPELINE_PROMPT`, `COVER_LETTER_PROMPT`, `CRITIC_PROMPT`, and `REVISION_PROMPT`. All five locations use the same ruleset.

### Language
- Natural human voice — sounds like the candidate wrote it
- **ZERO hyphens as dashes** — never `—` or `-` between two phrases or clauses
  - Wrong: `"I led the team — and cut latency by 40%"`
  - Right: `"I led the team and cut latency by 40%"`
  - (Compound adjectives like `production-ready` are fine)
- **ZERO buzzwords:** dynamic, passionate, results-driven, leverage, synergy, innovative, transformative, spearheaded, utilized, impactful, excited to
- ZERO bullet points in the body
- Vary sentence length
- First person active: "I built", "I led", "I reduced"

### Format
- Exactly 4 paragraphs, under 400 words
- No subject line, no date, no "Dear Hiring Manager" — start with first paragraph directly

### Structure
- **Para 1:** Hook naming company + exact role. Genuine interest. One sentence on background.
- **Para 2:** Two specific achievements from resume with numbers or outcomes.
- **Para 3:** What you bring to this specific team. Reference something real about the company.
- **Para 4:** Thank them. Eager to discuss. Clear call to action.

### Post-processing (`clean_cover_letter`)

`CoverLetterUtils.clean_cover_letter()` runs deterministically after every LLM generation:
- Converts em dashes to `, `
- Converts ` - ` to `, `
- Collapses double commas
- Strips leading bullet characters (`•`, `-`, `*`) from line starts
- Strips surrounding whitespace

### Self-check (Claude runs this before saving in MCP flow)
```
✗ Any em dash (—) or hyphen between phrases? → rewrite that sentence
✗ Any buzzword? → replace with a concrete specific statement
✗ Any bullet in body? → convert to a sentence
✗ Over 400 words? → trim
✗ Missing company or role name? → add it
```

---

## 13. Environment Variables

```env
# Database
DATABASE_URL=postgresql://autoapply:password@localhost:5432/autoapply_db

# Job Search (Tavily — secondary fallback)
TAVILY_API_KEY=tvly-...

# Server-side LLM (Groq — used in FitScorerUtils, CoverLetterUtils, CriticUtils)
GROQ_API_KEY=gsk_...

# App
SECRET_KEY=change-me-in-production
DEBUG=True
UPLOAD_DIR=./uploads
```

Both `TAVILY_API_KEY` and `GROQ_API_KEY` default to `""` — the server does not crash if either is missing. The Tavily tool returns early; Groq utils will raise at LLM call time.

---

## 14. Running the System

### Start PostgreSQL (Docker)
```bash
docker-compose up db
```

### Run migrations
```bash
venv\Scripts\python.exe -m alembic upgrade head
```

### Start FastAPI server
```bash
cd C:\Users\PMLS\Desktop\AutoApply
venv\Scripts\python.exe -m uvicorn autoapply.main:app --host 0.0.0.0 --port 8000
```

- Admin: `http://localhost:8000/admin`
- Health: `http://localhost:8000/health`

### Claude Desktop config
`%APPDATA%\Claude\claude_desktop_config.json` (edit while Claude Desktop is fully closed):
```json
{
  "mcpServers": {
    "autoapply": {
      "command": "C:\\Users\\PMLS\\Desktop\\AutoApply\\venv\\Scripts\\python.exe",
      "args": ["C:\\Users\\PMLS\\Desktop\\AutoApply\\autoapply\\ai\\mcp_server\\mcp_server.py"],
      "env": { "PYTHONPATH": "C:\\Users\\PMLS\\Desktop\\AutoApply" }
    }
  }
}
```

Restart Claude Desktop after any change to MCP server or prompts. Look for the hammer icon (🔨) in Claude Desktop to confirm the autoapply integration is connected.

### List available MCP tools
```bash
venv\Scripts\python.exe autoapply\ai\mcp_server\mcp_server_client.py
```

### Run tests
```bash
venv\Scripts\python.exe -m pytest tests/ -v
```

---

## 15. Tests

**Location:** `tests/`
**Framework:** pytest + `unittest.mock`

No real database required — all DB calls go through a `MagicMock` session fixture.

| File | What it covers |
|---|---|
| `conftest.py` | Shared fixtures: `mock_db`, `sample_user`, `sample_job`, `sample_resume`, `sample_application`, `sample_cover_letter` |
| `test_TextChunker.py` | Chunking logic — empty, short, long text, overlap correctness |
| `test_Embedder.py` | Singleton pattern, returns correct shape, model loaded once |
| `test_JobSearchUtils.py` | Domain extraction, job board detection, company parsing, query building, store new/existing job |
| `test_ContextUtils.py` | Fit context and cover letter context — expected keys, fallback to raw_text, raises on missing job/resume |
| `test_ResumeUtils.py` | PDF extraction (None pages), `ingest_resume`, `ingest_resume_from_text` — creates/updates records |
| `test_FitScorerUtils.py` | Mocked Groq LLM — happy path sets job attributes, raises on missing job/resume, raises on bad JSON |
| `test_CoverLetterUtils.py` | `clean_cover_letter` deterministic cases (em dash, bullet, double comma, compound adjective), `generate_cover_letter` creates DB records and applies post-processing |
| `test_CriticUtils.py` | Approve on first attempt, REVISE→APPROVE cycle, raises on missing application/cover letter, stops after max revisions |
| `test_SaveUtils.py` | `save_fit_score`, `save_cover_letter`, `save_critic_review` APPROVE/REVISE paths, missing entity raises |
| `test_MemoryUtils.py` | `store_memory`, `retrieve_memory` with/without type filter, `store_approved_cover_letter` returns None when missing/not approved |

---

## 16. What Is Complete

### Core pipeline (MCP / Claude Desktop)
- [x] Onboarding: greet → email → create_user → returning user detection → resume upload
- [x] Experience level collection — Claude asks after role/location, before pipeline starts
- [x] Job discovery via Claude's built-in web search with seniority in query
- [x] `store_job_manually` — stores any posting found via web search or user paste
- [x] Tavily fallback (`search_jobs`) with seniority, current year, job board domain filter
- [x] Fit scoring — `get_fit_context` → Claude scores → `save_fit_score_tool`
- [x] Cover letter writing — `get_cover_letter_context_tool` → Claude writes → self-check → `save_cover_letter_tool`
- [x] Critic review — Claude reviews → `save_critic_review_tool` → auto-stores to RAG on APPROVE
- [x] RAG memory — approved letters embedded and retrieved for future sessions

### Code quality
- [x] One model file per class, CamelCase filenames
- [x] All utils converted to static-method classes in `ai/utils/`
- [x] All LLM prompt strings moved to `ai/prompts/`
- [x] All variable names descriptive across all files
- [x] URL parsing via `urlparse`, no regex in `JobSearchUtils`
- [x] `_JOB_BOARD_DOMAINS` moved inside `JobSearchUtils` class as class attribute
- [x] Dead code removed (`_BUZZWORD_PATTERN`, smoke test code)
- [x] Prompt files renamed descriptively (`greet_user.py`, `run_pipeline.py`, etc.)

### Cover letter quality
- [x] Zero hyphens as dashes rule — enforced in all 5 prompt locations
- [x] Zero buzzwords list — enforced in all 5 prompt locations
- [x] `clean_cover_letter()` post-processor runs after every generation
- [x] Mandatory self-check in MCP flow before saving

### Admin panel
- [x] All 10 ModelViews with explicit `column_details_list`
- [x] Resume `raw_text` shown in detail view
- [x] `file_path` shows "(uploaded via chat)" when null

### Tests
- [x] `conftest.py` + 10 test files covering all util classes
- [x] No real DB required — fully mocked with `unittest.mock`

---

## 17. Remaining Work

### High priority
- [ ] **Outcome feedback loop** — store interview/offer outcomes to memory so letters that led to interviews are prioritized in RAG retrieval
- [ ] **Resume update flow** — delete old chunks and re-embed when user uploads a new resume (currently old chunks stay)

### Medium priority
- [ ] **ivfflat index** on `memory_entries.embedding` and `resume_chunks.embedding` — needed for performance once memory grows past ~1000 entries
- [ ] **Pass seniority to `run_pipeline` prompt** — Claude collects it in conversation but must be passed explicitly when calling the MCP prompt

### Low priority
- [ ] `Makefile` — `make run`, `make migrate`, `make test`
- [ ] `README.md` with setup instructions and architecture diagram
- [ ] SQLAdmin authentication before any public deployment
- [ ] `.env.example` file

---

*End of Implementation Plan — v5.0 (updated June 2026)*
