import json
from datetime import datetime
from sqlalchemy import select, delete, func
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from core.database.models import Base, User, VacancyFilter, Vacancy, SentVacancy, SavedVacancy, Blocklist
from scrapers.base import VacancyData


class Database:
    def __init__(self, url: str):
        self.engine = create_async_engine(url, echo=False)
        self.session_factory = async_sessionmaker(self.engine, expire_on_commit=False)

    async def create_tables(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def get_or_create_user(self, telegram_id: int, username: str | None = None) -> User:
        async with self.session_factory() as session:
            result = await session.execute(select(User).where(User.telegram_id == telegram_id))
            user = result.scalar_one_or_none()
            if user is None:
                user = User(telegram_id=telegram_id, username=username)
                session.add(user)
                await session.commit()
                await session.refresh(user)
            elif username and user.username != username:
                user.username = username
                await session.commit()
            return user

    async def get_user_by_telegram_id(self, telegram_id: int) -> User | None:
        async with self.session_factory() as session:
            result = await session.execute(select(User).where(User.telegram_id == telegram_id))
            return result.scalar_one_or_none()

    async def get_user(self, user_id: int) -> User | None:
        async with self.session_factory() as session:
            result = await session.execute(select(User).where(User.id == user_id))
            return result.scalar_one_or_none()

    async def create_filter(
        self, user_id: int, name: str, keywords: list[str],
        city: str | None, salary_min: int | None,
        salary_max: int | None, employment_types: list[str],
        sites: list[str], exclude_keywords: list[str] | None = None,
    ) -> VacancyFilter:
        async with self.session_factory() as session:
            vf = VacancyFilter(
                user_id=user_id,
                name=name,
                keywords=json.dumps(keywords, ensure_ascii=False),
                city=city,
                salary_min=salary_min,
                salary_max=salary_max,
                employment_types=json.dumps(employment_types, ensure_ascii=False),
                sites=json.dumps(sites, ensure_ascii=False),
                exclude_keywords=json.dumps(exclude_keywords or [], ensure_ascii=False),
            )
            session.add(vf)
            await session.commit()
            await session.refresh(vf)
            return vf

    async def get_user_filters(self, user_id: int) -> list[VacancyFilter]:
        async with self.session_factory() as session:
            result = await session.execute(
                select(VacancyFilter)
                .where(VacancyFilter.user_id == user_id)
                .order_by(VacancyFilter.created_at.desc())
            )
            return list(result.scalars().all())

    async def get_filter(self, filter_id: int) -> VacancyFilter | None:
        async with self.session_factory() as session:
            result = await session.execute(
                select(VacancyFilter).where(VacancyFilter.id == filter_id)
            )
            return result.scalar_one_or_none()

    async def toggle_filter(self, filter_id: int) -> bool:
        async with self.session_factory() as session:
            result = await session.execute(
                select(VacancyFilter).where(VacancyFilter.id == filter_id)
            )
            vf = result.scalar_one_or_none()
            if vf is None:
                return False
            vf.active = not vf.active
            await session.commit()
            return vf.active

    async def delete_filter(self, filter_id: int):
        async with self.session_factory() as session:
            await session.execute(delete(VacancyFilter).where(VacancyFilter.id == filter_id))
            await session.commit()

    async def update_filter(
        self, filter_id: int, name: str,
        keywords: list[str], city: str | None,
        salary_min: int | None, salary_max: int | None,
        employment_types: list[str], sites: list[str],
        exclude_keywords: list[str] | None = None,
    ) -> VacancyFilter | None:
        async with self.session_factory() as session:
            result = await session.execute(
                select(VacancyFilter).where(VacancyFilter.id == filter_id)
            )
            vf = result.scalar_one_or_none()
            if vf is None:
                return None
            vf.name = name
            vf.set_keywords(keywords)
            vf.city = city
            vf.salary_min = salary_min
            vf.salary_max = salary_max
            vf.set_employment_types(employment_types)
            vf.set_sites(sites)
            if exclude_keywords is not None:
                vf.set_exclude_keywords(exclude_keywords)
            await session.commit()
            await session.refresh(vf)
            return vf

    async def get_all_active_filters(self) -> list[VacancyFilter]:
        async with self.session_factory() as session:
            result = await session.execute(
                select(VacancyFilter).where(VacancyFilter.active == True)
            )
            return list(result.scalars().all())

    async def add_vacancy(self, data: VacancyData) -> Vacancy | None:
        async with self.session_factory() as session:
            result = await session.execute(
                select(Vacancy).where(
                    Vacancy.source == data.source,
                    Vacancy.source_id == data.source_id,
                )
            )
            existing = result.scalar_one_or_none()
            if existing:
                return None
            vac = Vacancy(
                source=data.source,
                source_id=data.source_id,
                title=data.title,
                company=data.company,
                salary_text=data.salary_text,
                employment_type=data.employment_type,
                city=data.city,
                description=data.description,
                url=data.url,
                published_at=data.published_at,
            )
            session.add(vac)
            await session.commit()
            await session.refresh(vac)
            return vac

    async def is_sent(self, user_id: int, vacancy_id: int) -> bool:
        async with self.session_factory() as session:
            result = await session.execute(
                select(SentVacancy).where(
                    SentVacancy.user_id == user_id,
                    SentVacancy.vacancy_id == vacancy_id,
                )
            )
            return result.scalar_one_or_none() is not None

    async def mark_sent(self, user_id: int, vacancy_id: int):
        async with self.session_factory() as session:
            session.add(SentVacancy(user_id=user_id, vacancy_id=vacancy_id))
            await session.commit()

    async def get_filter_count(self) -> int:
        async with self.session_factory() as session:
            result = await session.execute(select(func.count(VacancyFilter.id)))
            return result.scalar()

    async def add_blocklist(self, user_id: int, pattern: str, type: str = "company"):
        async with self.session_factory() as session:
            exists = await session.execute(
                select(Blocklist).where(
                    Blocklist.user_id == user_id,
                    Blocklist.pattern == pattern,
                    Blocklist.type == type,
                )
            )
            if exists.scalar_one_or_none() is None:
                session.add(Blocklist(user_id=user_id, pattern=pattern, type=type))
                await session.commit()

    async def is_blocked(self, user_id: int, company: str | None, title: str) -> bool:
        if not company:
            return False
        async with self.session_factory() as session:
            blocks = await session.execute(
                select(Blocklist).where(Blocklist.user_id == user_id)
            )
            for b in blocks.scalars().all():
                if b.pattern.lower() in (company or "").lower():
                    return True
                if b.pattern.lower() in title.lower():
                    return True
        return False

    async def save_vacancy(self, user_id: int, vacancy_id: int):
        async with self.session_factory() as session:
            exists = await session.execute(
                select(SavedVacancy).where(
                    SavedVacancy.user_id == user_id,
                    SavedVacancy.vacancy_id == vacancy_id,
                )
            )
            if exists.scalar_one_or_none() is None:
                session.add(SavedVacancy(user_id=user_id, vacancy_id=vacancy_id))
                await session.commit()

    async def get_recent_sent(self, limit: int = 20) -> list[tuple[SentVacancy, Vacancy, User]]:
        async with self.session_factory() as session:
            stmt = (
                select(SentVacancy, Vacancy, User)
                .join(Vacancy, SentVacancy.vacancy_id == Vacancy.id)
                .join(User, SentVacancy.user_id == User.id)
                .order_by(SentVacancy.sent_at.desc())
                .limit(limit)
            )
            result = await session.execute(stmt)
            return list(result.all())
