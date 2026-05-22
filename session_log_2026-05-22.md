# Session Log — 2026-05-22

## What was done in this session:

### 1. Vercel React Best Practices Review
- Installed `vercel-react-best-practices` skill from Vercel
- Reviewed all 13 frontend components against 70+ performance rules
- Fixed: side effect in render, `.sort()` → `.toSorted()`, `extractSalary` cached in Map, `React.memo` on VacancyCard
- Fixed: localStorage try-catch, inline callbacks → useCallback, hoisted JSX spinner

### 2. Phase 1 — Web Functionality Features
- **Save/Unsave/Block**: Wired up buttons in VacancyCard, added API endpoints, added delete button in SavedPanel, add-form in BlocklistPanel
- **Clone Filter**: Button + API endpoint
- **Search Filters**: Input field filters chips by name
- **Infinite Scroll**: IntersectionObserver in HistoryPanel
- **ConfirmModal**: Replaced `confirm()` with modal dialog
- **ErrorBoundary**: Wrapper for all panels
- **Filter Name Badge**: Shows which filter found the vacancy

### 3. Phase 2 — Major Features
- **SSE Real-time**: Event queue in Scheduler, `/api/events` endpoint, frontend EventSource replaces polling
- **VacancyDetail Modal**: Full description, all metadata, save/block/open actions
- **Web Auth**: JWT with HMAC (no external deps), login page, middleware, backward compatible

### 4. Phase 3 — Infrastructure
- **Docker**: Multi-stage Dockerfile, docker-compose.yml, .dockerignore
- **Alembic**: Migration setup with initial migration, auto-run on startup
- **Tests**: 20 tests for repository + API (pytest + httpx)
- **CI/CD**: GitHub Actions pipeline (test, lint, build, docker)
- **Docs**: Updated AGENTS.md, added .env.example

### Files created/modified:

#### Backend Python:
- `core/scheduler.py` — event_queue, SSE publishing
- `core/database/repository.py` — get_vacancy_by_id, unsave_vacancy, remove_blocklist_by_id, get_saved_vacancy_by_id
- `core/config.py` — WEB_PASSWORD
- `web/app.py` — auth middleware, login endpoint, SSE endpoint, save/block/clone endpoints
- `web/auth.py` — NEW: JWT token creation/verification
- `main.py` — alembic migration on startup
- `requirements.txt` — added alembic

#### Frontend:
- `web/frontend/src/App.tsx` — SSE, auth, lazy stats
- `web/frontend/src/api/index.ts` — auth headers, save/block/clone methods
- `web/frontend/src/types/index.ts` — vacancy id, filter_name fields
- `web/frontend/src/components/VacancyCard.tsx` — memo, save/block handlers, onDetail
- `web/frontend/src/components/VacancyDetail.tsx` — NEW: detail modal
- `web/frontend/src/components/LoginPage.tsx` — NEW: login form
- `web/frontend/src/components/ConfirmModal.tsx` — NEW: confirmation dialog
- `web/frontend/src/components/ErrorBoundary.tsx` — NEW: error boundary
- `web/frontend/src/components/HistoryPanel.tsx` — infinite scroll
- `web/frontend/src/components/FiltersPanel.tsx` — search, clone, confirm modal
- `web/frontend/src/components/ResultsPanel.tsx` — removed polling, added onDetail
- `web/frontend/src/components/SavedPanel.tsx` — delete button
- `web/frontend/src/components/BlocklistPanel.tsx` — add form

#### Infrastructure:
- `Dockerfile` — NEW: multi-stage build
- `docker-compose.yml` — NEW
- `.dockerignore` — NEW
- `alembic.ini` — NEW
- `alembic/env.py` — NEW
- `alembic/versions/20260522_065609_initial.py` — NEW: initial migration
- `tests/conftest.py` — NEW
- `tests/test_repository.py` — NEW: 12 tests
- `tests/test_api.py` — NEW: 8 tests
- `.github/workflows/ci.yml` — NEW
- `.env.example` — NEW
- `AGENTS.md` — updated

### How to continue:
- Start the project: `python main.py`
- Frontend dev: `cd web/frontend && npm run dev`
- Docker: `docker compose up --build`
- Tests: `pytest -v`
- Auth: set `WEB_PASSWORD=...` in .env

### Commits pushed to GitHub:
1. `perf(web): optimize rendering, bundle splitting, and localStorage safety`
2. `feat(web): Phase 1 — save/block/clone/confirm/error-boundary/filter-name`
3. `feat(web): Phase 2 — SSE real-time, VacancyDetail modal`
4. `feat(web): Phase 2.3 — JWT auth for web dashboard`
5. `feat(infra): Phase 3 — Docker, Alembic, tests, CI/CD`
6. `docs: update AGENTS.md with full instructions, add .env.example`
