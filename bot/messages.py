from datetime import datetime, timezone
from html import escape
from scrapers.base import VacancyData


EMPLOYMENT_LABELS: dict[str, str] = {
    "full": "Полная занятость",
    "part": "Частичная занятость",
    "remote": "Удалённая работа",
    "project": "Проектная работа",
    "internship": "Стажировка",
}

SOURCE_LABELS: dict[str, str] = {
    "hh": "HeadHunter",
    "superjob": "SuperJob",
    "rabota": "rabota.ru",
    "habr": "Хабр Карьера",
    "trudvsem": "Работа России",
}


def _relative_date(dt: datetime | None) -> str:
    if not dt:
        return ""

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    now = datetime.now(timezone.utc)
    diff = now - dt
    days = diff.days

    if days < 0:
        return ""
    if days == 0:
        hours = diff.seconds // 3600
        if hours == 0:
            minutes = max(1, diff.seconds // 60)
            return f"{minutes} мин. назад"
        return f"{hours} ч. назад"
    if days == 1:
        return "вчера"
    if days < 7:
        return f"{days} дн. назад"

    return dt.strftime("%d.%m")


def _normalize_text(value: str | None, max_len: int) -> str | None:
    if not value:
        return None

    text = " ".join(value.replace("\n", " ").split())
    if len(text) > max_len:
        text = text[:max_len].rsplit(" ", 1)[0].strip() + "..."

    return escape(text)


def _extract_tags(vac: VacancyData) -> str:
    source = f"{vac.title} {vac.description or ''}".lower()
    catalog = [
        "React", "TypeScript", "Next.js", "Python", "Django", "FastAPI",
        "Node.js", "Go", "Docker", "Kubernetes", "PostgreSQL", "1C",
    ]
    tags = [tag for tag in catalog if tag.lower() in source]
    return " · ".join(tags[:5])


def format_vacancy_card(vac: VacancyData) -> str:
    title = _normalize_text(vac.title, 120) or "Без названия"
    company = _normalize_text(vac.company, 70)
    salary = _normalize_text(vac.salary_text, 70)
    city = _normalize_text(vac.city, 70)
    source = escape(SOURCE_LABELS.get(vac.source, vac.source or "Источник"))

    employment = None
    if vac.employment_type:
        employment = escape(EMPLOYMENT_LABELS.get(vac.employment_type, vac.employment_type))

    published = _relative_date(vac.published_at)
    published = escape(published) if published else None

    description = _normalize_text(vac.description, 220)
    tags = _extract_tags(vac)

    lines: list[str] = [f"💼 <b>{title}</b>", ""]

    if company:
        lines.append(f"Компания: <b>{company}</b>")
    if city:
        lines.append(f"Локация: {city}")
    if employment:
        lines.append(f"Формат: {employment}")
    if salary:
        lines.append(f"Зарплата: <b>{salary}</b>")

    lines.append(f"Источник: {source}")

    if published:
        lines.append(f"Опубликовано: {published}")

    if tags:
        lines.extend(["", escape(tags)])

    if description:
        lines.extend(["", description])

    return "\n".join(lines)
