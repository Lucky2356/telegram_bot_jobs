# AGENTS.md — Telegram Job Bot

## Запуск

```bash
python main.py
```

Бот + FastAPI веб + APScheduler запускаются одновременно через `asyncio.gather`. **Не** через `uvicorn` или `python -m`.
`run.bat` / `run.ps1` при старте **удаляют `vacancies.db`** — для продакшна закомментировать эти строки.

## Прокси

В `main.py:16-17` очищаются `HTTP_PROXY`, `HTTPS_PROXY`, `ALL_PROXY` — они ломают aiogram и httpx.
Новые HTTP-клиенты должны создаваться с `trust_env=False`.

## Парсеры

5 штук в `scrapers/`, наследуют `BaseScraper` (ABC, методы `search()` и `close()`).
Регистрация нового парсера:
1. Класс в `scrapers/`
2. `Scheduler._get_scraper()` → `cls_map` в `core/scheduler.py:27-33`
3. Ключ в `SITES` в `bot/keyboards.py:123-129`

## Ключевые слова

`KEYWORDS_BY_GROUP` в `bot/keyboards.py:56-83`:
`dict[group_name, dict[display_name, list[synonyms]]]`

`get_synonyms(display_names)` — расширяет display_name до всех синонимов. Также резолвит старые английские ключи (например, `"SysAdmin"` → `["Системный администратор", "СисАдмин", ...]`).

## Города

`CITIES: dict[key, label]` в `bot/keyboards.py:87-96`. В БД хранится ключ, при поиске преобразуется в label: `CITIES.get(city, city)`.

## Веб

FastAPI без отдельного процесса — `uvicorn.Server.serve()` внутри `asyncio.gather`. Шаблон: `web/templates/index.html`.
При старте создаёт `web_user` (telegram_id=0), если нет пользователей.

## Фильтр-мастер (FSM)

9 шагов: keywords → exclude_keywords → city → experience → salary/custom_salary → employment → sites → confirm.
Навигация назад через `__back__` значения в callback data.

## `_safe_edit()`

Хелпер в каждом хендлере (определён локально). Игнорирует `TelegramBadRequest('message is not modified')`.
Все `edit_text`/`edit_reply_markup` должны использовать его.

## Digest

Вакансии буферизируются в `Scheduler._user_buffers`, отправляются заголовком + по одной карточке с клавиатурой.
Карточки обрезаются до 4000 символов.

## `_utcnow()`

Кастомная `_utcnow()` в `core/database/models.py:7-8` вместо `datetime.utcnow` (deprecated).
Все `default=` для DateTime используют её, а не `datetime.now`.

## Известные ограничения

- hh.ru: 403 без OAuth (HH_CLIENT_ID + HH_CLIENT_SECRET)
- SuperJob: пустой список без SUPERJOB_API_KEY
- rabota.ru, habr: HTML-парсеры, могут сломаться при редизайне
- Нет тестов, линтера, форматтера, CI, typecheck, pre-commit
