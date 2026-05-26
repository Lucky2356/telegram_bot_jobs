import httpx
from datetime import datetime
from scrapers.base import BaseScraper, VacancyData
from bot.keyboards import CITIES
from utils.text_cleaner import clean_html


TRUDVSEM_API = "https://opendata.trudvsem.ru/api/v1/vacancies"


class TrudvsemScraper(BaseScraper):
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0, trust_env=False)

    async def close(self):
        await self.client.aclose()

    async def search(self, keywords: list[str], city: str | None = None) -> list[VacancyData]:
        query = " ".join(keywords)
        results: list[VacancyData] = []

        for page in range(3):
            params: dict = {"keyword": query, "offset": page * 100, "limit": 100}
            if city:
                params["region"] = CITIES.get(city, city)
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
                    try:
                        smin_int = int(smin) if smin else None
                        smax_int = int(smax) if smax else None
                    except (ValueError, TypeError):
                        smin_int = smax_int = None
                    if (smin_int and smin_int != 0) or (smax_int and smax_int != 0):
                        parts = []
                        if smin_int and smin_int != 0:
                            parts.append(f"от {smin_int:,}".replace(",", " "))
                        if smax_int and smax_int != 0:
                            parts.append(f"до {smax_int:,}".replace(",", " "))
                        salary_text = " ".join(parts) + f" {salary_currency}"
                    elif v.get("salary"):
                        salary_text = f"{v['salary']} {salary_currency}"

                    emp_type = None
                    emp = v.get("employment", "")
                    mapping = {
                        "дистанционная": "remote", "удаленная": "remote", "удаленно": "remote",
                        "полная занятость": "full", "вахтовый метод": "full",
                        "частичная": "part",
                        "проект": "project",
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
                    desc = clean_html(" ".join(desc_parts).replace("\n", " ").strip())
                    vac_url = v.get("vac-url", "")

                    try:
                        sal_min_val = int(smin) if smin else None
                        sal_max_val = int(smax) if smax else None
                        if sal_min_val == 0:
                            sal_min_val = None
                        if sal_max_val == 0:
                            sal_max_val = None
                    except (ValueError, TypeError):
                        sal_min_val = None
                        sal_max_val = None

                    exp_value = None
                    min_exp = v.get("minExperience")
                    if min_exp is not None:
                        try:
                            exp_months = int(min_exp)
                            if exp_months <= 0:
                                exp_value = "no"
                            elif exp_months <= 12:
                                exp_value = "1-3"
                            elif exp_months <= 36:
                                exp_value = "3-6"
                            else:
                                exp_value = "6+"
                        except (ValueError, TypeError):
                            pass

                    results.append(VacancyData(
                        source="trudvsem",
                        source_id=v.get("id", vac_url) or vac_url or "trudvsem_unknown",
                        title=v.get("job-name", ""),
                        company=company_name,
                        salary_text=salary_text,
                        salary_min=sal_min_val,
                        salary_max=sal_max_val,
                        employment_type=emp_type,
                        experience=exp_value,
                        city=city_name,
                        description=desc,
                        url=vac_url,
                        published_at=published,
                    ))
                except Exception:
                    continue

        return results
