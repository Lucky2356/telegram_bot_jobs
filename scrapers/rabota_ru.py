import httpx
import re
from datetime import datetime
from bs4 import BeautifulSoup, Tag
from scrapers.base import BaseScraper, VacancyData


RABOTA_URL = "https://www.rabota.ru/vacancy/search"


class RabotaRuScraper(BaseScraper):
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0, follow_redirects=True, trust_env=False)

    async def close(self):
        await self.client.aclose()

    async def search(
        self, keywords: list[str], city: str | None = None
    ) -> list[VacancyData]:
        query = " ".join(keywords)
        params: dict = {"query": query}
        if city:
            params["city"] = city

        try:
            resp = await self.client.get(RABOTA_URL, params=params)
            resp.raise_for_status()
            return self._parse_html(resp.text)
        except Exception:
            return []

    def _parse_html(self, html: str) -> list[VacancyData]:
        results: list[VacancyData] = []
        soup = BeautifulSoup(html, "lxml")

        cards = (
            soup.select("div.vacancy-preview-card")
            or soup.select("[data-qa*='vacancy']")
            or soup.select("article")
            or soup.select("div[class*=card][class*=vacancy]")
            or soup.select("div[class*=item][class*=vacancy]")
        )
        if not cards:
            cards = soup.find_all("div", class_=re.compile(r"(vacancy|card|item)", re.I))

        seen = set()
        for card in cards:
            try:
                link_tag = (
                    card.select_one("a[href*='/vacancy']")
                    or card.select_one("a[href*='/vakansiya']")
                    or card.find("a", href=True)
                )
                if not link_tag:
                    continue
                href = link_tag.get("href", "")
                if not href.startswith("http"):
                    href = "https://rabota.ru" + href

                source_id = href.split("/")[-1] or href
                if source_id in seen:
                    continue
                seen.add(source_id)

                title = link_tag.get_text(strip=True) or ""
                company = None
                for sel in [
                    "span[class*=company]", "div[class*=company]",
                    "a[class*=company]", "[data-qa*=company]",
                    "div[class*=employer]",
                ]:
                    el = card.select_one(sel)
                    if el:
                        company = el.get_text(strip=True)
                        break

                salary_text = None
                for sel in [
                    "div[class*=salary]", "span[class*=salary]",
                    "div[class*=price]", "[data-qa*=salary]",
                ]:
                    el = card.select_one(sel)
                    if el:
                        salary_text = el.get_text(strip=True)
                        break

                city_name = None
                for sel in [
                    "span[class*=city]", "span[class*=metro]",
                    "div[class*=location]", "[data-qa*=city]",
                ]:
                    el = card.select_one(sel)
                    if el:
                        city_name = el.get_text(strip=True)
                        break

                emp_type = self._detect_employment_type(card.get_text(" "))

                desc = None
                desc_el = card.select_one("div[class*=description], p[class*=desc], [data-qa*=snippet]")
                if desc_el:
                    desc = desc_el.get_text(strip=True)

                results.append(VacancyData(
                    source="rabota",
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

    def _detect_employment_type(self, text: str) -> str | None:
        text_lower = text.lower()
        if "удален" in text_lower or "дистанци" in text_lower:
            return "remote"
        if "частич" in text_lower or "неполн" in text_lower:
            return "part"
        if "проект" in text_lower:
            return "project"
        if "стажировк" in text_lower:
            return "internship"
        if "полн" in text_lower:
            return "full"
        return None
