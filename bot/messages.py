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
    if vac.description:
        clean = vac.description.replace("\n\n", "\n").strip()
        if len(clean) > 300:
            clean = clean[:300].rsplit(" ", 1)[0] + "..."
        lines.append(f"📋 {clean}")
    source_label = SOURCE_LABELS.get(vac.source, vac.source)
    lines.append(f"🔗 {source_label} · {vac.url}")
    return "\n".join(lines)
