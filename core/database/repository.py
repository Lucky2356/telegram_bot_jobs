import json
from datetime import datetime, timezone, timedelta
from sqlalchemy import select, delete, func, update, case
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from core.database.models import (
    Base,
    Blocklist,
    ParserHealth,
    SavedVacancy,
    SentVacancy,
    TelegramDelivery,
    User,
    Vacancy,
    VacancyFilter,
)
from scrapers.base import VacancyData


class Database:
    def __init__(self, url: str):
        self.engine = create_async_engine(url, echo=False)
        self.session_factory = async_sessionmaker(self.engine, expire_on_commit=False)

    async def create_tables(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def ensure_legacy_schema_compatibility(self):
        """Patch legacy SQLite schemas in-place when old columns are missing."""
        async with self.engine.begin() as conn:
            if self.engine.url.get_backend_name() != "sqlite":
                return
            result = await conn.exec_driver_sql("PRAGMA table_info(blocklist)")
            cols = {row[1] for row in result.fetchall()}
            if "created_at" not in cols:
                await conn.exec_driver_sql("ALTER TABLE blocklist ADD COLUMN created_at DATETIME")
            await conn.run_sync(Base.metadata.create_all)

    async def get_or_create_user(self, telegram_id: int, username: str | None = None) -> User:
        async with self.session_factory() as session:
            result = await session.execute(select(User).where(User.telegram_id == telegram_id))
            user = result.scalar_one_or_none()
            if user is None:
                user = User(telegram_id=telegram_id, username=username)
                session.add(user)
                try:
                    await session.commit()
                except IntegrityError:
                    await session.rollback()
                    result = await session.execute(select(User).where(User.telegram_id == telegram_id))
                    user = result.scalar_one_or_none()
                    if user is None:
                        raise
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
                select(VacancyFilter).where(VacancyFilter.active).order_by(VacancyFilter.id)
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
            similar_stmt = select(Vacancy).where(
                func.lower(Vacancy.title) == (data.title or "").strip().lower(),
            )
            if data.company:
                similar_stmt = similar_stmt.where(func.lower(Vacancy.company) == data.company.strip().lower())
            else:
                similar_stmt = similar_stmt.where(Vacancy.company.is_(None))
            if data.city:
                similar_stmt = similar_stmt.where(func.lower(Vacancy.city) == data.city.strip().lower())
            similar = (await session.execute(similar_stmt.limit(1))).scalar_one_or_none()
            if similar:
                return similar
            result = await session.execute(
                select(Vacancy).where(
                    Vacancy.source == data.source,
                    Vacancy.source_id == data.source_id,
                )
            )
            existing = result.scalar_one_or_none()
            if existing:
                return existing
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
            try:
                await session.commit()
            except IntegrityError:
                await session.rollback()

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
                try:
                    await session.commit()
                except IntegrityError:
                    await session.rollback()

    async def get_active_filter_count(self) -> int:
        async with self.session_factory() as session:
            result = await session.execute(
                select(func.count(VacancyFilter.id)).where(VacancyFilter.active)
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

    async def enqueue_telegram_delivery(
        self,
        user_id: int | None,
        chat_id: int,
        vacancy_id: int | None,
        source: str,
        url: str,
        message: str,
        last_error: str | None = None,
    ) -> TelegramDelivery:
        async with self.session_factory() as session:
            item = TelegramDelivery(
                user_id=user_id,
                chat_id=chat_id,
                vacancy_id=vacancy_id,
                source=source,
                url=url,
                message=message,
                last_error=last_error,
            )
            session.add(item)
            await session.commit()
            await session.refresh(item)
            return item

    async def get_pending_telegram_deliveries(self, limit: int = 50) -> list[TelegramDelivery]:
        async with self.session_factory() as session:
            result = await session.execute(
                select(TelegramDelivery)
                .where(TelegramDelivery.status == "pending")
                .order_by(TelegramDelivery.created_at.asc())
                .limit(limit)
            )
            return list(result.scalars().all())

    async def mark_telegram_delivery_sent(self, delivery_id: int):
        async with self.session_factory() as session:
            item = await session.get(TelegramDelivery, delivery_id)
            if item:
                item.status = "sent"
                item.last_error = None
                item.updated_at = datetime.now(timezone.utc)
                await session.commit()

    async def mark_telegram_delivery_failed(self, delivery_id: int, error: str):
        async with self.session_factory() as session:
            item = await session.get(TelegramDelivery, delivery_id)
            if item:
                item.attempts += 1
                item.last_error = error[:2000]
                item.updated_at = datetime.now(timezone.utc)
                if item.attempts >= 10:
                    item.status = "failed"
                await session.commit()

    async def get_telegram_delivery_stats(self) -> dict[str, int]:
        async with self.session_factory() as session:
            result = await session.execute(
                select(TelegramDelivery.status, func.count(TelegramDelivery.id))
                .group_by(TelegramDelivery.status)
            )
            stats = {row[0]: row[1] for row in result.all()}
            return {
                "pending": stats.get("pending", 0),
                "sent": stats.get("sent", 0),
                "failed": stats.get("failed", 0),
            }

    async def get_recent_telegram_deliveries(self, limit: int = 30) -> list[TelegramDelivery]:
        async with self.session_factory() as session:
            result = await session.execute(
                select(TelegramDelivery)
                .order_by(TelegramDelivery.updated_at.desc(), TelegramDelivery.created_at.desc())
                .limit(limit)
            )
            return list(result.scalars().all())

    async def retry_failed_telegram_deliveries(self) -> int:
        async with self.session_factory() as session:
            result = await session.execute(
                update(TelegramDelivery)
                .where(TelegramDelivery.status == "failed")
                .values(status="pending", updated_at=datetime.now(timezone.utc))
            )
            await session.commit()
            return result.rowcount or 0

    async def cleanup_telegram_deliveries(self, days: int = 14) -> int:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        async with self.session_factory() as session:
            result = await session.execute(
                delete(TelegramDelivery).where(
                    TelegramDelivery.status == "sent",
                    TelegramDelivery.updated_at < cutoff,
                )
            )
            await session.commit()
            return result.rowcount or 0

    async def upsert_parser_health(self, site: str, ok: bool, count: int, latency_ms: int | None, error: str | None):
        async with self.session_factory() as session:
            result = await session.execute(select(ParserHealth).where(ParserHealth.site == site))
            item = result.scalar_one_or_none()
            if item is None:
                item = ParserHealth(site=site)
                session.add(item)
            item.ok = ok
            item.count = count
            item.latency_ms = latency_ms
            item.error = error[:2000] if error else None
            item.checked_at = datetime.now(timezone.utc)
            await session.commit()

    async def get_parser_health(self) -> list[ParserHealth]:
        async with self.session_factory() as session:
            result = await session.execute(select(ParserHealth).order_by(ParserHealth.site.asc()))
            return list(result.scalars().all())

    async def get_filter_performance(self, days: int = 30) -> list[dict]:
        async with self.session_factory() as session:
            from datetime import timedelta
            cutoff = datetime.now(timezone.utc) - timedelta(days=days)
            result = await session.execute(
                select(
                    VacancyFilter.id,
                    VacancyFilter.name,
                    func.coalesce(
                        func.sum(case((SentVacancy.sent_at >= cutoff, 1), else_=0)),
                        0,
                    ).label("sent_count"),
                    func.max(SentVacancy.sent_at).label("last_sent_at"),
                )
                .outerjoin(SentVacancy, SentVacancy.filter_id == VacancyFilter.id)
                .group_by(VacancyFilter.id, VacancyFilter.name)
                .order_by("sent_count")
            )
            return [
                {
                    "filter_id": row[0],
                    "filter_name": row[1],
                    "sent_count": row[2],
                    "last_sent_at": row[3].isoformat() if row[3] else None,
                }
                for row in result.all()
            ]

    async def append_filter_exclude_keywords(self, filter_id: int, keywords: list[str]) -> VacancyFilter | None:
        async with self.session_factory() as session:
            vf = await session.get(VacancyFilter, filter_id)
            if vf is None:
                return None
            current = vf.get_exclude_keywords()
            merged = list(dict.fromkeys([*current, *[kw.strip() for kw in keywords if kw and kw.strip()]]))
            vf.set_exclude_keywords(merged)
            await session.commit()
            await session.refresh(vf)
            return vf

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
        from datetime import timedelta
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
