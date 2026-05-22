# Telegram Job Bot — Summary of all changes

## Project structure
```
D:\bot telegram\
├── main.py              # Entry point (bot + web + scheduler)
├── run.bat              # Windows batch launcher
├── run.ps1              # PowerShell launcher
├── .env                 # API keys (BOT_TOKEN, SUPERJOB_API_KEY, HH_CLIENT_ID/SECRET)
├── requirements.txt     # Python dependencies
├── .gitignore
├── AGENTS.md            # OpenCode instruction file
├── FRONTEND.md          # Frontend development rules
├── opencode.json        # OpenCode config (references AGENTS.md + FRONTEND.md)
├── CHANGELOG.md         # This file
├── core/
│   ├── config.py        # Settings from .env
│   ├── scheduler.py     # Periodic check + vacancy filtering + digest + cleanup
│   └── database/
│       ├── models.py    # User, VacancyFilter, Vacancy, SentVacancy, SavedVacancy, Blocklist
│       └── repository.py
├── bot/
│   ├── dispatcher.py
│   ├── keyboards.py     # All inline keyboards + KEYWORDS_BY_GROUP (92 keywords) + get_synonyms()
│   ├── messages.py      # Vacancy card formatter + relative dates
│   └── handlers/
│       ├── start.py     # /start, main menu buttons
│       ├── filters.py   # /add_filter wizard (9 steps), _safe_edit helper
│       ├── control.py   # /filters, /pause, /resume, /stats, /saved, /blocklist
│       └── card_actions.py  # Save/Block/Similar buttons on vacancy cards
├── scrapers/
│   ├── base.py          # VacancyData dataclass + BaseScraper ABC
│   ├── hh_ru.py         # hh.ru API + OAuth + pagination
│   ├── superjob_ru.py   # SuperJob API + pagination
│   ├── trudvsem_ru.py   # Работа России OpenData API
│   ├── rabota_ru.py     # rabota.ru HTML parser (regex link matching)
│   └── habr_career.py   # Хабр Карьера HTML parser
├── web/
│   ├── app.py           # FastAPI + REST API (CRUD filters + history + check + results + saved + blocklist + status)
│   ├── frontend/        # React SPA (Vite + React + TypeScript + TailwindCSS + Chart.js)
│   │   ├── src/
│   │   │   ├── App.tsx
│   │   │   ├── main.tsx
│   │   │   ├── index.css
│   │   │   ├── api/index.ts
│   │   │   ├── types/index.ts
│   │   │   └── components/
│   │   │       ├── Tabs.tsx           # Underline-style tab navigation
│   │   │       ├── Toast.tsx          # Snackbar notifications
│   │   │       ├── StatusBar.tsx      # Parser health indicators
│   │   │       ├── FiltersPanel.tsx   # Filter chips with single-check button
│   │   │       ├── ResultsPanel.tsx   # Search + sort + group + skeleton + 4-col grid
│   │   │       ├── VacancyCard.tsx    # Glass card with accent stripe, expand desc
│   │   │       ├── HistoryPanel.tsx   # Date-grouped history with load more
│   │   │       ├── StatsPanel.tsx     # Chart.js graphs (bar + pie)
│   │   │       ├── SavedPanel.tsx     # Saved/bookmarked vacancies
│   │   │       ├── BlocklistPanel.tsx # Blocked companies/keywords
│   │   │       └── FilterModal.tsx    # Glass modal with collapsible keyword groups
│   │   ├── index.html
│   │   ├── vite.config.ts
│   │   ├── package.json
│   │   ├── tsconfig.json
│   │   └── dist/                      # Built static files (served by FastAPI)
│   └── templates/
│       └── index.html   # Jinja2 fallback (legacy)
└── utils/
    └── text_cleaner.py
```

## How to run
1. `python main.py` (bot + FastAPI web + scheduler via asyncio.gather)
2. For frontend dev: `cd web/frontend && npm run dev` (Vite proxy → FastAPI)
3. For production: `cd web/frontend && npm run build` → FastAPI serves `dist/`
4. Web UI at http://127.0.0.1:8000
5. In Telegram: `/start` → "Добавить фильтр" → follow step-by-step wizard
6. Vacancies checked every hour, digest sent to Telegram

## API Keys
| Key | Required | Where to get |
|---|---|---|
| `BOT_TOKEN` | ✅ | @BotFather in Telegram |
| `SUPERJOB_API_KEY` | ❌ | https://api.superjob.ru/ |
| `HH_CLIENT_ID` + `HH_CLIENT_SECRET` | ❌ | https://dev.hh.ru/ → OAuth |

## All improvements made

### Phase 0 — Critical bug fixes
- City matching: look up via CITIES dict
- Salary filtering: added salary_min/salary_max to VacancyData + scheduler checks
- SuperJob town: pass CITIES.get(city, city) instead of raw key
- SuperJob salary 0: convert 0 to None
- HH salary 0: same fix
- Web creates filter for correct user (not hardcoded id=1)

### Phase 1 — UX fixes
- Removed step numbering from wizard
- Fixed back navigation (employment → salary)
- `datetime.utcnow` → `_utcnow()` wrapper
- Fixed type hints

### Phase 2 — Pagination (all 5 scrapers)
- HH: 3 pages × 50
- SuperJob: 3 pages × 50
- trudvsem: 1 page × 100
- rabota.ru: 1 page (HTML parser)
- habr: 3 pages

### Phase 3 — Telegram UX
- `/saved`, `/blocklist`, `/stats` commands
- Digest buffering + split at 3500 chars
- Concurrent check lock
- Graceful shutdown

### Phase 4 — Web + digest
- Auto-refresh 30s (later removed)
- Filter CRUD on web
- `filter_id` in SentVacancy
- experience + exclude_keywords in API

### Scraper fixes
- rabota.ru: regex link matching
- habr_career: fallback title extraction
- trudvsem: skills + qualification in description
- _safe_edit helper for "message is not modified"
- Proxy env vars cleared at startup
- Keywords deduplicated at DB level

---

## Phase 5 — Frontend migration to React (feat(web): migrate frontend to Vite + React + TypeScript + TailwindCSS)

**What changed:**
- Replaced vanilla Jinja2 dashboard with Vite + React 19 + TypeScript 6 SPA
- Components: App, Tabs, Toast, FiltersPanel, HistoryPanel, StatsPanel, FilterModal
- Dark/light theme via @custom-variant dark + localStorage
- Rich VacancyCard with source badges, salary, chips, description
- API endpoints: /api/config, /api/stats
- TypeScript types for all API responses
- FastAPI serves built React app via StaticFiles (fallback to Jinja2)

**New files:**
- `web/frontend/` — full Vite project
- `FRONTEND.md` — frontend conventions
- `opencode.json` — config referencing AGENTS.md + FRONTEND.md

---

## Phase 6 — Live results + improved design (feat(web): add live results tab with vacancy cards)

**What changed:**
- **Scheduler.last_results** cache — results stored in memory during check
- **GET /api/results** — returns last check results
- **VacancyCard** component with nice card design
- **ResultsPanel** — grid of cards with count + timestamp
- **«Результаты» tab** moved to first position (default)

**New files:**
- `src/components/VacancyCard.tsx`
- `src/components/ResultsPanel.tsx`

---

## Phase 7 — Dashboard redesign (feat(web): redesign dashboard - merge filters+results, improve design, live polling)

**What changed:**
- **All filters shown** (active + inactive) via `get_all_filters()`
- **Filters + Results merged** into single «Поиск» tab
- **Filter chips** with status dot, quick actions (▶ check, ⏸ toggle, ✏️ edit, 🗑 delete)
- **Checking flag** in /api/results for live polling
- **History redesigned** — VacancyCard-like with date grouping (Сегодня / Вчера / Ранее)
- **History pagination** — «Загрузить ещё» button
- **30s auto-refresh removed** — no more scroll reset
- **Fade-in animation** on cards
- **Pill-style tabs** redesigned

**Backend:**
- `Scheduler.get_last_results()` returns serializable dicts
- `GET /api/results` returns `{items, checked_at, checking}`
- `GET /api/history` pagination `?page=N&limit=M`
- `get_all_filters()` in repository (returns all, not just active)

---

## Phase 8 — FilterModal redesign + more features (feat(web): redesign FilterModal to match card/chip system + add single-filter check, saved/blocklist, search/sort/group, parser status)

**What changed:**
- **FilterModal** redesigned: card-style sections, collapsible keyword groups, selected chips, sticky header/footer
- **Single-filter check** via `POST /api/filters/{id}/check` + ▶ button on each chip
- **Search** within results (input filters by title/company)
- **Source filter** in results (select dropdown)
- **Sort** by date (new/old) and salary (high/low)
- **Group by site** toggle (📂 Группы button)
- **Saved vacancies tab** (📁 Избранное) with SavedPanel
- **Blocklist tab** with BlocklistPanel
- **Parser status bar** (🟢/🔴 indicators for each site)
- **Expand description** in VacancyCard («показать ещё»)
- **fade-in + stagger animation** on results
- Tabs simplified to 4: Поиск / История / Избранное / Статистика

**New components:**
- `SavedPanel.tsx` — saved vacancies list
- `BlocklistPanel.tsx` — grouped by type with delete
- `StatusBar.tsx` — colored dots per parser

**Backend:**
- `POST /api/filters/{id}/check` — single filter check
- `GET /api/saved` — saved vacancies
- `GET /api/blocklist` + `POST /api/blocklist/{id}/delete` — blocklist CRUD
- `GET /api/status` — which parsers have API keys

---

## Phase 9 — Keywords expansion + DB fallback + auto-cleanup + design overhaul

### Keywords expanded to 92 roles in 15 groups

| Group | Count | Examples |
|---|---|---|
| 1С / ERP | 5 | 1С Программист, 1С Аналитик, ERP, SAP |
| Backend-разработка | 10 | Python, Java, Go, C++, C#, PHP, Rust, Kotlin, Scala, Ruby |
| Frontend-разработка | 7 | JavaScript, TypeScript, React, Vue, Angular, HTML/CSS, Node.js |
| Мобильная разработка | 4 | iOS, Android, Flutter, React Native |
| Data Science / ML / AI | 7 | Data Scientist, ML Engineer, NLP, CV, AI, BI |
| Базы данных | 6 | DBA, SQL, PostgreSQL, MySQL, ClickHouse, Oracle |
| DevOps / Cloud | 6 | DevOps, Kubernetes, Terraform, Ansible, CI/CD, Cloud |
| Сети и безопасность | 7 | Network, Cisco, Mikrotik, InfoSec, SOC, Pentest, DevSecOps |
| QA / Тестирование | 5 | QA Manual, Automation QA, Load Testing, Game QA |
| Управление | 6 | PM, Product Manager, Team Lead, Delivery, Scrum, CTO |
| Дизайн | 7 | UI/UX, Product, Graphic, Figma, Motion, Game, Art |
| Аналитика | 6 | System Analyst, BA, Data Analyst, BI, Product, Web |
| Маркетинг и продажи | 6 | Marketer, SEO, SMM, Sales, Account, Product Marketing |
| Административный и HR | 7 | HR, Recruiter, HRBP, Office, Бухгалтер, Юрист, Tech Writer |
| Техническая поддержка | 3 | Tech Support, SysAdmin, SRE |

### DB fallback after restart
- `GET /api/results` now returns last 50 vacancies from DB when in-memory cache is empty
- After restart, results tab shows previously found vacancies immediately

### DB auto-cleanup
- `cleanup_old_vacancies(days=7)` in repository — cascade deletes old vacancies
- Runs daily at 03:00 via APScheduler cron job
- Keeps database from growing indefinitely

### Design overhaul — glassmorphism + modern look
- **Inter font** via Google Fonts
- **Glassmorphism**: `bg-white/80 backdrop-blur-sm` on cards, modals, header
- **Accent stripe** on VacancyCard (colored by source: blue/cyan/emerald/amber/rose)
- **Skeleton loading** — animated pulse placeholders while checking
- **4-column grid** on large screens (xl:grid-cols-4)
- **Sticky header** with `backdrop-blur-md` glass effect
- **Tabs**: underline style (Material Design)
- **Colors**: `slate-*` palette instead of `gray-*`, primary `#6366f1`
- **Rounded-2xl** everywhere, softer borders, refined shadows
- **Dark mode**: glass cards `bg-slate-800/80`, refined slate palette
- **Loading spinner** instead of plain text
- **Fade-in + stagger** animations on card appearance

---

## Known issues
- **hh.ru 403**: needs OAuth credentials (HH_CLIENT_ID + HH_CLIENT_SECRET in .env)
- **SuperJob**: empty list without SUPERJOB_API_KEY
- **rabota.ru**: HTML parser, fragile to redesign
- **habr career**: HTML parser, fragile to redesign
- **No tests, linter, formatter, CI, typecheck, pre-commit**

## To continue development
```bash
git pull
cd web/frontend && npm run build
python main.py
```
Web UI at http://127.0.0.1:8000
