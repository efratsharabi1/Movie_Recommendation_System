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

```text
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