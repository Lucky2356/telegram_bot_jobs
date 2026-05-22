# AGENTS.md — Telegram Job Bot

## Запуск

```bash
# 1. Установить зависимости
pip install -r requirements.txt
cd web/frontend && npm install && cd ../..

# 2. Настроить .env (скопировать из .env.example)
cp .env.example .env  # и вписать BOT_TOKEN, ключи и т.д.

# 3. Запустить
python main.py
```

Бот + FastAPI веб + APScheduler запускаются одновременно через `asyncio.gather`. **Не** через `uvicorn` или `python -m`.

### Docker

```bash
docker compose up --build
```

### Тесты

```bash
pip install pytest pytest-asyncio httpx pytest-cov
pytest -v
```

### Фронтенд (dev-режим)

```bash
cd web/frontend && npm run dev  # Vite на :5173, прокси /api → :8000
```

## Прокси

В `main.py` очищаются `HTTP_PROXY`, `HTTPS_PROXY`, `ALL_PROXY` — они ломают aiogram и httpx.
Новые HTTP-клиенты должны создаваться с `trust_env=False`.

## Парсеры

5 штук в `scrapers/`, наследуют `BaseScraper` (ABC, методы `search()` и `close()`).
Регистрация нового парсера:
1. Класс в `scrapers/`
2. `Scheduler._get_scraper()` → `cls_map` в `core/scheduler.py:49-57`
3. Ключ в `SITES` в `bot/keyboards.py:123-129`

## Ключевые слова

`KEYWORDS_BY_GROUP` в `bot/keyboards.py:56-83`:
`dict[group_name, dict[display_name, list[synonyms]]]`

`get_synonyms(display_names)` — расширяет display_name до всех синонимов. Также резолвит старые английские ключи.

## Города

`CITIES: dict[key, label]` в `bot/keyboards.py:87-96`. В БД хранится ключ, при поиске преобразуется в label: `CITIES.get(city, city)`.

## Веб

FastAPI без отдельного процесса — `uvicorn.Server.serve()` внутри `asyncio.gather`.
При старте создаёт `web_user` (telegram_id=0), если нет пользователей.

### Auth

`WEB_PASSWORD` в `.env` — если установлен, включает JWT-аутентификацию (`web/auth.py`, HMAC-SHA256).
Без пароля — вход без логина (backward compatible).

### API эндпоинты

| Метод | Путь | Описание |
|---|---|---|
| POST | `/api/auth/login` | JWT-логин (`{password}` → `{token}`) |
| GET | `/api/config` | Константы (employment_types, sites, cities, etc.) |
| GET | `/api/events` | SSE-поток событий проверки |
| GET/POST/PUT/DELETE | `/api/filters` | CRUD фильтров |
| POST | `/api/filters/{id}/toggle` | Вкл/Выкл фильтр |
| POST | `/api/filters/{id}/clone` | Клонировать |
| POST | `/api/filters/{id}/check` | Проверить один |
| POST | `/api/check_now` | Запустить проверку всех |
| GET | `/api/results` | Последние результаты |
| GET | `/api/history` | История отправок (paginated) |
| GET | `/api/stats` | Статистика |
| GET | `/api/saved` | Избранные вакансии |
| POST | `/api/vacancies/{id}/save` | Сохранить вакансию |
| POST | `/api/vacancies/{id}/unsave` | Удалить из сохранённых |
| POST | `/api/vacancies/{id}/block` | Заблокировать компанию |
| DELETE | `/api/saved/{id}` | Удалить из избранного |
| GET | `/api/blocklist` | Блок-лист |
| POST | `/api/blocklist/add` | Добавить в блок-лист |
| POST | `/api/blocklist/{id}/delete` | Удалить из блок-листа |
| GET | `/api/status` | Статус парсеров |

### Frontend

- **Vite + React + TypeScript + TailwindCSS v4 + Chart.js**
- SSR-events (EventSource) вместо polling для real-time обновления проверки
- JWT-токен в `sessionStorage('auth_token')`, `Authorization: Bearer` на всех запросах
- Компоненты: `src/components/`, экспорт `default`
- Стили: Tailwind-классы + `@theme` кастомные цвета + `@custom-variant dark`
- Коммиты: `feat(web): ...`, `fix(web): ...`

## Фильтр-мастер (FSM)

9 шагов: keywords → exclude_keywords → city → experience → salary/custom_salary → employment → sites → confirm.
Навигация назад через `__back__` значения в callback data.

## `_safe_edit()`

Хелпер в каждом хендлере (определён локально). Игнорирует `TelegramBadRequest('message is not modified')`.
Все `edit_text`/`edit_reply_markup` должны использовать его.

## Digest

Вакансии буферизируются в `Scheduler._user_buffers`, отправляются заголовком + по одной карточке с клавиатурой.
Карточки обрезаются до 4000 символов. SSE-события публикуются в `Scheduler.event_queue`.

## `_utcnow()`

Кастомная `_utcnow()` в `core/database/models.py:7-8` вместо `datetime.utcnow` (deprecated).
Все `default=` для DateTime используют её, а не `datetime.now`.

## Миграции БД (Alembic)

```bash
alembic upgrade head     # Применить
alembic downgrade -1     # Откатить
alembic revision --autogenerate -m "описание"  # Создать новую
```

При `python main.py` миграции применяются автоматически. Если alembic не установлен — fallback на `create_tables`.

## Известные ограничения

- hh.ru: 403 без OAuth (HH_CLIENT_ID + HH_CLIENT_SECRET)
- SuperJob: пустой список без SUPERJOB_API_KEY
- rabota.ru, habr: HTML-парсеры, могут сломаться при редизайне
- Нет pre-commit hooks
