import httpx
from datetime import datetime
from scrapers.base import BaseScraper, VacancyData


HH_API = "https://api.hh.ru/vacancies"

CITY_IDS: dict[str, int] = {
    "moscow": 1,
    "spb": 2,
    "kazan": 88,
    "novosibirsk": 4,
    "ekb": 3,
    "krasnodar": 53,
    "nnovgorod": 66,
    "rostov": 76,
}


class HHScraper(BaseScraper):
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0, trust_env=False)

    async def close(self):
        await self.client.aclose()

    async def search(
        self, keywords: list[str], city: str | None = None
    ) -> list[VacancyData]:
        query = " ".join(keywords)
        params: dict = {
            "text": query,
            "per_page": 50,
            "page": 0,
            "search_field": "name",
            "order_by": "publication_time",
        }
        if city and city in CITY_IDS:
            params["area"] = CITY_IDS[city]

        try:
            resp = await self.client.get(HH_API, params=params)
            resp.raise_for_status()
            data = resp.json()
        except Exception:
            return []

        results: list[VacancyData] = []
        for item in data.get("items", []):
            salary_text = None
            salary = item.get("salary")
            if salary:
                parts = []
                if salary.get("from"):
                    parts.append(f"от {salary['from']:,}".replace(",", " "))
                if salary.get("to"):
                    parts.append(f"до {salary['to']:,}".replace(",", " "))
                cur = salary.get("currency", "").upper()
                if parts:
                    salary_text = " ".join(parts) + f" {cur}"

            emp_type = None
            employment = item.get("employment")
            if employment:
                emp_id = employment.get("id")
                mapping = {
                    "full": "full",
                    "part": "part",
                    "project": "project",
                    "probation": "internship",
                    "volunteer": "internship",
                }
                emp_type = mapping.get(emp_id)

            schedule = item.get("schedule")
            if schedule and schedule.get("id") == "remote":
                emp_type = "remote"

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

            results.append(VacancyData(
                source="hh",
                source_id=str(item["id"]),
                title=item.get("name", ""),
                company=item.get("employer", {}).get("name") if item.get("employer") else None,
                salary_text=salary_text,
                employment_type=emp_type,
                city=city_name,
                description=". ".join(filter(None, [
                    item.get("snippet", {}).get("requirement", ""),
                    item.get("snippet", {}).get("responsibility", ""),
                ])) if item.get("snippet") else None,
                url=item.get("alternate_url", ""),
                published_at=published,
            ))

        return results
