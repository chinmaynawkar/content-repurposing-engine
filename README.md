# Content Repurposing Engine

An AI-powered web application that turns **one piece of long-form content** (blog, transcript, article) into multiple platform-ready formats: LinkedIn posts, Twitter threads, Instagram captions, SEO meta descriptions, and thumbnail text suggestions.

## Problem

Content creators spend 60%+ of their time on repetitive reformatting. This project automates that workflow—one upload, multiple outputs—so creators can focus on ideation and engagement.

## What It Does

| Input                       | Output                                                                            |
| --------------------------- | --------------------------------------------------------------------------------- |
| Blog / transcript / article | 3 LinkedIn posts, 5 Twitter threads, Instagram captions, SEO meta, thumbnail text |

## Tech Stack

| Layer    | Technology                                                     |
| -------- | -------------------------------------------------------------- |
| Backend  | FastAPI (Python 3.11+)                                         |
| Frontend | React 18 + TypeScript + Vite                                   |
| Database | PostgreSQL (Supabase)                                          |
| AI       | Gemini 2.5 Flash, Groq (Llama 3.3), Pollinations.ai (optional) |

All APIs use **free tiers**—no credit card required.

## Project Structure

```
the-content-hub/
├── backend/           # FastAPI
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── routers/
│   │   └── services/
│   ├── requirements.txt
│   └── .env
├── frontend/          # React + Vite + TypeScript
├── .github/workflows/ # CI (ci.yml)
├── memory-bank/
├── md-docs/
└── README.md
```

## Branch strategy and CI

- **`dev`**: Active development. CI runs on every push to `dev`.
- **`main`**: Production-ready. Merges only via pull request after CI passes.

**CI checks** (see [.github/workflows/ci.yml](.github/workflows/ci.yml)):

| Check            | What runs |
|------------------|-----------|
| backend-tests    | Python 3.11, PostgreSQL service, schema apply, `pytest tests/ -v` |
| frontend-build   | Node 20, `npm ci`, `npm run build` (tsc + vite build) |
| frontend-lint    | Node 20, `npm ci`, `npm run lint` (eslint) |

**Run the same checks locally:**

```bash
# Backend (requires local Postgres or DATABASE_URL to Supabase)
cd backend && pip install -r requirements-dev.txt && pytest tests/ -v

# Frontend
cd frontend && npm ci && npm run build && npm run lint
```

**Branch protection:** In GitHub → Settings → Branches → Add rule for `main`, require a pull request and require status checks `backend-tests`, `frontend-build`, and `frontend-lint` to pass before merging. See [md-docs/ci-pipeline.md](md-docs/ci-pipeline.md) for details.

## Prerequisites

- Python 3.11+
- Node.js 18+ (for frontend)
- Supabase, Gemini, Groq accounts (free)

## Getting Started

### Backend

1. Clone and enter the project:

   ```bash
   cd the-content-hub
   ```

2. Create and activate the virtual environment:

   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate   # Mac/Linux
   # venv\Scripts\activate   # Windows
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Configure environment variables. Create `backend/.env`:

   ```
   DATABASE_URL=postgresql://postgres:PASSWORD@db.PROJECT.supabase.co:5432/postgres
   GEMINI_API_KEY=AIza...
   GROQ_API_KEY=gsk_...
   ENVIRONMENT=development
   DEBUG=True
   ```

5. Run the API:

   ```bash
   uvicorn app.main:app --reload
   ```

6. Open:
   - API: http://127.0.0.1:8000
   - Health: http://127.0.0.1:8000/health
   - Docs: http://127.0.0.1:8000/docs

### Frontend

Coming soon.

## Environment Variables

| Variable         | Description                                                |
| ---------------- | ---------------------------------------------------------- |
| `DATABASE_URL`   | Supabase PostgreSQL connection string                      |
| `GEMINI_API_KEY` | Google AI Studio API key                                   |
| `GROQ_API_KEY`   | Groq Console API key                                       |
| `LOG_LEVEL`      | DEBUG, INFO, WARNING, ERROR (default: INFO)                 |
| `ENVIRONMENT`    | development or production (affects log format: console/JSON)|

## Current Status

- [x] Backend structure, health endpoint
- [ ] Frontend (React + Vite + TS)
- [ ] Supabase tables (users, content, generated_posts)
- [ ] Content upload & AI generation endpoints
- [ ] Content library & analytics

## Docs

- [FastAPI Tutorial](https://fastapi.tiangolo.com/tutorial/)
- [Supabase](https://supabase.com/docs)
