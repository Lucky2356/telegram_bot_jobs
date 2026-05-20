import httpx
from datetime import datetime
from scrapers.base import BaseScraper, VacancyData


TRUDVSEM_API = "https://opendata.trudvsem.ru/api/v1/vacancies"


class TrudvsemScraper(BaseScraper):
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0, trust_env=False)

    async def close(self):
        await self.client.aclose()

    async def search(
        self, keywords: list[str], city: str | None = None
    ) -> list[VacancyData]:
        query = " ".join(keywords)
        params: dict = {"keyword": query, "offset": 0, "limit": 100}

        try:
            resp = await self.client.get(TRUDVSEM_API, params=params)
            resp.raise_for_status()
            data = resp.json()
        except Exception:
            return []

        results: list[VacancyData] = []
        vacancies = data.get("results", {}).get("vacancies", [])
        for item in vacancies:
            try:
                v = item.get("vacancy", {})
                if not v.get("job-name"):
                    continue

                city_name = None
                region = v.get("region")
                if region:
                    city_name = region.get("name", "").replace("\n", " ").strip()

                company_name = None
                company = v.get("company")
                if company:
                    company_name = company.get("name", "").replace("\n", " ").strip()

                salary_text = None
                salary_currency = v.get("currency", "RUB")
                smin = v.get("salary_min")
                smax = v.get("salary_max")
                if smin or smax:
                    parts = []
                    if smin:
                        parts.append(f"от {smin}")
                    if smax:
                        parts.append(f"до {smax}")
                    salary_text = " ".join(parts) + f" {salary_currency}"
                elif v.get("salary"):
                    salary_text = f"{v['salary']} {salary_currency}"

                emp_type = None
                emp = v.get("employment", "")
                mapping = {
                    "полная занятость": "full",
                    "частичная": "part",
                    "дистанционная": "remote",
                    "удаленно": "remote",
                    "удаленная": "remote",
                    "вахтовый метод": "full",
                    "стажировка": "internship",
                }
                if emp:
                    emp_lower = emp.lower()
                    for key, val in mapping.items():
                        if key in emp_lower:
                            emp_type = val
                            break

                published = None
                date_str = v.get("creation-date", "")
                if date_str:
                    try:
                        published = datetime.fromisoformat(date_str)
                    except Exception:
                        pass

                desc_parts = filter(None, [
                    v.get("duty", ""),
                    v.get("requirements", ""),
                ])
                desc = " ".join(desc_parts).replace("\n", " ").strip()

                vac_url = v.get("vac-url", "")

                results.append(VacancyData(
                    source="trudvsem",
                    source_id=v.get("id", vac_url or ""),
                    title=v.get("job-name", ""),
                    company=company_name,
                    salary_text=salary_text,
                    employment_type=emp_type,
                    city=city_name,
                    description=desc,
                    url=vac_url,
                    published_at=published,
                ))
            except Exception:
                continue

        return results
