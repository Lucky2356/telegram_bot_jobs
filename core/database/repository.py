import json
from datetime import datetime, timezone
from sqlalchemy import select, delete, func, update
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

    async def get_first_real_user(self) -> User | None:
        async with self.session_factory() as session:
            result = await session.execute(
                select(User)
                .where(User.telegram_id != 0)
                .order_by(User.created_at.asc())
                .limit(1)
            )
            return result.scalar_one_or_none()

    async def merge_user_data(self, source_user_id: int, target_user_id: int):
        if source_user_id == target_user_id:
            return
        async with self.session_factory() as session:
            source = await session.get(User, source_user_id)
            target = await session.get(User, target_user_id)
            if source is None or target is None:
                return

            await session.execute(
                update(VacancyFilter)
                .where(VacancyFilter.user_id == source_user_id)
                .values(user_id=target_user_id)
            )

            source_blocks = (
                await session.execute(select(Blocklist).where(Blocklist.user_id == source_user_id))
            ).scalars().all()
            for block in source_blocks:
                exists = await session.execute(
                    select(Blocklist.id).where(
                        Blocklist.user_id == target_user_id,
                        Blocklist.pattern == block.pattern,
                        Blocklist.type == block.type,
                    )
                )
                if exists.scalar_one_or_none():
                    await session.delete(block)
                else:
                    block.user_id = target_user_id

            source_saved = (
                await session.execute(select(SavedVacancy).where(SavedVacancy.user_id == source_user_id))
            ).scalars().all()
            for saved in source_saved:
                exists = await session.execute(
                    select(SavedVacancy.id).where(
                        SavedVacancy.user_id == target_user_id,
                        SavedVacancy.vacancy_id == saved.vacancy_id,
                    )
                )
                if exists.scalar_one_or_none():
                    await session.delete(saved)
                else:
                    saved.user_id = target_user_id

            source_sent = (
                await session.execute(select(SentVacancy).where(SentVacancy.user_id == source_user_id))
            ).scalars().all()
            for sent in source_sent:
                exists = await session.execute(
                    select(SentVacancy.id).where(
                        SentVacancy.user_id == target_user_id,
                        SentVacancy.vacancy_id == sent.vacancy_id,
                        SentVacancy.filter_id == sent.filter_id,
                    )
                )
                if exists.scalar_one_or_none():
                    await session.delete(sent)
                else:
                    sent.user_id = target_user_id

            await session.commit()

    async def create_filter(
        self, user_id: int, name: str, keywords: list[str],
        city: str | None, salary_min: int | None,
        salary_max: int | None, employment_types: list[str],
        sites: list[str], exclude_keywords: list[str] | None = None,
        experience: str | None = None,
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
                experience=experience,
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
        experience: str | None = None,
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
            vf.set_exclude_keywords(exclude_keywords or [])
            vf.experience = experience
            await session.commit()
            await session.refresh(vf)
            return vf

    async def get_all_active_filters(self) -> list[VacancyFilter]:
        async with self.session_factory() as session:
            result = await session.execute(
                select(VacancyFilter).where(VacancyFilter.active == True)
            )
            return list(result.scalars().all())

    async def get_all_filters(self) -> list[VacancyFilter]:
        async with self.session_factory() as session:
            result = await session.execute(
                select(VacancyFilter).order_by(VacancyFilter.created_at.desc())
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
                experience=data.experience,
                city=data.city,
                description=data.description,
                url=data.url,
                published_at=data.published_at,
            )
            session.add(vac)
            await session.commit()
            await session.refresh(vac)
            return vac

    async def get_vacancy_by_source(self, source: str, source_id: str) -> Vacancy | None:
        async with self.session_factory() as session:
            result = await session.execute(
                select(Vacancy).where(
                    Vacancy.source == source,
                    Vacancy.source_id == source_id,
                )
            )
            return result.scalar_one_or_none()

    async def is_sent(self, user_id: int, vacancy_id: int) -> bool:
        async with self.session_factory() as session:
            result = await session.execute(
                select(SentVacancy).where(
                    SentVacancy.user_id == user_id,
                    SentVacancy.vacancy_id == vacancy_id,
                )
            )
            return result.scalar_one_or_none() is not None

    async def mark_sent(self, user_id: int, vacancy_id: int, filter_id: int | None = None):
        async with self.session_factory() as session:
            session.add(SentVacancy(user_id=user_id, vacancy_id=vacancy_id, filter_id=filter_id))
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
        async with self.session_factory() as session:
            blocks = await session.execute(
                select(Blocklist).where(Blocklist.user_id == user_id)
            )
            for b in blocks.scalars().all():
                pattern = b.pattern.strip().lower()
                if not pattern:
                    continue
                if b.type == "company" and company and pattern in company.lower():
                    return True
                if b.type == "keyword" and pattern in title.lower():
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

    async def get_active_filter_count(self) -> int:
        async with self.session_factory() as session:
            result = await session.execute(
                select(func.count(VacancyFilter.id)).where(VacancyFilter.active == True)
            )
            return result.scalar() or 0

    async def get_total_vacancy_count(self) -> int:
        async with self.session_factory() as session:
            result = await session.execute(select(func.count(Vacancy.id)))
            return result.scalar() or 0

    async def get_total_sent_count(self) -> int:
        async with self.session_factory() as session:
            result = await session.execute(select(func.count(SentVacancy.id)))
            return result.scalar() or 0

    async def get_sent_by_source(self) -> dict[str, int]:
        async with self.session_factory() as session:
            result = await session.execute(
                select(Vacancy.source, func.count(Vacancy.id))
                .select_from(SentVacancy)
                .join(Vacancy, SentVacancy.vacancy_id == Vacancy.id)
                .group_by(Vacancy.source)
            )
            return dict(result.all())

    async def get_sent_by_day(self, days: int = 30) -> list[dict]:
        async with self.session_factory() as session:
            from datetime import datetime, timezone, timedelta
            cutoff = datetime.now(timezone.utc) - timedelta(days=days)
            result = await session.execute(
                select(
                    func.date(SentVacancy.sent_at).label("date"),
                    func.count(SentVacancy.id).label("count"),
                )
                .where(SentVacancy.sent_at >= cutoff)
                .group_by(func.date(SentVacancy.sent_at))
                .order_by("date")
            )
            return [{"date": str(row[0]), "count": row[1]} for row in result.all()]

    async def get_saved_vacancies(self, user_id: int | None = None) -> list[tuple[SavedVacancy, Vacancy]]:
        async with self.session_factory() as session:
            stmt = (
                select(SavedVacancy, Vacancy)
                .join(Vacancy, SavedVacancy.vacancy_id == Vacancy.id)
            )
            if user_id is not None:
                stmt = stmt.where(SavedVacancy.user_id == user_id)
            stmt = stmt.order_by(SavedVacancy.saved_at.desc()).limit(50)
            result = await session.execute(
                stmt
            )
            return list(result.all())

    async def get_blocklist(self, user_id: int | None = None) -> list[Blocklist]:
        async with self.session_factory() as session:
            stmt = select(Blocklist)
            if user_id is not None:
                stmt = stmt.where(Blocklist.user_id == user_id)
            result = await session.execute(stmt.order_by(Blocklist.type, Blocklist.pattern))
            return list(result.scalars().all())

    async def get_vacancy_by_id(self, vacancy_id: int) -> Vacancy | None:
        async with self.session_factory() as session:
            result = await session.execute(
                select(Vacancy).where(Vacancy.id == vacancy_id)
            )
            return result.scalar_one_or_none()

    async def unsave_vacancy(self, user_id: int, vacancy_id: int):
        async with self.session_factory() as session:
            await session.execute(
                delete(SavedVacancy).where(
                    SavedVacancy.user_id == user_id,
                    SavedVacancy.vacancy_id == vacancy_id,
                )
            )
            await session.commit()

    async def get_saved_vacancy_by_id(self, saved_id: int) -> SavedVacancy | None:
        async with self.session_factory() as session:
            result = await session.execute(
                select(SavedVacancy).where(SavedVacancy.id == saved_id)
            )
            return result.scalar_one_or_none()

    async def remove_blocklist_by_id(self, block_id: int):
        async with self.session_factory() as session:
            await session.execute(delete(Blocklist).where(Blocklist.id == block_id))
            await session.commit()

    async def cleanup_old_vacancies(self, days: int = 7):
        from datetime import datetime, timezone, timedelta
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        async with self.session_factory() as session:
            # Get IDs of old vacancies
            old = await session.execute(
                select(Vacancy.id).where(Vacancy.created_at < cutoff)
            )
            old_ids = [row[0] for row in old.all()]
            if not old_ids:
                return
            # Delete cascade
            await session.execute(
                delete(SentVacancy).where(SentVacancy.vacancy_id.in_(old_ids))
            )
            await session.execute(
                delete(SavedVacancy).where(SavedVacancy.vacancy_id.in_(old_ids))
            )
            await session.execute(
                delete(Vacancy).where(Vacancy.id.in_(old_ids))
            )
            await session.commit()

    async def get_recent_vacancies(self, limit: int = 50) -> list[Vacancy]:
        async with self.session_factory() as session:
            result = await session.execute(
                select(Vacancy).order_by(Vacancy.created_at.desc()).limit(limit)
            )
            return list(result.scalars().all())

    async def get_recent_sent(self, limit: int = 20, offset: int = 0) -> list[tuple[SentVacancy, Vacancy, User, VacancyFilter | None]]:
        async with self.session_factory() as session:
            stmt = (
                select(SentVacancy, Vacancy, User, VacancyFilter)
                .join(Vacancy, SentVacancy.vacancy_id == Vacancy.id)
                .join(User, SentVacancy.user_id == User.id)
                .outerjoin(VacancyFilter, SentVacancy.filter_id == VacancyFilter.id)
                .order_by(SentVacancy.sent_at.desc())
                .offset(offset)
                .limit(limit)
            )
            result = await session.execute(stmt)
            return list(result.all())
