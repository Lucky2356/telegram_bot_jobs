# Bugfix Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix all 59 identified bugs across the Python backend and TypeScript/React frontend

**Architecture:** 8 sequential tasks grouped by file/module boundaries. Each task fixes multiple bugs in the same files. Tasks progress HIGH -> MEDIUM -> LOW priority.

**Tech Stack:** Python 3.12+ (aiogram, FastAPI, SQLAlchemy, aiohttp, httpx), TypeScript 6 (React 19, Vite, TailwindCSS)

---

## File Structure Map

### Tasks 1-5: Python Backend
| Task | Files Touched | Bugs Fixed |
|------|--------------|------------|
| 1 | `bot/handlers/filters.py`, `bot/handlers/card_actions.py` | 4 |
| 2 | `core/scheduler.py`, `web/app.py` | 4 |
| 3 | `core/database/repository.py`, `core/config.py`, `main.py` | 4 |
| 4 | `scrapers/*.py`, `utils/text_cleaner.py`, `bot/keyboards.py` | 9 |
| 5 | `web/app.py`, `web/auth.py`, `bot/messages.py`, `bot/keyboards.py` | 6 |

### Tasks 6-8: TypeScript Frontend
| Task | Files Touched | Bugs Fixed |
|------|--------------|------------|
| 6 | `App.tsx` | 6 |
| 7 | All components + `api/index.ts` + `types/index.ts` | 12 |
| 8 | `web/app.py` (backend: exclude SSE from auth), `main.tsx`, `index.css` | 3 |

---

### Task 1: Bot handlers -- missing `_safe_edit`, redundant unpack, None text crash

**Files:**
- Modify: `bot/handlers/filters.py:81` -- missing `_safe_edit`
- Modify: `bot/handlers/filters.py:72` -- redundant `FilterCallback.unpack`
- Modify: `bot/handlers/filters.py:237` -- crash on None `message.text`
- Modify: `bot/handlers/card_actions.py:76` -- missing `_safe_edit`

- [ ] **Step 1: Fix `filters.py:81` -- keywords toggle crash**

  Change direct `edit_reply_markup` to `_safe_edit`:
  ```python
  await _safe_edit(callback.message, reply_markup=build_keywords_keyboard(selected))
  ```

- [ ] **Step 2: Fix `filters.py:72` -- redundant unpack**

  Read actual callback data format from `FilterCallback` class (around line 67). Use the parsed callback directly instead of `FilterCallback.unpack(callback.data).value`.

- [ ] **Step 3: Fix `filters.py:237` -- None `message.text` crash**

  ```python
  if not message.text:
      await message.answer("Пожалуйста, введите текст")
      return
  text = message.text.strip()
  ```

- [ ] **Step 4: Fix `card_actions.py:76` -- missing `_safe_edit`**

  Wrap `edit_text` call in `_safe_edit(callback.message, text=..., reply_markup=...)`.

- [ ] **Step 5: Commit**

  ```bash
  git add bot/handlers/filters.py bot/handlers/card_actions.py
  git commit -m "fix(bot): add missing _safe_edit, fix None text crash, remove redundant FilterCallback.unpack"
  ```

---

### Task 2: Scheduler -- race condition, double fetch, private attr, fire-and-forget logging

**Files:**
- Modify: `core/scheduler.py`
- Modify: `web/app.py`

- [ ] **Step 1: Remove `_user_buffers.clear()` from `_send_to_telegram`**

  Delete line `self._user_buffers.clear()` -- the buffer is already cleared before population in `run_check`.

- [ ] **Step 2: Fix double user fetch in `run_check_for_filter`**

  Pass `user` to `_check_filter(vf, user)`. Update `_check_filter` signature: `async def _check_filter(self, vf, user=None)` -- only fetch user if not provided.

- [ ] **Step 3: Add public `is_checking` property**

  ```python
  @property
  def is_checking(self) -> bool:
      return self._lock.locked()
  ```

- [ ] **Step 4: Add error-logging task wrapper + use it in `web/app.py`**

  In `core/scheduler.py`:
  ```python
  import logging
  logger = logging.getLogger(__name__)
  ```

  In `web/app.py`, wrap `asyncio.create_task(scheduler.run_check())` in a wrapper that logs exceptions.

- [ ] **Step 5: Update `web/app.py:401` to use `scheduler.is_checking`**

  Replace `scheduler._lock.locked()` with `scheduler.is_checking`.

- [ ] **Step 6: Commit**

  ```bash
  git add core/scheduler.py web/app.py
  git commit -m "fix(core): fix _user_buffers race, double user fetch, add is_checking() public API"
  ```

---

### Task 3: Database + Config -- is_blocked early return, hardcoded password, .env path, Alembic URL

**Files:**
- Modify: `core/database/repository.py:204-216`
- Modify: `core/config.py:5,15`
- Modify: `main.py:35`

- [ ] **Step 1: Fix `is_blocked` -- remove early return**

  Remove `if not company: return False`. Check company pattern only if company is non-None. Always check title pattern.

- [ ] **Step 2: Fix hardcoded `WEB_PASSWORD` default**

  Change `WEB_PASSWORD: str = "F65Hei812QF!"` to `WEB_PASSWORD: str = ""`.

- [ ] **Step 3: Fix `.env` path to be absolute**

  ```python
  model_config = SettingsConfigDict(
      env_file=os.path.join(os.path.dirname(__file__), "..", ".env"),
      ...
  )
  ```

- [ ] **Step 4: Fix Alembic sync URL derivation**

  ```python
  SQLITE_PREFIX = "sqlite+aiosqlite://"
  if settings.DATABASE_URL.startswith(SQLITE_PREFIX):
      sync_url = "sqlite+pysqlite://" + settings.DATABASE_URL[len(SQLITE_PREFIX):]
  else:
      sync_url = settings.DATABASE_URL
  ```

- [ ] **Step 5: Commit**

  ```bash
  git add core/database/repository.py core/config.py main.py
  git commit -m "fix(db,config): fix is_blocked early return, remove hardcoded password, fix .env path, robust Alembic URL"
  ```

---

### Task 4: Scrapers + utils -- 9 fixes across 6 files

**Files:**
- Modify: `scrapers/superjob_ru.py`
- Modify: `scrapers/trudvsem_ru.py`
- Modify: `scrapers/hh_ru.py`
- Modify: `scrapers/habr_career.py`
- Modify: `scrapers/rabota_ru.py`
- Modify: `scrapers/base.py`
- Modify: `utils/text_cleaner.py`
- Modify: `bot/keyboards.py`

- [ ] **Step 1: Fix `superjob_ru.py` -- `.upper()` crash + duplicate emp_form**

  ```python
  salary_text = " ".join(parts) + f" {str(currency or 'rub').upper()}"
  ```
  Extract `EMPLOYMENT_MAP` to a constant.

- [ ] **Step 2: Fix `trudvsem_ru.py` -- paginate 3 pages**

  Change `for page in range(1):` to `for page in range(3):`.

- [ ] **Step 3: Fix `hh_ru.py` -- log warning for unrecognized city + validate response is dict**

  Add logger.warning for unknown city keys. Add `isinstance(data, dict)` check after `resp.json()`.

- [ ] **Step 4: Fix `habr_career.py` -- use regex for `source_id`**

  ```python
  import re
  source_id = re.search(r'/vacancies/(\d+)', href).group(1) if href and re.search(r'/vacancies/(\d+)', href) else None
  ```

- [ ] **Step 5: Fix `rabota_ru.py` -- use `urljoin`**

  ```python
  from urllib.parse import urljoin
  href = urljoin("https://rabota.ru", href)
  ```

- [ ] **Step 6: Add `close()` abstract method to `BaseScraper`**

- [ ] **Step 7: Fix `text_cleaner.py` -- regex edge case**

  `re.findall(r"\d[\d ]*", text)` instead of `r"[\d ]{2,}"`.

- [ ] **Step 8: Fix `bot/keyboards.py` -- typo "BI Analyts"**

  Change to `"BI Analyst": ["BI Analyst", "BI-аналитик", "Power BI", "Tableau"]`.

- [ ] **Step 9: Commit**

  ```bash
  git add scrapers/ utils/text_cleaner.py bot/keyboards.py
  git commit -m "fix(scrapers): fix currency crash, paginate trudvsem, validate api responses, add close() ABC"
  ```

---

### Task 5: Web Python + auth -- dead code, history isolation, JWT, messages, mutable state

**Files:**
- Modify: `web/app.py`
- Modify: `web/auth.py`
- Modify: `bot/messages.py`
- Modify: `bot/keyboards.py`

- [ ] **Step 1: Fix `web/app.py` dead code + redundant import**

  Replace `user_id=user.id if user else 1` with `user_id=user.id`.
  Remove redundant re-import of `settings` inside function body.

- [ ] **Step 2: Fix history endpoint -- add user_id filter**

  Pass `user_id` to `get_recent_sent`. Update repository method to accept optional `user_id`.

- [ ] **Step 3: Fix JWT -- add `sub` claim**

  ```python
  import hashlib
  password_hash = hashlib.sha256(settings.WEB_PASSWORD.encode()).hexdigest()[:16]
  payload = json.dumps({"exp": int(time.time()) + TOKEN_TTL, "sub": password_hash}, ...)
  ```

- [ ] **Step 4: Fix `bot/messages.py` -- log warning for future dates**

  Add `logger.warning(...)` in the `days < 0` branch.

- [ ] **Step 5: Commit**

  ```bash
  git add web/app.py web/auth.py bot/messages.py
  git commit -m "fix(web): fix dead code, history isolation, JWT sub claim, future date logging"
  ```

---

### Task 6: Frontend App.tsx -- 6 HIGH/MEDIUM bugs

**File:** `web/frontend/src/App.tsx`

- [ ] **Step 1: Fix blank stats tab (HIGH)**

  Change condition from `activeTab === 'stats' && stats && (...)` to `activeTab === 'stats' && (stats ? <Suspense>...</Suspense> : <LoadingSpinner />)`.

- [ ] **Step 2: Fix duplicate API call on filter save (HIGH)**

  Remove `fetchResults()` from `handleSavedFilter` -- `handleRefresh` already calls it.

- [ ] **Step 3: Fix perpetual spinner on config fetch failure (HIGH)**

  Add `configError` state. Show retry UI when config fetch fails instead of infinite spinner.

- [ ] **Step 4: Fix login flash (MEDIUM)**

  Use tri-state `'loading' | 'authenticated' | 'unauthenticated'`. Show spinner during loading.

- [ ] **Step 5: Wrap `AuthenticatedApp` in ErrorBoundary + move outside App (MEDIUM+LOW)**

  Add `<ErrorBoundary>` wrapper. Define `AuthenticatedApp` as module-level function.

- [ ] **Step 6: Commit**

  ```bash
  git add web/frontend/src/App.tsx
  git commit -m "fix(web): fix blank stats tab, duplicate API call, config fail, login flash, error boundaries"
  ```

---

### Task 7: Frontend components -- 12 fixes

**Files:**
- `web/frontend/src/components/VacancyCard.tsx`
- `web/frontend/src/components/FilterModal.tsx`
- `web/frontend/src/components/SavedPanel.tsx`
- `web/frontend/src/components/BlocklistPanel.tsx`
- `web/frontend/src/components/HistoryPanel.tsx`
- `web/frontend/src/components/StatsPanel.tsx`
- `web/frontend/src/components/VacancyDetail.tsx`
- `web/frontend/src/components/Toast.tsx`
- `web/frontend/src/api/index.ts`
- `web/frontend/src/types/index.ts`

- [ ] **Step 1: Fix VacancyCard description truncation (MEDIUM)**

  ```tsx
  const truncateDesc = (desc: string, maxLen: number) => {
      if (desc.length <= maxLen) return desc
      const truncated = desc.slice(0, maxLen)
      const lastSpace = truncated.lastIndexOf(' ')
      return (lastSpace > 0 ? truncated.slice(0, lastSpace) : truncated) + '...'
  }
  ```

- [ ] **Step 2: Fix FilterModal exclude keywords grouping + duplicate keys (MEDIUM)**

  Use `Object.entries()` instead of `Object.values()` to preserve group names. Use composite key `${group}-${kw}`.

- [ ] **Step 3: Fix FilterModal salary matching safeguard**

- [ ] **Step 4: Add loading states to SavedPanel + BlocklistPanel (LOW)**

- [ ] **Step 5: Consolidate hardcoded site labels (LOW)**

  Either use `config.sites` prop or centralize in one place.

- [ ] **Step 6: Fix HistoryPanel useEffect missing deps (LOW)**

  Add `// eslint-disable-line react-hooks/exhaustive-deps` comment.

- [ ] **Step 7: Fix Toast module-level mutable (LOW)**

  Add optional chaining: `addToastFn?.({...})`.

- [ ] **Step 8: Fix api/index.ts -- remove unreachable throw (LOW)**

  Replace `throw new Error(...)` with `return`.

- [ ] **Step 9: Fix types/index.ts -- unused SalaryTuple (LOW)**

- [ ] **Step 10: Commit**

  ```bash
  git add web/frontend/src/components/ web/frontend/src/api/index.ts web/frontend/src/types/index.ts
  git commit -m "fix(web): fix description truncation, exclude keywords grouping, loading states, labels, deps"
  ```

---

### Task 8: Remaining fixes -- SSE auth exclusion, TS version, main.tsx, index.css

**Files:**
- Modify: `web/app.py`
- Modify: `web/frontend/package.json`
- Modify: `web/frontend/src/main.tsx`
- Modify: `web/frontend/src/index.css`

- [ ] **Step 1: Exclude `/api/events` from auth middleware**

  Add `"/api/events"` to the excluded paths list in `auth_middleware`.

- [ ] **Step 2: Fix TypeScript version**

  Change `"typescript": "~6.0.2"` to `"typescript": "~5.8.0"`.

- [ ] **Step 3: Fix main.tsx non-null assertion**

  ```tsx
  const rootEl = document.getElementById('root')
  if (!rootEl) throw new Error('Root element not found')
  createRoot(rootEl)
  ```

- [ ] **Step 4: Fix index.css layer directives (if needed)**

  Wrap custom animations in `@layer utilities`.

- [ ] **Step 5: Commit**

  ```bash
  git add web/app.py web/frontend/package.json web/frontend/src/main.tsx web/frontend/src/index.css
  git commit -m "fix(web): exclude SSE from auth, fix TS version, fix main.tsx, fix CSS layers"
  ```

---

## Verification

- [ ] **Run pytest**
  ```bash
  pytest -v
  ```

- [ ] **Frontend build check**
  ```bash
  cd web/frontend && npm run build
  ```

- [ ] **Start the app and verify**
  ```bash
  python main.py
  ```
