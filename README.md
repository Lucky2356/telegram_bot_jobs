# Telegram Job Bot 🤖

Бот для поиска вакансий в Telegram. Собирает вакансии с 5 сайтов по заданным фильтрам и присылает их в Telegram.

## Поддерживаемые сайты
| Сайт | Метод |
|---|---|
| [hh.ru](https://hh.ru) | REST API |
| [SuperJob](https://superjob.ru) | REST API (нужен ключ) |
| [Работа России](https://trudvsem.ru) | Open Data API |
| [rabota.ru](https://rabota.ru) | HTML парсинг |
| [Хабр Карьера](https://career.habr.com) | HTML парсинг |

## Возможности
- Создание фильтров через Telegram (полностью на кнопках, без ввода текста)
- Фильтрация по: ключевым словам, городу, зарплате, типу занятости, сайтам
- Ежечасная автоматическая проверка новых вакансий
- Карточка вакансии: заголовок, компания, зарплата, город, тип занятости, описание, ссылка
- Веб-интерфейс для управления фильтрами (`http://127.0.0.1:8000`)
- SQLite база данных (не нужно настраивать сервер)

## Установка и запуск

### 1. Клонировать репозиторий
```bash
git clone https://github.com/Lucky2356/telegram_bot_jobs.git
cd telegram_bot_jobs
```

### 2. Установить зависимости
```bash
pip install -r requirements.txt
```

### 3. Настроить `.env`
Скопируйте `.env.example` в `.env` и заполните:

| Параметр | Обязательный | Где взять |
|---|---|---|
| `BOT_TOKEN` | ✅ | [@BotFather](https://t.me/BotFather) → `/newbot` |
| `SUPERJOB_API_KEY` | ❌ | [api.superjob.ru](https://api.superjob.ru) — регистрация приложения |

### 4. Запустить
```bash
python main.py
```
Или двойным кликом по `run.bat` (Windows).

## Telegram команды
| Команда | Действие |
|---|---|
| `/start` | Главное меню |
| `/add_filter` | Создать новый фильтр (пошаговый мастер) |
| `/filters` | Список фильтров |
| `/pause` | Поставить все фильтры на паузу |
| `/resume` | Возобновить все фильтры |

## Веб-интерфейс
Откройте в браузере: [http://127.0.0.1:8000](http://127.0.0.1:8000)

Доступно:
- Просмотр и управление фильтрами (вкл/выкл, удаление)
- История отправленных вакансий
- Кнопка «Проверить сейчас»

## Структура проекта
```
├── main.py              # Точка входа
├── .env                 # Конфиденциальные настройки
├── core/
│   ├── config.py        # Конфигурация
│   ├── scheduler.py     # Планировщик проверки
│   └── database/        # SQLAlchemy модели + репозиторий
├── bot/                 # Telegram bot (aiogram 3)
│   ├── handlers/        # Обработчики команд
│   ├── keyboards.py     # Inline-клавиатуры
│   └── messages.py      # Шаблоны сообщений
├── scrapers/            # Парсеры сайтов
│   ├── hh_ru.py         # hh.ru API
│   ├── superjob_ru.py   # SuperJob API
│   ├── trudvsem_ru.py   # Работа России API
│   ├── rabota_ru.py     # rabota.ru (HTML)
│   └── habr_career.py   # Хабр Карьера (HTML)
├── web/                 # Веб-интерфейс (FastAPI)
│   ├── app.py
│   └── templates/       # Jinja2 шаблоны
└── utils/               # Вспомогательные утилиты
```

## Технологии
- Python 3.12
- aiogram 3.x — Telegram Bot API
- FastAPI + Jinja2 — веб-интерфейс
- SQLAlchemy + SQLite — база данных
- httpx — HTTP клиент
- BeautifulSoup + lxml — парсинг HTML
- APScheduler — планировщик
