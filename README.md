# VexaAI RAG Chat PDF

React frontend and FastAPI backend for uploading PDF documents and chatting with them through a RAG-style workflow.

## Current Architecture

The repository is intentionally scoped to two application surfaces:

- `frontend/`: Next.js 14 + TypeScript client
- `backend/`: FastAPI API, auth, document processing, and chat services

The repository now presents as a single frontend experience backed by one API.

## Stack

- Frontend: Next.js 14, React 18, TypeScript, Tailwind CSS
- Backend: FastAPI, Pydantic Settings, Supabase, JWT auth, PyMuPDF
- Infra: Render for API deployment, Vercel-ready frontend

## Repository Layout

```text
.
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── middleware/
│   │   ├── services/
│   │   ├── utils/
│   │   ├── config.py
│   │   ├── database.py
│   │   └── models.py
│   ├── .env.example
│   ├── main.py
│   ├── render.yaml
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   ├── components/
│   │   ├── lib/
│   │   └── types/
│   ├── .env.local.example
│   └── package.json
├── docs/
└── infrastructure/
```

## Local Development

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --reload
```

The API starts on `http://localhost:8000`.

### Frontend

```bash
cd frontend
npm install
cp .env.local.example .env.local
npm run dev
```

The UI starts on `http://localhost:3000`.

## Environment Files

- Backend template: `backend/.env.example`
- Frontend template: `frontend/.env.local.example`

Do not commit populated `.env` files or runtime artifacts.

## Deployment Notes

- `backend/render.yaml` contains the Render service definition
- `frontend/vercel.json` contains the frontend deployment settings

## What Was Cleaned Up

- Removed the legacy prototype UI and its tests
- Trimmed backend dependencies to the active API stack
- Updated docs to reflect the actual frontend/backend architecture
- Ignored generated logs, exports, caches, and local frontend build output
