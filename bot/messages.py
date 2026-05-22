from datetime import datetime, timezone
from scrapers.base import VacancyData


EMPLOYMENT_LABELS: dict[str, str] = {
    "full": "Полная занятость",
    "part": "Частичная занятость",
    "remote": "Удалённая работа",
    "project": "Проектная работа",
    "internship": "Стажировка",
}

SOURCE_LABELS: dict[str, str] = {
    "hh": "hh.ru",
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
            minutes = diff.seconds // 60
            return f"{minutes} мин. назад"
        return f"{hours} ч. назад"
    if days == 1:
        return "вчера"
    if days < 7:
        return f"{days} дн. назад"
    return dt.strftime("%d.%m")


def format_vacancy_card(vac: VacancyData) -> str:
    lines = [f"💼 {vac.title}"]
    if vac.company:
        lines.append(f"🏢 {vac.company}")
    if vac.salary_text:
        lines.append(f"💰 {vac.salary_text}")
    if vac.city:
        lines.append(f"📍 {vac.city}")
    if vac.employment_type:
        label = EMPLOYMENT_LABELS.get(vac.employment_type, vac.employment_type)
        lines.append(f"👔 {label}")
    if vac.published_at:
        lines.append(f"🕐 {_relative_date(vac.published_at)}")
    if vac.description:
        clean = vac.description.replace("\n\n", "\n").strip()
        if len(clean) > 300:
            clean = clean[:300].rsplit(" ", 1)[0] + "..."
        lines.append(f"📋 {clean}")
    source_label = SOURCE_LABELS.get(vac.source, vac.source)
    if vac.url:
        lines.append(f"🔗 {source_label} · {vac.url}")
    else:
        lines.append(f"🔗 {source_label}")
    return "\n".join(lines)
