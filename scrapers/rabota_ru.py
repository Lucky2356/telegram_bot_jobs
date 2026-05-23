import re
import httpx
from datetime import datetime
from bs4 import BeautifulSoup
from scrapers.base import BaseScraper, VacancyData
from bot.keyboards import CITIES
from utils.text_cleaner import extract_salary_numbers, clean_html


RABOTA_URL = "https://www.rabota.ru/vacancy/search"


class RabotaRuScraper(BaseScraper):
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0, follow_redirects=True, trust_env=False)

    async def close(self):
        await self.client.aclose()

    async def search(self, keywords: list[str], city: str | None = None) -> list[VacancyData]:
        query = " ".join(keywords)
        results: list[VacancyData] = []
        seen: set = set()
        for page in range(1):
            params: dict = {"query": query}
            if city:
                params["city"] = CITIES.get(city, city)
            params["page"] = page
            try:
                resp = await self.client.get(RABOTA_URL, params=params)
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

        # Find all vacancy links with numeric IDs
        for link_tag in soup.find_all("a", href=True):
            href = link_tag.get("href", "")
            # Only accept links like /vacancy/123456/ or similar
            m = re.search(r"/vacancy/(\d+)", href)
            if not m:
                continue
            vacancy_id = m.group(1)
            if vacancy_id in {v.source_id for v in results}:
                continue

            if not href.startswith("http"):
                from urllib.parse import urljoin
                href = urljoin("https://rabota.ru", href)

            title = link_tag.get_text(strip=True) or link_tag.get("title", "")
            if not title:
                continue

            # Try to get company from nearby elements
            card = link_tag.find_parent(["div", "article"])
            company = None
            if card:
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
            salary_min = None
            salary_max = None
            if card:
                for sel in [
                    "div[class*=salary]", "span[class*=salary]",
                    "div[class*=price]", "[data-qa*=salary]",
                ]:
                    el = card.select_one(sel)
                    if el:
                        salary_text = el.get_text(strip=True)
                        salary_min, salary_max = extract_salary_numbers(salary_text)
                        break

            city_name = None
            if card:
                for sel in [
                    "span[class*=city]", "span[class*=metro]",
                    "div[class*=location]", "[data-qa*=city]",
                ]:
                    el = card.select_one(sel)
                    if el:
                        city_name = el.get_text(strip=True)
                        break

            emp_type = None
            exp_value = None
            desc_value = None
            if card:
                card_text = card.get_text(" ", strip=True)
                emp_type = self._detect_employment_type(card_text)
                exp_value = self._detect_experience(card_text)
                desc_el = card.select_one("[class*=description]") or card.select_one("[class*=desc]") or card.select_one("[data-qa*=vacancy-description]")
                if desc_el:
                    desc_value = clean_html(desc_el.get_text(strip=True))

            results.append(VacancyData(
                source="rabota",
                source_id=vacancy_id,
                title=title,
                company=company,
                salary_text=salary_text,
                salary_min=salary_min,
                salary_max=salary_max,
                employment_type=emp_type,
                experience=exp_value,
                city=city_name,
                description=desc_value,
                url=href,
            ))

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
        if "полный рабочий" in text_lower or "полная занятость" in text_lower or "полный день" in text_lower:
            return "full"
        return None

    def _detect_experience(self, text: str) -> str | None:
        text_lower = text.lower()
        if "без опыта" in text_lower:
            return "no"
        if "опыт" in text_lower:
            exp_years = re.findall(r'(?:от\s*)?(\d+)\s*(?:года|лет|год)', text_lower)
            if exp_years:
                years = int(exp_years[0])
                if years <= 1: return "1-3"
                if years <= 3: return "3-6"
                return "6+"
        return None
