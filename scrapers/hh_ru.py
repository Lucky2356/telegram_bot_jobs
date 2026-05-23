import httpx
from datetime import datetime, timedelta, timezone
from scrapers.base import BaseScraper, VacancyData
from core.config import settings
from utils.text_cleaner import clean_html


HH_API = "https://api.hh.ru/vacancies"
HH_TOKEN_URL = "https://api.hh.ru/token"

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
            headers={"User-Agent": "TelegramJobBot/1.0 (job-bot)"},
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
                    if emp_type not in ("remote", None):
                        # Both: remote schedule + employment type (e.g. full-time remote)
                        pass  # Keep employment type, remote is implied
                    else:
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

        return results
