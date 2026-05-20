import httpx
from datetime import datetime
from scrapers.base import BaseScraper, VacancyData
from core.config import settings


SJ_API = "https://api.superjob.ru/2.0/vacancies/"
SJ_HEADERS = {"X-Api-App-Id": settings.SUPERJOB_API_KEY}


class SuperJobScraper(BaseScraper):
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0, headers=SJ_HEADERS, trust_env=False)

    async def close(self):
        await self.client.aclose()

    async def search(
        self, keywords: list[str], city: str | None = None
    ) -> list[VacancyData]:
        if not settings.SUPERJOB_API_KEY:
            return []

        query = " ".join(keywords)
        params: dict = {
            "keyword": query,
            "count": 50,
            "page": 0,
        }
        if city:
            params["town"] = city

        try:
            resp = await self.client.get(SJ_API, params=params)
            resp.raise_for_status()
            data = resp.json()
        except Exception:
            return []

        results: list[VacancyData] = []
        for item in data.get("objects", []):
            salary_text = None
            payment_from = item.get("payment_from")
            payment_to = item.get("payment_to")
            currency = item.get("currency", "rub")
            if payment_from or payment_to:
                parts = []
                if payment_from:
                    parts.append(f"от {payment_from:,}".replace(",", " "))
                if payment_to:
                    parts.append(f"до {payment_to:,}".replace(",", " "))
                salary_text = " ".join(parts) + f" {currency.upper()}"

            emp_type = None
            tof = item.get("type_of_work", {})
            if tof:
                tid = tof.get("id")
                mapping = {
                    1: "full",
                    2: "part",
                    3: "project",
                    4: "part",
                    5: "part",
                    6: "remote",
                }
                emp_type = mapping.get(tid)

            emp_form = item.get("employment", {})
            if emp_form:
                eid = emp_form.get("id")
                emp_mapping = {
                    1: "full",
                    2: "part",
                    3: "project",
                    4: "internship",
                }
                if eid in emp_mapping:
                    emp_type = emp_mapping[eid]

            published = None
            if item.get("date_published"):
                try:
                    published = datetime.fromtimestamp(item["date_published"])
                except Exception:
                    pass

            exp = None
            sj_exp = item.get("experience", {})
            if sj_exp:
                eid = sj_exp.get("id")
                exp_map = {1: "no", 2: "1-3", 3: "3-6", 4: "6+"}
                exp = exp_map.get(eid)

            town = item.get("town", {})
            city_name = town.get("title") if town else None

            results.append(VacancyData(
                source="superjob",
                source_id=str(item["id"]),
                title=item.get("profession", ""),
                company=item.get("firm_name") or (
                    item.get("firm", {}).get("title") if item.get("firm") else None
                ),
                salary_text=salary_text,
                employment_type=emp_type,
                experience=exp,
                city=city_name,
                description=item.get("candidat"),
                url=item.get("link", ""),
                published_at=published,
            ))

        return results
