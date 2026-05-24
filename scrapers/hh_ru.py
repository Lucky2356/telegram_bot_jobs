import re
import httpx
from datetime import datetime, timedelta, timezone
from bs4 import BeautifulSoup
from scrapers.base import BaseScraper, VacancyData
from core.config import settings
from utils.text_cleaner import clean_html, extract_salary_numbers


HH_API = "https://api.hh.ru/vacancies"
HH_TOKEN_URL = "https://api.hh.ru/token"
HH_SEARCH_URL = "https://hh.ru/search/vacancy"

CITY_IDS: dict[str, int] = {
    "moscow": 1, "spb": 2, "kazan": 88, "novosibirsk": 4,
    "ekb": 3, "krasnodar": 53, "nnovgorod": 66, "rostov": 76,
}


class HHScraper(BaseScraper):
    def __init__(self):
        self._token: str | None = None
        self._token_expires: datetime | None = None
        self.client = httpx.AsyncClient(
            timeout=30.0, trust_env=False,
            headers={
                "User-Agent": settings.HH_USER_AGENT,
                "HH-User-Agent": settings.HH_USER_AGENT,
            },
        )

    async def close(self):
        await self.client.aclose()

    async def _ensure_token(self):
        if not settings.HH_CLIENT_ID or not settings.HH_CLIENT_SECRET:
            return
        if self._token and self._token_expires and datetime.now(timezone.utc) < self._token_expires:
            return
        try:
            resp = await self.client.post(
                HH_TOKEN_URL,
                data={
                    "grant_type": "client_credentials",
                    "client_id": settings.HH_CLIENT_ID,
                    "client_secret": settings.HH_CLIENT_SECRET,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            self._token = data.get("access_token")
            expires_in = data.get("expires_in", 3600)
            self._token_expires = datetime.now(timezone.utc) + timedelta(seconds=expires_in - 60)
        except Exception:
            self._token = None
            self._token_expires = None

    async def search(self, keywords: list[str], city: str | None = None) -> list[VacancyData]:
        await self._ensure_token()
        query = " ".join(keywords)
        headers = {}
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"

        results: list[VacancyData] = []
        max_pages = 3
        base_params = {"text": query, "per_page": 50, "search_field": "name", "order_by": "publication_time"}
        if city:
            import logging
            logger = logging.getLogger(__name__)
            if city in CITY_IDS:
                base_params["area"] = CITY_IDS[city]
            else:
                logger.warning("Unrecognized city key for hh.ru: %s, searching all regions", city)

        for page in range(max_pages):
            params = {**base_params, "page": page}
            try:
                resp = await self.client.get(HH_API, params=params, headers=headers)
                resp.raise_for_status()
                data = resp.json()
            except Exception:
                break

            if not isinstance(data, dict):
                logger = logging.getLogger(__name__)
                logger.warning("hh.ru returned non-dict response: %s", type(data).__name__)
                break

            for item in data.get("items", []):
                salary_text = None
                salary_min = None
                salary_max = None
                salary = item.get("salary")
                if salary:
                    salary_min = salary.get("from")
                    salary_max = salary.get("to")
                    if salary_min == 0:
                        salary_min = None
                    if salary_max == 0:
                        salary_max = None
                    parts = []
                    if salary_min:
                        parts.append(f"от {salary_min:,}".replace(",", " "))
                    if salary_max:
                        parts.append(f"до {salary_max:,}".replace(",", " "))
                    cur = salary.get("currency", "").upper()
                    if parts:
                        salary_text = " ".join(parts) + f" {cur}"

                emp_type = None
                employment = item.get("employment")
                if employment:
                    emp_id = employment.get("id")
                    mapping = {"full": "full", "part": "part", "project": "project",
                               "probation": "internship", "volunteer": "internship",
                               "temporary": "project"}
                    emp_type = mapping.get(emp_id)

                schedule = item.get("schedule")
                if schedule and schedule.get("id") == "remote":
                    emp_type = "remote"

                exp = None
                experience = item.get("experience")
                if experience:
                    exp = {"noExperience": "no", "between1And3": "1-3",
                           "between3And6": "3-6", "moreThan6": "6+"}.get(experience.get("id"))

                published = None
                if item.get("published_at"):
                    try:
                        published = datetime.fromisoformat(item["published_at"].replace("Z", "+00:00"))
                    except Exception:
                        pass

                city_name = None
                area = item.get("area")
                if area:
                    city_name = area.get("name")

                snippet = item.get("snippet", {}) or {}
                desc = clean_html(". ".join(filter(None, [snippet.get("requirement", ""), snippet.get("responsibility", "")])))

                results.append(VacancyData(
                    source="hh", source_id=str(item["id"]), title=item.get("name", ""),
                    company=item.get("employer", {}).get("name") if item.get("employer") else None,
                    salary_text=salary_text, salary_min=salary_min, salary_max=salary_max,
                    employment_type=emp_type, experience=exp, city=city_name,
                    description=desc, url=item.get("alternate_url", ""), published_at=published,
                ))

        return results or await self._search_html(query, city)

    async def _search_html(self, query: str, city: str | None = None) -> list[VacancyData]:
        results: list[VacancyData] = []
        seen: set[str] = set()
        base_params: dict = {"text": query, "search_field": "name"}
        if city and city in CITY_IDS:
            base_params["area"] = CITY_IDS[city]

        for page in range(3):
            params = {**base_params, "page": page}
            try:
                resp = await self.client.get(HH_SEARCH_URL, params=params)
                resp.raise_for_status()
            except Exception:
                break

            soup = BeautifulSoup(resp.text, "lxml")
            cards = soup.select('[data-qa="vacancy-serp__vacancy"]')
            if not cards:
                break

            for card in cards:
                title_link = card.select_one('a[data-qa="serp-item__title"]')
                if not title_link:
                    continue
                href = title_link.get("href", "")
                vacancy_id_match = re.search(r"/vacancy/(\d+)", href)
                source_id = vacancy_id_match.group(1) if vacancy_id_match else href
                if not source_id or source_id in seen:
                    continue
                seen.add(source_id)

                title = title_link.get_text(" ", strip=True)
                company_el = (
                    card.select_one('[data-qa="vacancy-serp__vacancy-employer-text"]')
                    or card.select_one('[data-qa="vacancy-serp__vacancy-employer"]')
                )
                city_el = card.select_one('[data-qa="vacancy-serp__vacancy-address"]')
                text = card.get_text(" ", strip=True)
                salary_text = self._extract_html_salary(text)
                salary_min, salary_max = extract_salary_numbers(salary_text or "")

                results.append(VacancyData(
                    source="hh",
                    source_id=source_id,
                    title=title,
                    company=company_el.get_text(" ", strip=True) if company_el else None,
                    salary_text=salary_text,
                    salary_min=salary_min,
                    salary_max=salary_max,
                    employment_type=self._detect_html_employment(text),
                    experience=self._detect_html_experience(text),
                    city=city_el.get_text(" ", strip=True) if city_el else None,
                    description=clean_html(text),
                    url=href,
                ))

        return results

    def _extract_html_salary(self, text: str) -> str | None:
        match = re.search(r"(\d[\d\s\u202f]*(?:\s*[–-]\s*\d[\d\s\u202f]*)?\s*₽)", text)
        if not match:
            return None
        return re.sub(r"\s+", " ", match.group(1).replace("\u202f", " ")).strip()

    def _detect_html_employment(self, text: str) -> str | None:
        text_lower = text.casefold()
        if "удал" in text_lower or "дистанц" in text_lower:
            return "remote"
        if "частич" in text_lower:
            return "part"
        if "стаж" in text_lower:
            return "internship"
        return None

    def _detect_html_experience(self, text: str) -> str | None:
        text_lower = text.casefold()
        if "без опыта" in text_lower:
            return "no"
        if "1" in text_lower and "3" in text_lower and "опыт" in text_lower:
            return "1-3"
        if "3" in text_lower and "6" in text_lower and "опыт" in text_lower:
            return "3-6"
        if "6" in text_lower and "опыт" in text_lower:
            return "6+"
        return None
