from dataclasses import dataclass
from datetime import datetime
from abc import ABC, abstractmethod


@dataclass
class VacancyData:
    source: str
    source_id: str
    title: str
    company: str | None = None
    salary_text: str | None = None
    salary_min: int | None = None
    salary_max: int | None = None
    employment_type: str | None = None
    employment_types: list[str] | None = None
    experience: str | None = None
    city: str | None = None
    description: str | None = None
    url: str = ""
    published_at: datetime | None = None


class BaseScraper(ABC):
    @abstractmethod
    async def search(
        self, keywords: list[str], city: str | None = None
    ) -> list[VacancyData]:
        pass

    @abstractmethod
    async def close(self):
        """Close any network sessions, cleanup resources."""
        pass
