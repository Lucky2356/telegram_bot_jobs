import httpx
import re
from datetime import datetime
from bs4 import BeautifulSoup
from scrapers.base import BaseScraper, VacancyData


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
                params["city"] = city
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

                source_id = href.split("/")[-1] or href.split("/")[-2] if href else href

                title = ""
                title_el = card.select_one("[class*=title]")
                if title_el:
                    title = title_el.get_text(strip=True)
                if not title:
                    title = link_tag.get_text(strip=True) or card.get_text(strip=True)[:80]

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
                for sel in [
                    "div.vacancy-card__price",
                    "span[class*=salary]",
                    "div[class*=salary]",
                    "[class*=price]",
                ]:
                    el = card.select_one(sel)
                    if el:
                        salary_text = el.get_text(strip=True)
                        break

                city_name = None
                emp_type = None
                meta = card.select_one("div.vacancy-card__meta")
                if meta:
                    meta_text = meta.get_text(" ", strip=True)
                    parts = meta_text.split("•")
                    if parts:
                        city_name = parts[0].strip()
                    emp_part = parts[-1].strip() if len(parts) > 1 else None
                    if emp_part:
                        emp_type_mapping = {
                            "удаленно": "remote",
                            "удаленная": "remote",
                            "полный": "full",
                            "полная": "full",
                            "частичная": "part",
                            "проект": "project",
                            "стажировка": "internship",
                        }
                        for key, val in emp_type_mapping.items():
                            if key in emp_part.lower():
                                emp_type = val
                                break

                skils = card.select_one("div.vacancy-card__skills")
                desc = skils.get_text(", ", strip=True) if skils else None

                results.append(VacancyData(
                    source="habr",
                    source_id=source_id,
                    title=title,
                    company=company,
                    salary_text=salary_text,
                    employment_type=emp_type,
                    city=city_name,
                    description=desc,
                    url=href,
                ))
            except Exception:
                continue

        return results
