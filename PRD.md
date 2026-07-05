# Product Requirements Document
## Minimalist Movie Recommendation System

**Version:** 1.0  
**Status:** Draft  
**Target:** Desktop application (Windows / macOS / Linux)

---

## Overview

### Purpose
A lightweight desktop application that lets users browse movies, save favorites, view trending statistics, and chat with an AI movie advisor. The product is intentionally minimal—enough features to demonstrate a clean, pattern-driven architecture rather than a full streaming platform.

### Goals
- Deliver a working desktop client with five core user flows: auth, browse, favorites, chart, and AI chat.
- Satisfy explicit architectural constraints (Microfrontends, MVP, MVC, CQRS, Event Sourcing, API Gateway, RAG).
- Keep scope small: no social features, no payment, no offline sync beyond local caching.

### Non-Goals
- Multi-user collaboration or sharing.
- Full-text search across millions of titles.
- Production-grade security hardening (beyond basic auth and HTTPS).
- Mobile or web clients.

### Personas
| Persona | Need |
|---------|------|
| **Casual viewer** | Quickly find a movie and save it for later. |
| **Student / demo user** | Explore the app to see architectural patterns in action. |

---

## Core Features

### F1 — User Authentication
- **Register:** email + password → stored in backend (hashed).
- **Login:** returns JWT; client stores token in memory or OS keychain.
- **Logout:** clears local session.
- **Constraint mapping:** Auth is a separate **Microfrontend** (`auth_mf`) with its own MVP triad.

### F2 — Movie Browse & Details
- **Browse:** paginated list of movies from external API (title, poster, rating).
- **Details:** single movie view (overview, genres, release year, cast snippet).
- **Constraint mapping:** `browse_mf` Microfrontend; movie data fetched via **API Gateway** only—client never calls TMDB/OMDB directly.

### F3 — Favorites
- **Add / remove favorite** from movie detail or list row.
- **View favorites** in a dedicated panel.
- **Constraint mapping:** Each favorite action emits a **domain event** (`MovieFavorited`, `MovieUnfavorited`) persisted via **Event Sourcing** to cloud storage (e.g., Somee.com SQL). Read model rebuilt via CQRS projections.

### F4 — Trending Chart
- **Display:** horizontal bar chart of **Top 5 trending movies** (by popularity or rating from external API).
- **Constraint mapping:** `charts_mf` Microfrontend using **QtCharts** (`QChart`, `QBarSeries`). Data sourced from backend Gateway endpoint, not hardcoded.

### F5 — AI Movie Advisor (RAG Chat)
- **Chat UI:** simple message thread; user asks for recommendations.
- **Behavior:** backend retrieves relevant rows from a **local CSV movie dataset**, augments the prompt, and calls **Ollama** (Docker) for a short natural-language reply.
- **Constraint mapping:** `advisor_mf` Microfrontend; RAG pipeline lives in backend service layer, isolated from UI.

### Feature Priority
| Priority | Feature |
|----------|---------|
| P0 | F1 Auth, F2 Browse, F3 Favorites |
| P1 | F4 Chart, F5 AI Advisor |

---

## Architecture & Tech Stack

### High-Level Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    Desktop Client (PySide6)                      │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌───────┐ │
│  │ auth_mf  │ │browse_mf │ │fav_mf    │ │charts_mf │ │adv_mf │ │
│  │ MVP      │ │ MVP      │ │ MVP      │ │ MVP      │ │ MVP   │ │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ └───┬───┘ │
│       └────────────┴────────────┴────────────┴───────────┘     │
│                         Shared API Client                        │
└──────────────────────────────┬──────────────────────────────────┘
                               │ HTTP (REST)
┌──────────────────────────────▼──────────────────────────────────┐
│                     FastAPI Backend (MVC + CQRS)                 │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────────────┐ │
│  │ Controllers │→ │ Commands /   │→ │ Event Store (Somee SQL) │ │
│  │ (Views)     │  │ Queries      │  │ append-only events      │ │
│  └─────────────┘  └──────────────┘  └─────────────────────────┘ │
│         │                │                    │                  │
│         ▼                ▼                    ▼                  │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────────────┐ │
│  │ Models      │  │ Projections  │  │ API Gateway             │ │
│  │ (Domain)    │  │ (Read DB)    │  │ → TMDB / OMDB           │ │
│  └─────────────┘  └──────────────┘  └─────────────────────────┘ │
│                          │                                       │
│                          ▼                                       │
│                   ┌──────────────┐  ┌─────────────────────────┐ │
│                   │ RAG Service  │→ │ Ollama (Docker, local)    │ │
│                   │ + CSV index  │  │ llama3 / mistral          │ │
│                   └──────────────┘  └─────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

---

### 1. Frontend — PySide6, Microfrontends, MVP

| Aspect | Decision |
|--------|----------|
| Framework | **PySide6** (Qt6 bindings) |
| Pattern | **MVP:** each screen has a `View` (Qt widgets), `Presenter` (logic, API calls), `Model` (DTOs / state). |
| Microfrontends | Independent Python packages under `frontend/microfrontends/`, each with own views + presenter + optional router. Shell app loads MF modules and wires navigation. |
| Communication | Microfrontends do not import each other; they communicate via a thin **event bus** (Qt signals or pub/sub) and shared **API client**. |
| Charting | **QtCharts** module (`PySide6.QtCharts`) in `charts_mf`. |

**MVP example (Browse):**
- **View:** `MovieListWidget`, `MovieDetailWidget`
- **Presenter:** fetches `/movies`, handles pagination, emits view updates
- **Model:** `MovieSummary`, `MovieDetail` dataclasses

---

### 2. Backend — FastAPI, MVC, CQRS

| Layer | Responsibility |
|-------|----------------|
| **Controllers** (MVC View) | FastAPI routers; validate request/response schemas; no business logic. |
| **Models** (MVC Model) | Domain entities: `User`, `Favorite`, `MovieEvent`. |
| **Services** (MVC Controller) | Orchestrate commands/queries; enforce rules. |

**CQRS split:**

| Side | Examples |
|------|----------|
| **Commands** (write) | `RegisterUser`, `LoginUser`, `AddFavorite`, `RemoveFavorite` → append events |
| **Queries** (read) | `GetFavorites`, `GetTrendingMovies`, `GetMovieById` → read from projections or Gateway |

Command handlers are synchronous for MVP; queries may cache Gateway responses (TTL ~5 min).

---

### 3. Database & Storage — Event Sourcing (Cloud)

| Component | Implementation |
|-----------|----------------|
| **Event Store** | Somee.com (or similar) **SQL Server** table: `events(id, aggregate_id, event_type, payload JSON, timestamp)`. |
| **Events** | `UserRegistered`, `UserLoggedIn`, `MovieFavorited`, `MovieUnfavorited`. |
| **Projections** | Materialized tables: `users`, `user_favorites` rebuilt by projection workers on startup + after each append. |
| **Auth secrets** | JWT signing key in env; passwords bcrypt-hashed in projection table. |

**Flow (Add Favorite):**
1. Command → validate movie exists (Gateway).
2. Append `MovieFavorited` event.
3. Projection updates `user_favorites`.
4. Query side serves updated list.

For local development, SQLite may mirror projections; event store target remains cloud SQL.

---

### 4. External API — API Gateway Pattern

| Rule | Detail |
|------|--------|
| Single entry | All external movie calls go through `gateway/tmdb_client.py` (or OMDB). |
| Abstraction | Domain uses `MovieProvider` interface; Gateway implements it. |
| Endpoints exposed | `GET /movies`, `GET /movies/{id}`, `GET /movies/trending?limit=5`. |
| Resilience | API key from env; basic retry (1×) on 5xx; return 502 with message on failure. |
| Caching | In-memory cache for trending list (reduce quota usage). |

Client **never** holds TMDB/OMDB keys.

---

### 5. Data Visualization — QtCharts

| Requirement | Implementation |
|-------------|----------------|
| Chart type | **Horizontal bar chart** — movie title vs. popularity score |
| Data source | `GET /movies/trending?limit=5` |
| Widget | `QChartView` embedded in `charts_mf` |
| Refresh | Manual refresh button + auto-load on tab open |

---

### 6. AI Integration — RAG + Ollama (Docker)

| Component | Role |
|-----------|------|
| **CSV dataset** | `data/movies.csv` — columns: `title`, `genres`, `overview`, `rating`, `year` (~500–2000 rows). |
| **Retriever** | Simple embedding or TF-IDF / keyword match (minimal: cosine similarity on concatenated text). |
| **Augmenter** | Top-k (k=5) rows injected into system prompt. |
| **Generator** | HTTP POST to `http://localhost:11434/api/generate` (Ollama). |
| **Docker** | `docker-compose.yml` runs `ollama/ollama`; model pulled on first run (`llama3.2` or `mistral`). |

**Endpoint:** `POST /advisor/chat` — body: `{ "message": "..." }` → `{ "reply": "...", "sources": [...] }`.

RAG runs server-side only; desktop sends chat text, receives reply.

---

### Tech Stack Summary

| Layer | Technology |
|-------|------------|
| Desktop UI | Python 3.11+, PySide6, QtCharts |
| API | FastAPI, Uvicorn, Pydantic v2 |
| Auth | JWT (python-jose), passlib bcrypt |
| Event Store | Somee.com SQL Server (pyodbc or pymssql) |
| External Movies | TMDB API v3 (primary) |
| AI | Ollama (Docker), local CSV, optional sentence-transformers |
| DevOps | Docker Compose (Ollama), `.env` for secrets |

---

## Project Structure

```
Movie_Recommendation_System/
├── README.md
├── PRD.md
├── docker-compose.yml              # Ollama service
├── .env.example
│
├── frontend/                       # PySide6 desktop app
│   ├── main.py                     # App entry + shell window
│   ├── shell/
│   │   ├── navigation.py           # Tab / sidebar router
│   │   └── event_bus.py            # Cross-MF signals
│   ├── shared/
│   │   ├── api_client.py           # HTTP client (JWT header)
│   │   └── dto.py                  # Shared dataclasses
│   └── microfrontends/
│       ├── auth_mf/
│       │   ├── view.py
│       │   ├── presenter.py
│       │   └── model.py
│       ├── browse_mf/
│       │   ├── view.py
│       │   ├── presenter.py
│       │   └── model.py
│       ├── favorites_mf/
│       ├── charts_mf/              # QtCharts
│       └── advisor_mf/             # Chat UI
│
├── backend/                        # FastAPI
│   ├── main.py
│   ├── config.py
│   ├── controllers/                # MVC: HTTP routers
│   │   ├── auth_controller.py
│   │   ├── movies_controller.py
│   │   ├── favorites_controller.py
│   │   └── advisor_controller.py
│   ├── models/                     # MVC: domain entities
│   │   ├── user.py
│   │   └── events.py
│   ├── services/                   # MVC: application logic
│   │   ├── command_handlers/
│   │   ├── query_handlers/
│   │   └── projections/
│   ├── gateway/
│   │   ├── movie_provider.py       # Interface
│   │   └── tmdb_client.py          # API Gateway impl
│   ├── event_store/
│   │   ├── repository.py           # Append / read stream
│   │   └── somee_connection.py
│   ├── rag/
│   │   ├── retriever.py
│   │   ├── prompt_builder.py
│   │   └── ollama_client.py
│   └── schemas/                    # Pydantic request/response
│
├── data/
│   └── movies.csv                  # RAG corpus
│
└── tests/
    ├── backend/
    └── frontend/
```

---

## Acceptance Criteria (Minimal)

| ID | Criterion |
|----|-----------|
| AC-1 | User can register, login, and access protected routes with JWT. |
| AC-2 | Movie list and detail load via backend Gateway (TMDB). |
| AC-3 | Favoriting persists; after restart, favorites reflect event-sourced state. |
| AC-4 | Chart displays 5 trending titles with correct labels and values. |
| AC-5 | AI advisor returns a coherent reply citing movies present in CSV. |
| AC-6 | Each Microfrontend is loadable independently; MVP layers are separable in code review. |

---

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Somee.com connectivity | Local SQLite event log for dev; sync script optional. |
| TMDB rate limits | Cache trending; limit pagination size. |
| Ollama resource usage | Document minimum RAM; allow mock advisor in tests. |
| RAG quality on small CSV | Keep user prompts genre-focused; show retrieved titles in UI. |

---

## Milestones (Suggested)

1. **M1 — Skeleton:** Shell app, FastAPI health, Gateway mock, Docker Ollama up.
2. **M2 — Auth + Events:** Register/login, event store on Somee, first projection.
3. **M3 — Movies + Favorites:** Browse, detail, favorite commands/queries.
4. **M4 — Chart + RAG:** QtCharts trending view, advisor chat end-to-end.

---

*End of PRD*
