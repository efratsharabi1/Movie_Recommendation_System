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
- **Constraint mapping:** Each favorite action emits a **domain event** (`MovieFavorited`, `MovieUnfavorited`) persisted via **Event Sourcing** to cloud storage. Read model rebuilt via CQRS projections.

### F4 — Trending Chart
- **Display:** horizontal bar chart of **Top 5 trending movies** (by popularity or rating from external API).
- **Constraint mapping:** `charts_mf` Microfrontend using **QtCharts** (`QChart`, `QBarSeries`). Data sourced from backend Gateway endpoint, not hardcoded.

### F5 — AI Movie Advisor (RAG Chat)
- **Chat UI:** simple message thread; user asks for recommendations.
- **Behavior:** backend retrieves the user's favorite movies from the database and popular movies from the API Gateway (TMDB). It augments the prompt with this live context and calls **Ollama** (Docker) to select the best matches and provide a natural-language reply.
- **Constraint mapping:** `advisor_mf` Microfrontend; RAG pipeline lives in backend service layer (`RAGRecommendationService`), fully utilizing async external calls. No local CSV is used.

### Feature Priority
| Priority | Feature |
|----------|---------|
| P0 | F1 Auth, F2 Browse, F3 Favorites |
| P1 | F4 Chart, F5 AI Advisor |

---

## Architecture & Tech Stack

### High-Level Diagram

    ┌─────────────────────────────────────────────────────────────────┐
    │                    Desktop Client (PySide6)                     │
    │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌───────┐  │
    │  │ auth_mf  │ │browse_mf │ │fav_mf    │ │charts_mf │ │adv_mf │  │
    │  │ MVP      │ │ MVP      │ │ MVP      │ │ MVP      │ │ MVP   │  │
    │  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ └───┬───┘  │
    │       └────────────┴────────────┴────────────┴───────────┘      │
    │                        Shared API Client                        │
    └──────────────────────────────┬──────────────────────────────────┘
                                   │ HTTP (REST)
    ┌──────────────────────────────▼──────────────────────────────────┐
    │                    FastAPI Backend (MVC + CQRS)                 │
    │  ┌─────────────┐  ┌──────────────┐  ┌─────────────────────────┐ │
    │  │ Controllers │→ │ Commands /   │→ │ Event Store (Supabase)  │ │
    │  │ (Views)     │  │ Queries      │  │ append-only events      │ │
    │  └─────────────┘  └──────────────┘  └─────────────────────────┘ │
    │        │                 │                    │                 │
    │        ▼                 ▼                    ▼                 │
    │  ┌─────────────┐  ┌──────────────┐  ┌─────────────────────────┐ │
    │  │ Models      │  │ Projections  │  │ API Gateway             │ │
    │  │ (Domain)    │  │ (Read DB)    │  │ → TMDB / OMDB           │ │
    │  └─────────────┘  └──────────────┘  └─────────────────────────┘ │
    │                          │                                      │
    │                          ▼                                      │
    │                   ┌──────────────┐  ┌─────────────────────────┐ │
    │                   │ RAG Service  │→ │ Ollama (Docker, local)  │ │
    │                   │ (Live Context│  │ llama3 / mistral        │ │
    │                   └──────────────┘  └─────────────────────────┘ │
    └─────────────────────────────────────────────────────────────────┘

---

### 1. Frontend — PySide6, Microfrontends, MVP

| Aspect | Decision |
|--------|----------|
| Framework | **PySide6** (Qt6 bindings) |
| Pattern | **MVP:** each screen has a `View` (Qt widgets), `Presenter` (logic, API calls), `Model` (DTOs / state). |
| Microfrontends | Independent Python packages under `frontend/microfrontends/`, each with own views + presenter + optional router. Shell app loads MF modules and wires navigation. |
| Communication | Microfrontends do not import each other; they communicate via a thin **event bus** (Qt signals or pub/sub) and shared **API client**. |
| Charting | **QtCharts** module (`PySide6.QtCharts`) in `charts_mf`. |

---

### 2. Backend — FastAPI, MVC, CQRS

| Layer | Responsibility |
|-------|----------------|
| **Controllers** (MVC View) | FastAPI routers; use `Depends()` for Dependency Injection; catch domain exceptions (`ValueError`) and return `HTTPException`; no infrastructure logic. |
| **Handlers / Services** (MVC Controller) | Orchestrate commands/queries; handle gateway logic; catch `httpx` exceptions and map them to domain exceptions. Fully **async**. |
| **Models** (MVC Model) | Domain entities: `User`, `Favorite`, `Event`. |

**CQRS split:**

| Side | Examples |
|------|----------|
| **Commands** (write) | `AuthCommandHandler`, `FavoritesCommandHandler` → append events |
| **Queries** (read) | `MoviesQueryHandler`, `FavoritesQueryHandler` → read from projections or Gateway. Controllers **never** call the Gateway directly. All flows are fully asynchronous using `async def` and `await`. |

---

### 3. Database & Storage — Event Sourcing (Cloud)

| Component | Implementation |
|-----------|----------------|
| **Event Store** | **Supabase** (PostgreSQL) table: `events(id, aggregate_id, event_type, payload JSON, timestamp)`. Chosen for robust native JSON handling and async Python SDK support. |
| **Events** | `UserRegistered`, `UserLoggedIn`, `MovieFavorited`, `MovieUnfavorited`. |
| **Projections** | Materialized tables (e.g., `user_favorites`) updated as events are appended, representing the current read state. |
| **Auth secrets** | JWT signing key in env; passwords bcrypt-hashed in projection table. |

---

### 4. External API — API Gateway Pattern

| Rule | Detail |
|------|--------|
| Single entry | All external movie calls go through `gateway/tmdb_client.py`. |
| Abstraction | Domain services use Gateways to fetch data; Controllers remain oblivious. |
| Endpoints exposed | `GET /movies/search`, `GET /movies/{id}`, `GET /movies/trending`. |
| Resilience | API key from env; mapping `httpx` status errors to clean domain logic exceptions inside the Handlers. |

---

### 5. Data Visualization — QtCharts

| Requirement | Implementation |
|-------------|----------------|
| Chart type | **Horizontal bar chart** — movie title vs. popularity score |
| Data source | `GET /movies/trending` |
| Widget | `QChartView` embedded in `charts_mf` |
| Refresh | Manual refresh button + auto-load on tab open |

---

### 6. AI Integration — RAG + Ollama (Docker)

| Component | Role |
|-----------|------|
| **Context Source** | Live data: User's favorites (from Event Store) + Trending movies (from TMDB via Gateway). |
| **Augmenter** | Formats titles and user preferences into a strict instruction prompt (`RAGRecommendationService`). |
| **Generator** | HTTP POST to `http://ollama:11434/api/generate` (Ollama) via `OllamaGateway`. |
| **Processor** | Maps Ollama's text output back to real TMDB movie objects to ensure accurate display data. |
| **Docker** | `docker-compose.yml` runs `ollama/ollama`; model pulled on first run (`llama3`). |

---

### Tech Stack Summary

| Layer | Technology |
|-------|------------|
| Desktop UI | Python 3.11+, PySide6, QtCharts |
| API | FastAPI, Uvicorn, Pydantic v2 |
| Auth | JWT (python-jose), passlib bcrypt |
| Event Store | Supabase (PostgreSQL via async Client) |
| External Movies | TMDB API v3 (primary) |
| AI | Ollama (Docker, Llama3) |
| DevOps | Docker Compose (Ollama), `.env` for secrets |

---

## Project Structure

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
    │   │   └── recommendations_controller.py
    │   ├── models/                     # MVC: domain entities
    │   │   ├── user.py
    │   │   └── events.py
    │   ├── services/                   # MVC: application logic
    │   │   ├── command_handlers/
    │   │   ├── query_handlers/
    │   │   ├── projections/
    │   │   └── rag_service.py
    │   ├── gateway/                    # External API Gateways
    │   │   ├── tmdb_client.py          
    │   │   └── ollama_gateway.py
    │   ├── event_store/
    │   │   ├── repository.py           # Append / read stream
    │   │   └── supabase_connection.py
    │   └── schemas/                    # Pydantic request/response

---

## Acceptance Criteria (Minimal)

| ID | Criterion |
|----|-----------|
| AC-1 | User can register, login, and access protected routes with JWT. |
| AC-2 | Movie list and detail load via backend Gateway (TMDB) asynchronously. |
| AC-3 | Favoriting persists; after restart, favorites reflect event-sourced state. |
| AC-4 | Chart displays 5 trending titles with correct labels and values. |
| AC-5 | AI advisor returns a coherent recommendation citing live TMDB & favorites data. |
| AC-6 | Each Microfrontend is loadable independently; MVP layers are separable in code review. |

---

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| API Latency | Backend handlers are fully async to prevent blocking FastAPI workers. |
| TMDB rate limits | Limit pagination size and queries during recommendation generation. |
| Ollama resource usage | Document minimum RAM requirement for local execution. |
| RAG quality | Use highly specific system prompts and clean string mapping to ensure accurate TMDB matching. |

---

## Milestones (Suggested)

1. **M1 — Skeleton:** Shell app, FastAPI health, API Gateways setup, Docker Ollama up.
2. **M2 — Auth + Events:** Register/login, Event Store on Supabase, first projection.
3. **M3 — Movies + Favorites:** Controllers, Command/Query handlers (CQRS), async operations.
4. **M4 — Chart + AI:** QtCharts integration, RAG logic complete.