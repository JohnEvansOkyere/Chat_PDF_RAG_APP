# Frontend

Next.js 14 frontend for the VexaAI PDF chat product.

## Commands

```bash
npm install
cp .env.local.example .env.local
npm run dev
```

The app runs on `http://localhost:3000`.

## Required Environment Variables

```env
NEXT_PUBLIC_SUPABASE_URL=https://your-project-id.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
BACKEND_API_URL=http://localhost:8000/api
```

## Structure

```text
src/
├── app/
├── components/
├── lib/
└── types/
```

## Notes

- The frontend expects the FastAPI backend to be running
- Authentication and document actions are performed through the API
- Browser requests are routed through Next.js `/api` rewrites instead of exposing the backend base URL in client code
- Deployment configuration lives in `vercel.json`
