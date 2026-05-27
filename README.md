# Telegram Job Bot

Telegram-бот и веб-панель для поиска вакансий по фильтрам. Проект запускает в одном процессе:

- Telegram-бота на `aiogram`;
- FastAPI веб-панель;
- APScheduler для регулярных проверок;
- SQLite/SQLAlchemy базу с Alembic-миграциями;
- React/Vite frontend.

## Что умеет

- Поиск вакансий по ключевым словам, городу, зарплате, опыту, типу занятости и источникам.
- Строгая фильтрация типа занятости: если выбран `Удаленно`, проходят только удаленные вакансии; если `Полная`, только полная занятость.
- Повторные поиски по фильтрам без “залипания” старых результатов.
- Telegram-карточки вакансий с кнопками сохранения, скрытия и похожих вакансий.
- Веб-панель для управления фильтрами, результатами, историей, избранным и блок-листом.
- Preview фильтра без отправки в Telegram.
- Диагностика фильтра по каждому источнику: сколько пришло, сколько прошло, почему отсеяно.
- Релевантность вакансий через `score` и антишум для нерелевантных профессий.
- Персистентная очередь Telegram-доставки с retry после сетевых ошибок.
- Backup SQLite перед миграциями и ручной backup из веб-панели.
- JWT-авторизация веб-панели, rate limit, security headers и диагностика конфигурации.
- Импорт/экспорт фильтров и полный JSON-экспорт пользовательских данных.
- Health-check источников и журнал событий проверок.

## Источники вакансий

| Источник | Метод | Примечание |
|---|---|---|
| hh.ru | API + HTML fallback | OAuth повышает стабильность |
| SuperJob | API | Нужен `SUPERJOB_API_KEY` |
| Работа России | Open Data API | Работает без ключа |
| rabota.ru | HTML-парсер | Может ломаться при редизайне сайта |
| Хабр Карьера | HTML-парсер | Может ломаться при редизайне сайта |

## Быстрый старт

### 1. Клонировать проект

```bash
git clone https://github.com/Lucky2356/telegram_bot_jobs.git
cd telegram_bot_jobs
```

### 2. Установить Python-зависимости

```bash
pip install -r requirements.txt
```

### 3. Установить frontend-зависимости

```bash
cd web/frontend
npm install
npm run build
cd ../..
```

### 4. Настроить `.env`

```bash
copy .env.example .env
```

Минимально нужно указать:

```env
BOT_TOKEN=your_bot_token_here
WEB_PASSWORD=your_web_password
JWT_SECRET=long_random_secret
```

`BOT_TOKEN` берется у [@BotFather](https://t.me/BotFather).

### 5. Запустить проект

```bash
python main.py
```

Открой веб-панель:

```text
http://127.0.0.1:8000
```

Важно: проект запускается через `python main.py`. Не нужно запускать отдельно `uvicorn`, потому что бот, FastAPI и scheduler стартуют вместе.

## Переменные окружения

| Переменная | Назначение |
|---|---|
| `BOT_TOKEN` | Токен Telegram-бота |
| `SUPERJOB_API_KEY` | API-ключ SuperJob |
| `HH_CLIENT_ID` / `HH_CLIENT_SECRET` | OAuth для hh.ru |
| `HH_USER_AGENT` | User-Agent для hh.ru |
| `DATABASE_URL` | URL базы, по умолчанию SQLite |
| `WEB_HOST` / `WEB_PORT` | Хост и порт веб-панели |
| `WEB_CORS_ORIGINS` | Разрешенные origin для веба |
| `WEB_PASSWORD` | Пароль веб-панели |
| `WEB_PASSWORD_HASH` | Более безопасная альтернатива `WEB_PASSWORD` |
| `JWT_SECRET` | Секрет подписи JWT |
| `WEB_SESSION_TTL_SECONDS` | Время жизни JWT |
| `WEB_LOGIN_RATE_LIMIT` | Лимит попыток входа |
| `WEB_ACTION_RATE_LIMIT` | Лимит ручных действий |
| `CHECK_INTERVAL_HOURS` | Интервал автоматической проверки |
| `TELEGRAM_PROXY` | Прокси для Telegram, если нужен |
| `BACKUP_DIR` | Папка backup-файлов |
| `SEARCH_CACHE_SECONDS` | Кэш поисковых запросов к источникам |
| `SEARCH_MAX_QUERIES` | Максимум поисковых query на фильтр |
| `WEB_PARSER_HEALTH_CACHE_SECONDS` | Кэш health-check источников |
| `LOG_MAX_BYTES` / `LOG_BACKUP_COUNT` | Ротация логов |
| `DISABLE_TELEGRAM_POLLING` | Отключить polling для локальной проверки веба |

### Хеш пароля веб-панели

Можно использовать не plain-text `WEB_PASSWORD`, а хеш:

```bash
python -c "from web.auth import hash_password; print(hash_password('your-password'))"
```

Результат положить в `.env`:

```env
WEB_PASSWORD_HASH=pbkdf2_sha256$...
WEB_PASSWORD=
```

## Telegram

Основные действия доступны через inline-кнопки:

- создать фильтр;
- посмотреть фильтры;
- включить/выключить фильтр;
- удалить фильтр;
- клонировать фильтр;
- запустить проверку сейчас;
- сохранить вакансию;
- скрыть компанию/похожую вакансию.

Мастер фильтра проходит шаги:

1. ключевые слова;
2. исключающие слова;
3. город;
4. опыт;
5. зарплата;
6. тип занятости;
7. источники;
8. подтверждение.

## Веб-панель

React-панель доступна на `http://127.0.0.1:8000`.

Разделы:

- `Фильтры` — CRUD фильтров, включение/выключение, клонирование.
- `Результаты` — последние найденные вакансии, сортировка, группировка, сохранение и скрытие.
- `История` — история отправленных вакансий.
- `Статистика` — графики и агрегаты.
- `Избранное` — сохраненные вакансии.
- `Блок-лист` — заблокированные компании и ключевые слова.
- `Контроль` — диагностика, preview, здоровье источников, очередь Telegram, backup, импорт/экспорт.

## Диагностика фильтров

Во вкладке `Контроль` можно выбрать фильтр и выполнить:

- `Диагностика` — показывает, сколько вакансий пришло с каждого источника и почему они отсеяны.
- `Preview без Telegram` — запускает поиск и показывает найденные вакансии только в вебе.
- `Рекомендации` — подсказывает, почему фильтр может ничего не находить или давать шум.

Причины отсева:

- `keyword` — не совпали ключевые слова;
- `noise` — вакансия похожа на нерелевантный шум;
- `exclude` — найдено исключающее слово;
- `employment` — не совпал тип занятости;
- `city` — не совпал город;
- `experience` — не совпал опыт;
- `salary` — не совпала зарплата;
- `blocklist` — компания или слово в блок-листе.

## Тип занятости

Фильтрация типа занятости работает строго:

- выбран `Полная` — проходит только `full`;
- выбран `Удаленно` — проходит только `remote`;
- выбран `Частичная` — проходит только `part`;
- выбран `Проектная` — проходит только `project`;
- выбран `Стажировка` — проходит только `internship`.

Если источник не отдал тип занятости, бот пытается распознать его по тексту вакансии. Если тип не удалось определить, вакансия не проходит фильтр с выбранным типом занятости.

## Очередь Telegram

Если Telegram временно недоступен, сообщения не теряются:

- вакансии сохраняются в таблицу доставок;
- retry запускается автоматически каждые 5 минут;
- в вебе можно посмотреть `pending`, `sent`, `failed`;
- есть ручной `Retry` и очистка старых отправленных записей.

## Backup

Перед миграциями SQLite автоматически копируется в `backups/`.

В веб-панели можно:

- создать backup базы;
- посмотреть список backup-файлов;
- сделать полный JSON-экспорт фильтров, блок-листа, избранного и истории.

## База данных и миграции

По умолчанию используется SQLite:

```env
DATABASE_URL=sqlite+aiosqlite:///./vacancies.db
```

Миграции Alembic применяются автоматически при `python main.py`.

Ручные команды:

```bash
alembic upgrade head
alembic downgrade -1
alembic revision --autogenerate -m "description"
```

Если Alembic недоступен, приложение использует fallback `create_tables`.

## Docker

```bash
docker compose up --build
```

Контейнер:

- собирает React frontend;
- запускает `python main.py`;
- хранит SQLite в volume `bot_data`;
- открывает порт `8000`;
- имеет healthcheck `/api/health`.

## Проверки

Backend:

```bash
pip install pytest pytest-asyncio httpx pytest-cov ruff
python -m pytest -q
python -m ruff check .
```

Frontend:

```bash
cd web/frontend
npm run build
```

Текущий проект покрыт тестами основных сценариев:

- API веб-панели;
- фильтры;
- строгая занятость;
- Telegram flow;
- repository/database;
- diagnostics/preview;
- delivery queue;
- auth/logout/security headers;
- backup/export.

## Структура проекта

```text
.
├── main.py                         # Точка входа: bot + web + scheduler
├── core/
│   ├── config.py                   # Настройки из .env
│   ├── scheduler.py                # Поиск, фильтрация, очередь проверок, Telegram delivery
│   └── database/
│       ├── models.py               # SQLAlchemy модели
│       └── repository.py           # Работа с БД
├── bot/
│   ├── dispatcher.py               # Регистрация handlers
│   ├── keyboards.py                # Inline-клавиатуры и константы фильтров
│   ├── messages.py                 # Форматирование карточек
│   └── handlers/                   # Telegram handlers
├── scrapers/
│   ├── base.py                     # VacancyData и BaseScraper
│   ├── hh_ru.py
│   ├── superjob_ru.py
│   ├── trudvsem_ru.py
│   ├── rabota_ru.py
│   └── habr_career.py
├── web/
│   ├── app.py                      # FastAPI API + React static
│   ├── auth.py                     # JWT и password hashing
│   └── frontend/                   # React + Vite + TypeScript + Tailwind
├── alembic/                        # Миграции БД
├── tests/                          # Pytest
├── backups/                        # Runtime backup, не коммитится
├── logs/                           # Runtime логи, не коммитится
└── .env                            # Локальные секреты, не коммитится
```

## Важные ограничения

- `hh.ru` может отдавать меньше данных или 403 без OAuth.
- `SuperJob` без API-ключа возвращает пустой список.
- HTML-парсеры `rabota.ru` и `Хабр Карьера` зависят от верстки сайтов.
- `.env`, `.jwt_secret`, `vacancies.db`, `backups/`, `logs/` не должны попадать в GitHub.
- `run.bat` и `run.ps1` являются локальными вспомогательными скриптами; основной безопасный запуск — `python main.py`.

