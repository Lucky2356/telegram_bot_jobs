import pytest
from core.database.models import User


@pytest.mark.asyncio
async def test_create_user(db):
    user = await db.get_or_create_user(telegram_id=12345, username="test_user")
    assert user is not None
    assert user.telegram_id == 12345
    assert user.username == "test_user"


@pytest.mark.asyncio
async def test_get_or_create_user_returns_existing(db):
    user1 = await db.get_or_create_user(telegram_id=999, username="first")
    user2 = await db.get_or_create_user(telegram_id=999, username="second")
    assert user1.id == user2.id
    assert user2.username == "second"  # updated


@pytest.mark.asyncio
async def test_create_filter(db):
    user = await db.get_or_create_user(telegram_id=1)
    vf = await db.create_filter(
        user_id=user.id,
        name="Test Filter",
        keywords=["Python", "Django"],
        city="Москва",
        salary_min=100000,
        salary_max=200000,
        employment_types=["full"],
        sites=["hh"],
    )
    assert vf.name == "Test Filter"
    assert vf.get_keywords() == ["Python", "Django"]


@pytest.mark.asyncio
async def test_get_user_filters(db):
    user = await db.get_or_create_user(telegram_id=1)
    await db.create_filter(user.id, "F1", ["Python"], None, None, None, [], ["hh"])
    await db.create_filter(user.id, "F2", ["JS"], None, None, None, [], ["hh"])
    filters = await db.get_user_filters(user.id)
    assert len(filters) == 2


@pytest.mark.asyncio
async def test_toggle_filter(db):
    user = await db.get_or_create_user(telegram_id=1)
    vf = await db.create_filter(user.id, "F1", ["Python"], None, None, None, [], ["hh"])
    assert vf.active is True

    active = await db.toggle_filter(vf.id)
    assert active is False

    active = await db.toggle_filter(vf.id)
    assert active is True


@pytest.mark.asyncio
async def test_delete_filter(db):
    user = await db.get_or_create_user(telegram_id=1)
    vf = await db.create_filter(user.id, "ToDelete", ["x"], None, None, None, [], ["hh"])
    await db.delete_filter(vf.id)
    assert await db.get_filter(vf.id) is None


@pytest.mark.asyncio
async def test_add_vacancy_and_check_sent(db):
    user = await db.get_or_create_user(telegram_id=1)
    from scrapers.base import VacancyData
    from datetime import datetime, timezone

    data = VacancyData(
        source="hh",
        source_id="123",
        title="Python Developer",
        company="TestCorp",
        url="https://hh.ru/vacancy/123",
    )
    vac = await db.add_vacancy(data)
    assert vac is not None
    assert vac.title == "Python Developer"

    assert await db.is_sent(user.id, vac.id) is False
    await db.mark_sent(user.id, vac.id)
    assert await db.is_sent(user.id, vac.id) is True


@pytest.mark.asyncio
async def test_add_vacancy_duplicate(db):
    from scrapers.base import VacancyData
    data = VacancyData(source="hh", source_id="dup", title="Dup", url="url")
    v1 = await db.add_vacancy(data)
    v2 = await db.add_vacancy(data)
    assert v1 is not None
    assert v2 is None  # duplicate skipped


@pytest.mark.asyncio
async def test_save_and_get_saved_vacancies(db):
    user = await db.get_or_create_user(telegram_id=1)
    from scrapers.base import VacancyData
    vac = await db.add_vacancy(VacancyData(source="hh", source_id="s1", title="Saved", url="url"))
    assert vac is not None

    await db.save_vacancy(user.id, vac.id)
    saved = await db.get_saved_vacancies()
    assert len(saved) == 1
    assert saved[0][1].title == "Saved"


@pytest.mark.asyncio
async def test_blocklist(db):
    user = await db.get_or_create_user(telegram_id=1)
    await db.add_blocklist(user.id, "BadCompany", "company")

    blocks = await db.get_blocklist()
    assert len(blocks) == 1
    assert blocks[0].pattern == "BadCompany"

    assert await db.is_blocked(user.id, "BadCompany", "Some title") is True
    assert await db.is_blocked(user.id, "GoodCompany", "Some title") is False


@pytest.mark.asyncio
async def test_unsave_vacancy(db):
    user = await db.get_or_create_user(telegram_id=1)
    from scrapers.base import VacancyData
    vac = await db.add_vacancy(VacancyData(source="hh", source_id="u1", title="Unsave", url="url"))
    await db.save_vacancy(user.id, vac.id)
    await db.unsave_vacancy(user.id, vac.id)
    saved = await db.get_saved_vacancies()
    assert len(saved) == 0


@pytest.mark.asyncio
async def test_remove_blocklist_by_id(db):
    user = await db.get_or_create_user(telegram_id=1)
    await db.add_blocklist(user.id, "SpamCo", "company")
    blocks = await db.get_blocklist()
    await db.remove_blocklist_by_id(blocks[0].id)
    assert len(await db.get_blocklist()) == 0
