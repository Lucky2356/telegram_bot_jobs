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
├── core/
│   ├── config.py        # Settings from .env
│   ├── scheduler.py     # Periodic check + vacancy filtering + digest
│   └── database/
│       ├── models.py    # User, VacancyFilter, Vacancy, SentVacancy, SavedVacancy, Blocklist
│       └── repository.py
├── bot/
│   ├── dispatcher.py
│   ├── keyboards.py     # All inline keyboards + KEYWORDS_BY_GROUP + get_synonyms()
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
│   ├── app.py           # FastAPI + REST API (CRUD filters + history + check)
│   └── templates/
│       └── index.html   # Dashboard with dark theme, auto-refresh, edit/create modals
└── utils/
    └── text_cleaner.py
```

## How to run
1. Click `run.bat` (Windows) or `python main.py` in VS Code terminal
2. Bot connects to Telegram + web UI at http://127.0.0.1:8000
3. In Telegram: `/start` → "Добавить фильтр" → follow step-by-step wizard
4. Vacancies are checked every hour, digest sent to Telegram

## API Keys needed
| Key | Where to get | Required |
|---|---|---|
| `BOT_TOKEN` | @BotFather in Telegram | ✅ Yes |
| `SUPERJOB_API_KEY` | https://api.superjob.ru/ → Register app | ❌ Optional (without it SuperJob won't work) |
| `HH_CLIENT_ID` + `HH_CLIENT_SECRET` | https://dev.hh.ru/ → Create app → OAuth | ❌ Optional (without it hh.ru returns 403) |

## All improvements made

### Phase 0 — Critical bug fixes
- **City matching**: was comparing filter key "moscow" with city label "Москва" → never matched. Fixed: look up via CITIES dict.
- **Salary filtering**: was not implemented at all. Added `salary_min`/`salary_max` to VacancyData + checks in scheduler.
- **SuperJob town**: was passing key "moscow" instead of label. Fixed: pass CITIES.get(city, city).
- **SuperJob salary 0**: `payment_to=0` means "not set", was treated as max=0 → filtered all jobs. Fixed: convert 0 to None.
- **HH salary 0**: same fix.
- **Web creates filter for wrong user**: was always user_id=1. Fixed: get first real user from DB.

### Phase 1 — UX fixes
- Removed step numbering from wizard messages
- Fixed back navigation from employment → salary (was going to experience)
- `datetime.utcnow` → `datetime.now(timezone.utc)` with proper _utcnow() wrapper
- Fixed `get_recent_sent` return type hint

### Phase 2 — Pagination (all 5 scrapers)
- HH: 3 pages × 50 = up to 150 results
- SuperJob: 3 pages × 50 = up to 150 results
- trudvsem: 1 page × 100 (API returns 500 beyond page 0)
- rabota.ru: 1 page (limited, HTML parser)
- habr: 3 pages

### Phase 3 — Telegram UX improvements
- `/saved` — saved/bookmarked vacancies
- `/blocklist` — view blocked companies
- `/stats` — statistics (filters, vacancies sent, by site)
- Digest: vacancies buffered, sent as single message per user
- Digest split at 3500 chars to avoid Telegram's 4096 limit
- Concurrent check lock (prevents double-run)
- Graceful shutdown (closes connections on Ctrl+C)

### Phase 4 — Web + digest
- Auto-refresh dashboard every 30 seconds (skips when modal open)
- Create filter on web (POST /api/filters)
- `filter_id` in SentVacancy → shows which filter matched each vacancy in web history
- `experience` + `exclude_keywords` exposed in web API

### Keyword system rewrite
- KEYWORDS_BY_GROUP changed from `dict[str, list[str]]` to `dict[str, dict[str, list[str]]]`
- Each keyword now has Russian display name + all synonyms
- `get_synonyms()` function: expands display names to all search variants
- Reverse lookup: old English keywords (e.g. "SysAdmin") auto-resolve to Russian synonyms
- Examples:
  - "Системный администратор" → ["SysAdmin", "Системный администратор", "СисАдмин", "System Administrator"]
  - "Junior / Младший" → ["Junior", "Джуниор", "Младший"]
  - "Backend / Бэкенд" → ["Backend", "Бэкенд", "Бекенд"]

### Scraper fixes
- **rabota.ru**: rewrote parser — uses regex `/vacancy/(\d+)` to find real vacancy links, ignores garbage
- **habr_career**: added fallback title extraction (searches `[class*=title]`, then link text, then card text)

### Stability fixes
- `_safe_edit()` helper: silently ignores Telegram "message is not modified" errors
- Proxy env vars cleared at startup (prevents SOCKS proxy conflicts)
- Keywords deduplicated at DB level (`list(dict.fromkeys(...))`)
- trudvsem description now includes `skills` + `qualification` fields

## Known issues
- **hh.ru 403**: needs OAuth credentials (HH_CLIENT_ID + HH_CLIENT_SECRET in .env)
- **rabota.ru**: HTML parser works but page structure may change
- **habr career**: HTML parser works but may break if site redesigns
- **Network errors**: "Указанное сетевое имя более недоступно" = network issue, not a bug

## To continue development later
- Run `git pull` to get latest code
- Run `python main.py` or double-click `run.bat`
- Web UI at http://127.0.0.1:8000
- Delete old `vacancies.db` if schema changed
