import json
from datetime import datetime, timezone
from sqlalchemy import Integer, BigInteger, String, Boolean, DateTime, Text, ForeignKey, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def _utcnow():
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    username: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)


class VacancyFilter(Base):
    __tablename__ = "filters"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255))
    keywords: Mapped[str] = mapped_column(Text, default="[]")
    city: Mapped[str | None] = mapped_column(String(100))
    salary_min: Mapped[int | None] = mapped_column(Integer)
    salary_max: Mapped[int | None] = mapped_column(Integer)
    employment_types: Mapped[str] = mapped_column(Text, default="[]")
    sites: Mapped[str] = mapped_column(Text, default="[]")
    exclude_keywords: Mapped[str] = mapped_column(Text, default="[]")
    experience: Mapped[str | None] = mapped_column(String(10))
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)

    def get_keywords(self) -> list[str]:
        return list(dict.fromkeys(json.loads(self.keywords)))

    def set_keywords(self, keywords: list[str]):
        self.keywords = json.dumps(list(dict.fromkeys(keywords)), ensure_ascii=False)

    def get_exclude_keywords(self) -> list[str]:
        return list(dict.fromkeys(json.loads(self.exclude_keywords)))

    def set_exclude_keywords(self, keywords: list[str]):
        self.exclude_keywords = json.dumps(list(dict.fromkeys(keywords)), ensure_ascii=False)

    def get_employment_types(self) -> list[str]:
        return json.loads(self.employment_types)

    def set_employment_types(self, types: list[str]):
        self.employment_types = json.dumps(types, ensure_ascii=False)

    def get_sites(self) -> list[str]:
        return json.loads(self.sites)

    def set_sites(self, sites: list[str]):
        self.sites = json.dumps(sites, ensure_ascii=False)


class Vacancy(Base):
    __tablename__ = "vacancies"

    id: Mapped[int] = mapped_column(primary_key=True)
    source: Mapped[str] = mapped_column(String(50), nullable=False)
    source_id: Mapped[str] = mapped_column(String(255), nullable=False)
    title: Mapped[str] = mapped_column(String(500))
    company: Mapped[str | None] = mapped_column(String(500))
    salary_text: Mapped[str | None] = mapped_column(String(255))
    employment_type: Mapped[str | None] = mapped_column(String(50))
    experience: Mapped[str | None] = mapped_column(String(10))
    city: Mapped[str | None] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    url: Mapped[str] = mapped_column(String(1000))
    published_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)

    __table_args__ = (
        UniqueConstraint("source", "source_id", name="uq_source_vacancy"),
    )


class SentVacancy(Base):
    __tablename__ = "sent_vacancies"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    vacancy_id: Mapped[int] = mapped_column(ForeignKey("vacancies.id", ondelete="CASCADE"), nullable=False)
    filter_id: Mapped[int | None] = mapped_column(ForeignKey("filters.id"))
    sent_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)

    __table_args__ = (
        UniqueConstraint("user_id", "vacancy_id", name="uq_sent_user_vacancy"),
    )


class SavedVacancy(Base):
    __tablename__ = "saved_vacancies"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    vacancy_id: Mapped[int] = mapped_column(ForeignKey("vacancies.id", ondelete="CASCADE"), nullable=False)
    saved_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)

    __table_args__ = (
        UniqueConstraint("user_id", "vacancy_id", name="uq_saved_user_vacancy"),
    )


class Blocklist(Base):
    __tablename__ = "blocklist"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    pattern: Mapped[str] = mapped_column(String(500), nullable=False)
    type: Mapped[str] = mapped_column(String(20), nullable=False)  # "company" or "keyword"
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)

    __table_args__ = (
        UniqueConstraint("user_id", "pattern", "type", name="uq_blocklist_entry"),
    )


class TelegramDelivery(Base):
    __tablename__ = "telegram_deliveries"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    chat_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    vacancy_id: Mapped[int | None] = mapped_column(ForeignKey("vacancies.id", ondelete="SET NULL"))
    source: Mapped[str] = mapped_column(String(50), nullable=False)
    url: Mapped[str] = mapped_column(String(1000), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_error: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)


class ParserHealth(Base):
    __tablename__ = "parser_health"

    id: Mapped[int] = mapped_column(primary_key=True)
    site: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    ok: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    latency_ms: Mapped[int | None] = mapped_column(Integer)
    error: Mapped[str | None] = mapped_column(Text)
    checked_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
