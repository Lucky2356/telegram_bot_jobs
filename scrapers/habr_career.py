import httpx
import re
from datetime import datetime
from bs4 import BeautifulSoup
from scrapers.base import BaseScraper, VacancyData
from bot.keyboards import CITIES
from utils.text_cleaner import extract_salary_numbers


HABR_URL = "https://career.habr.com/vacancies"


class HabrCareerScraper(BaseScraper):
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0, follow_redirects=True, trust_env=False)

    async def close(self):
        await self.client.aclose()

    async def search(
        self, keywords: list[str], city: str | None = None
    ) -> list[VacancyData]:
        query = " ".join(keywords)
        results: list[VacancyData] = []
        seen: set = set()
        for page in range(3):
            params: dict = {"q": query, "type": "all", "page": page}
            if city:
                params["city"] = CITIES.get(city, city)
            try:
                resp = await self.client.get(HABR_URL, params=params)
                resp.raise_for_status()
                page_results = self._parse_html(resp.text)
                for v in page_results:
                    if v.source_id not in seen:
                        seen.add(v.source_id)
                        results.append(v)
            except Exception:
                break
        return results

    def _parse_html(self, html: str) -> list[VacancyData]:
        results: list[VacancyData] = []
        soup = BeautifulSoup(html, "lxml")

        cards = (
            soup.select("div.vacancy-card")
            or soup.select("div[class*=vacancy][class*=card]")
            or soup.select("div.vacancy-card__info")
            or soup.find_all("div", class_=re.compile(r"vacancy", re.I))
        )

        for card in cards:
            try:
                link_tag = card.select_one("a[href*='/vacancies/']") or card.find("a", href=True)
                if not link_tag:
                    continue
                href = link_tag.get("href", "")
                if not href.startswith("http"):
                    href = "https://career.habr.com" + href

                m_id = re.search(r'/vacancies/(\d+)', href)
                source_id = m_id.group(1) if m_id else href.split("/")[-1].split("?")[0]

                title = link_tag.get_text(strip=True)
                if not title:
                    title_el = (
                        card.select_one(".vacancy-card__title")
                        or card.select_one("[class*=vacancy][class*=title]")
                    )
                    if title_el:
                        title = title_el.get_text(strip=True)
                if not title:
                    title = card.get_text(strip=True)[:80]

                company = None
                for sel in [
                    "div.vacancy-card__company-title",
                    "a.vacancy-card__company-link",
                    "a[class*=company]",
                    "div[class*=company]",
                ]:
                    el = card.select_one(sel)
                    if el:
                        company = el.get_text(strip=True)
                        break

                salary_text = None
                salary_min = None
                salary_max = None
                for sel in [
                    "div.vacancy-card__price",
                    "span[class*=salary]",
                    "div[class*=salary]",
                    "[class*=price]",
                ]:
                    el = card.select_one(sel)
                    if el:
                        salary_text = el.get_text(strip=True)
                        salary_min, salary_max = extract_salary_numbers(salary_text)
                        break

                city_name = None
                emp_type = None
                emp_types = []
                exp_value = None
                _emp_type_kw = {"удаленно": "remote", "удаленная": "remote",
                                "полный": "full", "полная": "full",
                                "частичная": "part", "проект": "project",
                                "стажировка": "internship"}
                parts = []
                meta = card.select_one("div.vacancy-card__meta")
                if meta:
                    meta_text = meta.get_text(" ", strip=True)
                    parts = meta_text.split("•")
                    if parts:
                        candidate = parts[0].strip()
                        is_emp = any(k in candidate.lower() for k in _emp_type_kw)
                        if not is_emp:
                            city_name = candidate
                        else:
                            for key, val in _emp_type_kw.items():
                                if key in candidate.lower():
                                    emp_types.append(val)
                                    break
                    if len(parts) > 1:
                        for part in parts[1:]:
                            p = part.strip().lower()
                            for key, val in _emp_type_kw.items():
                                if key in p:
                                    emp_types.append(val)
                                    break
                emp_types = list(dict.fromkeys(emp_types))
                emp_type = "remote" if "remote" in emp_types else (emp_types[0] if emp_types else None)

                exp_el = card.select_one("[class*=experience]") or card.select_one("[class*=exp-]")
                if exp_el:
                    exp_text = exp_el.get_text(strip=True).lower()
                    if "без опыта" in exp_text and not re.search(r'\d+\s*(?:года|лет|год)', exp_text):
                        exp_value = "no"
                    else:
                        exp_years = re.findall(r'(\d+)\s*(?:года|лет|год)', exp_text)
                        if exp_years:
                            years = int(exp_years[0])
                            if years <= 1:
                                exp_value = "1-3"
                            elif years <= 3:
                                exp_value = "3-6"
                            else:
                                exp_value = "6+"
                if exp_value is None and len(parts) > 1:
                    for part in parts[1:]:
                        p = part.strip().lower()
                        if "без опыта" in p and not re.search(r'\d+\s*(?:года|лет|год)', p):
                            exp_value = "no"
                            break
                        elif "опыт" in p:
                            exp_years = re.findall(r'(\d+)\s*(?:года|лет|год)', p)
                            if exp_years:
                                years = int(exp_years[0])
                                if years <= 1:
                                    exp_value = "1-3"
                                elif years <= 3:
                                    exp_value = "3-6"
                                else:
                                    exp_value = "6+"
                                break

                skils = card.select_one("div.vacancy-card__skills")
                desc = skils.get_text(", ", strip=True) if skils else None

                published = None
                date_el = card.select_one("time[datetime]") or card.select_one("[class*=date]") or card.select_one("[class*=published]")
                if date_el:
                    date_str = date_el.get("datetime") or date_el.get_text(strip=True)
                    try:
                        published = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                    except (ValueError, TypeError):
                        pass

                results.append(VacancyData(
                    source="habr",
                    source_id=source_id,
                    title=title,
                    company=company,
                    salary_text=salary_text,
                    salary_min=salary_min,
                    salary_max=salary_max,
                    employment_type=emp_type,
                    employment_types=emp_types,
                    experience=exp_value,
                    city=city_name,
                    description=desc,
                    url=href,
                    published_at=published,
                ))
            except Exception:
                continue

        return results
