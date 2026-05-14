# Chatbot Platform — Full System Design
**Date:** 2026-05-15
**Sub-projects:** 3–6 of 7 (Auth, RAG, Chat API, Admin Dashboard)
**Status:** Approved — ready for implementation

---

## Context

Extends the existing Knowledge Base Ingestion service (sub-project 2). Same FastAPI monolith, same Docker Compose stack. Adding JWT auth, RAG engine, Chat API, and a React admin/chat frontend.

---

## Architecture

Single FastAPI monolith. All new routers added to the existing app. One `docker-compose up` starts everything.

**Services (Docker):** postgres, qdrant, minio, app (FastAPI), ollama (LLM)

**LLM:** Ollama with `llama3.2` (3B model, CPU-compatible, ~4GB RAM)

---

## Sub-project 3 — Auth / Multi-tenancy

### New Tables
```sql
CREATE TABLE tenants (
    tenant_id   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name        TEXT NOT NULL,
    slug        TEXT NOT NULL UNIQUE,
    created_at  TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE users (
    user_id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES tenants(tenant_id),
    email           TEXT NOT NULL UNIQUE,
    hashed_password TEXT NOT NULL,
    role            TEXT NOT NULL DEFAULT 'user',  -- 'admin' | 'user'
    created_at      TIMESTAMPTZ DEFAULT now()
);
```

### JWT
- Library: `python-jose[cryptography]` + `passlib[bcrypt]`
- Payload: `{ user_id, tenant_id, role, exp }`
- `ACCESS_TOKEN_EXPIRE_MINUTES=60`
- `JWT_SECRET_KEY` from env

### Routes
- `POST /api/v1/auth/register` — create user + tenant (open for prototype)
- `POST /api/v1/auth/login` — returns `{ access_token, token_type }`
- `GET  /api/v1/tenants` — list tenants (admin only)
- `POST /api/v1/tenants` — create tenant (admin only)

### Middleware
`get_current_user` FastAPI dependency extracts `tenant_id` and `user_id` from JWT. Replaces the current trusted `X-Tenant-ID` header on all existing routes.

---

## Sub-project 4 — RAG Engine

### Module: `app/rag.py`
No new routes — called internally by the Chat API.

**Flow:**
1. Embed query with existing `EmbeddingService`
2. `VectorStoreClient.search(tenant_id, query_vector, top_k=5)`
3. Build prompt: system instructions + retrieved chunk texts + user question
4. Stream response from Ollama: `POST http://ollama:11434/api/chat`
5. Yield tokens as SSE events

### Ollama Docker Service
```yaml
ollama:
  image: ollama/ollama:latest
  ports: ["11434:11434"]
  volumes: [ollama_data:/root/.ollama]
```

Model pulled once: `docker compose exec ollama ollama pull llama3.2`

---

## Sub-project 5 — Chat API

### New Tables
```sql
CREATE TABLE conversations (
    conversation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL,
    user_id         UUID NOT NULL REFERENCES users(user_id),
    title           TEXT NOT NULL DEFAULT 'New conversation',
    created_at      TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE messages (
    message_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(conversation_id) ON DELETE CASCADE,
    role            TEXT NOT NULL,  -- 'user' | 'assistant'
    content         TEXT NOT NULL,
    created_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_messages_conversation ON messages (conversation_id);
CREATE INDEX idx_conversations_user ON conversations (user_id);
```

### Routes
- `POST /api/v1/conversations` — create conversation
- `GET  /api/v1/conversations` — list user's conversations
- `DELETE /api/v1/conversations/{id}` — delete conversation + messages
- `GET  /api/v1/conversations/{id}/messages` — fetch message history
- `POST /api/v1/conversations/{id}/messages` — send message; returns **streaming SSE**

### Message flow
1. Save user message to DB
2. Fetch last 10 messages for context
3. Call `rag.stream_answer(tenant_id, query, history)` → yields tokens
4. Stream tokens as `text/event-stream`
5. Accumulate full response, save assistant message to DB after stream ends

---

## Sub-project 6 — Admin Dashboard (Frontend)

**Stack:** React 18 + Vite + TailwindCSS

**Location:** `frontend/` directory. Dev: `npm run dev` (port 5173). Production: built to `frontend/dist/`, served by FastAPI `StaticFiles`.

### Views
- `/login` — email + password form, stores JWT in localStorage
- `/admin` — tenant list, source list per tenant, upload document (calls POST /api/v1/sources), delete source
- `/chat` — conversation list sidebar, chat window with streaming message display

### Auth
All API calls include `Authorization: Bearer <token>`. Redirect to `/login` on 401.

---

## Updated `.env` keys
```
JWT_SECRET_KEY=changeme-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=60
OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_MODEL=llama3.2
```

---

## Migration file: `migrations/002_auth_chat.sql`
Adds `tenants`, `users`, `conversations`, `messages` tables.

---

## Implementation Order
1. Auth (tenants, users, JWT) — everything depends on this
2. RAG engine module
3. Chat API routes
4. Frontend (React + Vite)
5. Docker Compose updates (Ollama service, env vars)
