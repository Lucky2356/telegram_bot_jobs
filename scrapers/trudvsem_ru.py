import httpx
from datetime import datetime
from scrapers.base import BaseScraper, VacancyData


TRUDVSEM_API = "https://opendata.trudvsem.ru/api/v1/vacancies"


class TrudvsemScraper(BaseScraper):
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0, trust_env=False)

    async def close(self):
        await self.client.aclose()

    async def search(self, keywords: list[str], city: str | None = None) -> list[VacancyData]:
        query = " ".join(keywords)
        results: list[VacancyData] = []

        for page in range(1):
            params: dict = {"keyword": query, "offset": page * 100, "limit": 100}
            try:
                resp = await self.client.get(TRUDVSEM_API, params=params)
                resp.raise_for_status()
                data = resp.json()
            except Exception:
                break

            for item in data.get("results", {}).get("vacancies", []):
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
                        "полная занятость": "full", "частичная": "part",
                        "дистанционная": "remote", "удаленно": "remote",
                        "удаленная": "remote", "вахтовый метод": "full",
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
                        v.get("duty", ""), v.get("requirements", ""),
                        v.get("qualification", ""), v.get("skills", ""),
                    ])
                    desc = " ".join(desc_parts).replace("\n", " ").strip()
                    vac_url = v.get("vac-url", "")

                    try:
                        sal_min_val = int(smin) if smin else None
                        sal_max_val = int(smax) if smax else None
                    except (ValueError, TypeError):
                        sal_min_val = None
                        sal_max_val = None

                    results.append(VacancyData(
                        source="trudvsem",
                        source_id=v.get("id", vac_url or ""),
                        title=v.get("job-name", ""),
                        company=company_name,
                        salary_text=salary_text,
                        salary_min=sal_min_val,
                        salary_max=sal_max_val,
                        employment_type=emp_type,
                        city=city_name,
                        description=desc,
                        url=vac_url,
                        published_at=published,
                    ))
                except Exception:
                    continue

        return results
