import httpx
import xml.etree.ElementTree as ET
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
        params: dict = {
            "keyword": query,
            "offset": 0,
            "limit": 100,
        }

        try:
            resp = await self.client.get(TRUDVSEM_API, params=params)
            resp.raise_for_status()
            return self._parse_xml(resp.text, city)
        except Exception:
            return []

    def _parse_xml(self, xml_text: str, city_filter: str | None) -> list[VacancyData]:
        results: list[VacancyData] = []
        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError:
            return []

        ns = {"": "http://opendata.trudvsem.ru/opendata/trudvsem"}
        for vacancy_elem in root.iter("vacancy"):
            try:
                data = {}
                for child in vacancy_elem:
                    data[child.tag] = child.text or ""

                city = data.get("location", "")
                if city_filter and city_filter.lower() not in city.lower():
                    continue

                salary_text = None
                salary = data.get("salary", "")
                if salary:
                    salary_text = f"{salary} ₽"
                salary_min = data.get("salary_min")
                salary_max = data.get("salary_max")
                if salary_min or salary_max:
                    parts = []
                    if salary_min:
                        parts.append(f"от {salary_min}")
                    if salary_max:
                        parts.append(f"до {salary_max}")
                    salary_text = " ".join(parts) + " ₽"

                emp_type = None
                emp = data.get("employment", "")
                mapping = {
                    "Полная занятость": "full",
                    "Частичная": "part",
                    "Дистанционная": "remote",
                    "Вахтовый метод": "full",
                    "Стажировка": "internship",
                }
                emp_type = mapping.get(emp)

                published = None
                try:
                    date_str = data.get("creation_date", "")
                    if date_str:
                        published = datetime.fromisoformat(date_str)
                except Exception:
                    pass

                results.append(VacancyData(
                    source="trudvsem",
                    source_id=data.get("id", data.get("vacancy_url", "")),
                    title=data.get("job_name", ""),
                    company=data.get("company_name", "").replace("\n", " ").strip(),
                    salary_text=salary_text,
                    employment_type=emp_type,
                    city=data.get("location", "").replace("\n", " ").strip(),
                    description=data.get("duty", "").replace("\n", " ").strip(),
                    url=data.get("vacancy_url", ""),
                    published_at=published,
                ))
            except Exception:
                continue

        return results
