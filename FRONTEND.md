# Frontend — Job Bot Dashboard

React + TypeScript + TailwindCSS + Chart.js на Vite.

## Структура

```
web/frontend/src/
├── main.tsx               # Entry point
├── App.tsx                # Root: tabs, theme, data fetching
├── index.css              # Tailwind import + @theme + @custom-variant dark
├── api/
│   └── index.ts           # Fetch-клиент к FastAPI (/api/*)
├── types/
│   └── index.ts           # TypeScript-типы (VacancyFilter, Stats, HistoryItem и др.)
└── components/
    ├── FiltersPanel.tsx   # Таблица фильтров + inline-редактирование названия
    ├── HistoryPanel.tsx   # Таблица истории + поиск + фильтр по сайту
    ├── StatsPanel.tsx     # Графики Chart.js (bar + pie) + stat-карточки
    ├── FilterModal.tsx    # Модалка создания/редактирования фильтра
    ├── Tabs.tsx           # Переключение вкладок (Фильтры / История / Статистика)
    └── Toast.tsx          # Snackbar-уведомления (через toast.success/error/info)
```

## Запуск

- **Dev**: `cd web/frontend && npm run dev` (Vite на 5173, прокси `/api/*` на FastAPI 8000)
- **Prod**: `npm run build`, FastAPI раздаёт `dist/` автоматически

## Правила кода

- `const Component = () => {}`, экспорт `default`
- `handleClick`, `handleKeyDown` — префикс для событий
- Tailwind-классы для всей стилизации (без кастомного CSS)
- Aria-label, tabIndex, onKeyDown для доступности
- Без `;`
- Ранние return
- DRY, осмысленные имена

## Тема

- `dark` класс на `<html>`, toggle через `@custom-variant dark`
- Кастомные цвета: `primary`, `primary-hover`, `primary-light`, `error` в `@theme`
- Сохраняется в localStorage('theme')

## API эндпоинты (FastAPI)

| Метод | Путь | Описание |
|---|---|---|
| GET | /api/config | Константы (employment_types, sites, cities, salaries, keyword_groups) |
| GET | /api/filters | Все активные фильтры |
| POST | /api/filters | Создать фильтр |
| GET | /api/filters/:id | Один фильтр |
| PUT | /api/filters/:id | Обновить фильтр |
| POST | /api/filters/:id/toggle | Вкл/Выкл |
| DELETE | /api/filters/:id | Удалить фильтр |
| GET | /api/history | Последние 50 отправленных вакансий |
| GET | /api/stats | Статистика (счётчики + по дням + по сайтам) |
| POST | /api/check_now | Запустить проверку вакансий |

## Коммиты

`feat(web): ...`, `fix(web): ...`, `chore(web): ...` со строчной буквы, без точки в конце.
