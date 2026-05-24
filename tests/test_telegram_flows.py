import pytest

from bot.handlers.filters import FilterWizard, on_confirm
from bot.handlers.control import _safe_edit
from bot.keyboards import (
    FilterCallback, WizardAction,
    build_city_keyboard,
    build_confirm_keyboard,
    build_employment_keyboard,
    build_exclude_keywords_keyboard,
    build_experience_keyboard,
    build_keyword_groups_keyboard,
    build_keywords_for_group_keyboard,
    build_salary_keyboard,
    build_sites_keyboard,
    build_start_keyboard,
    build_vacancy_actions_keyboard,
)
from core.scheduler import Scheduler
from scrapers.base import VacancyData


class EditableMessage:
    def __init__(self):
        self.text = None
        self.reply_markup = None
        self.kwargs = None

    async def edit_text(self, text=None, reply_markup=None, **kwargs):
        self.text = text
        self.reply_markup = reply_markup
        self.kwargs = kwargs

    async def edit_reply_markup(self, reply_markup=None):
        self.reply_markup = reply_markup


class FakeUser:
    id = 555


class FakeCallback:
    def __init__(self):
        self.from_user = FakeUser()
        self.message = EditableMessage()
        self.answers = []

    async def answer(self, text=None, **kwargs):
        self.answers.append((text, kwargs))


class FakeState:
    def __init__(self, data):
        self.data = dict(data)
        self.state = FilterWizard.confirm
        self.cleared = False

    async def get_data(self):
        return dict(self.data)

    async def update_data(self, **kwargs):
        self.data.update(kwargs)

    async def set_state(self, state):
        self.state = state

    async def clear(self):
        self.cleared = True
        self.data.clear()
        self.state = None


@pytest.mark.asyncio
async def test_control_safe_edit_accepts_parse_mode():
    msg = EditableMessage()
    await _safe_edit(msg, text="<b>Filter</b>", parse_mode="HTML")

    assert msg.text == "<b>Filter</b>"
    assert msg.kwargs == {"parse_mode": "HTML"}


def test_exclude_keywords_back_returns_to_keyword_groups():
    markup = build_exclude_keywords_keyboard([])
    first_button = markup.inline_keyboard[0][0]
    callback = FilterCallback.unpack(first_button.callback_data)

    assert callback.action == WizardAction.KW_GROUP_BACK


def test_all_wizard_callback_data_fits_telegram_limit():
    markups = [
        build_start_keyboard(),
        build_keyword_groups_keyboard([]),
        build_keywords_for_group_keyboard("Backend-разработка", []),
        build_exclude_keywords_keyboard([]),
        build_city_keyboard(None),
        build_experience_keyboard(None),
        build_salary_keyboard(None),
        build_employment_keyboard([]),
        build_sites_keyboard([]),
        build_confirm_keyboard(),
        build_vacancy_actions_keyboard(123, "hh", "https://example.com"),
    ]

    for markup in markups:
        for row in markup.inline_keyboard:
            for button in row:
                if button.callback_data:
                    assert len(button.callback_data.encode("utf-8")) <= 64, button.callback_data


@pytest.mark.asyncio
async def test_scheduler_sends_existing_vacancy_to_unsent_user(db):
    user1 = await db.get_or_create_user(telegram_id=101)
    user2 = await db.get_or_create_user(telegram_id=202)
    vf = await db.create_filter(
        user_id=user2.id,
        name="Python",
        keywords=["Python"],
        city=None,
        salary_min=None,
        salary_max=None,
        employment_types=[],
        sites=["hh"],
    )
    data = VacancyData(
        source="hh",
        source_id="shared",
        title="Python Developer",
        company="Good Co",
        url="https://example.com/v/shared",
    )
    existing = await db.add_vacancy(data)
    await db.mark_sent(user1.id, existing.id)

    scheduler = Scheduler(db, bot=object())
    await scheduler._process_vacancy(
        data,
        vf,
        user2,
        keywords=["Python"],
        emp_types=[],
        exclude_keywords=[],
        experience=None,
    )

    assert await db.is_sent(user2.id, existing.id) is True
    assert scheduler.last_results[user2.id][0][0] == existing.id


@pytest.mark.asyncio
async def test_filter_wizard_confirm_creates_filter(db):
    state = FakeState({
        "filter_name": "Python Remote",
        "selected_keywords": ["Python-разработчик", "Python-разработчик"],
        "excluded_keywords": ["стажер"],
        "city": "novosibirsk",
        "salary_min": 150000,
        "salary_max": 300000,
        "employment_types": ["remote"],
        "sites": ["hh", "habr"],
        "experience": "1-3",
    })
    callback = FakeCallback()

    await on_confirm(callback, state, db)

    user = await db.get_or_create_user(callback.from_user.id)
    filters = await db.get_user_filters(user.id)
    assert len(filters) == 1
    assert filters[0].name == "Python Remote"
    assert filters[0].get_keywords() == ["Python-разработчик"]
    assert filters[0].get_exclude_keywords() == ["стажер"]
    assert filters[0].city == "novosibirsk"
    assert filters[0].salary_min == 150000
    assert filters[0].salary_max == 300000
    assert filters[0].get_employment_types() == ["remote"]
    assert filters[0].get_sites() == ["hh", "habr"]
    assert filters[0].experience == "1-3"
    assert state.cleared is True
    assert "создан" in callback.message.text

from datetime import datetime, timezone


@pytest.mark.asyncio
async def test_scheduler_rejects_vacancy_outside_salary_range(db):
    user = await db.get_or_create_user(telegram_id=303)
    vf = await db.create_filter(
        user_id=user.id,
        name="Salary bounded",
        keywords=["Python"],
        city=None,
        salary_min=150000,
        salary_max=250000,
        employment_types=[],
        sites=["hh"],
    )
    scheduler = Scheduler(db, bot=object())

    too_low = VacancyData(
        source="hh",
        source_id="sal-low",
        title="Python Developer",
        company="Low Co",
        salary_text="100 000 ?",
        salary_min=90000,
        salary_max=120000,
        url="https://example.com/low",
        published_at=datetime.now(timezone.utc),
    )
    too_high = VacancyData(
        source="hh",
        source_id="sal-high",
        title="Python Developer",
        company="High Co",
        salary_text="400 000 ?",
        salary_min=300000,
        salary_max=450000,
        url="https://example.com/high",
        published_at=datetime.now(timezone.utc),
    )

    await scheduler._process_vacancy(too_low, vf, user, ["Python"], [], [], None)
    await scheduler._process_vacancy(too_high, vf, user, ["Python"], [], [], None)

    assert scheduler._user_buffers.get(user.id) is None
    assert user.id not in scheduler.last_results


@pytest.mark.asyncio
async def test_scheduler_keeps_vacancy_without_salary_when_filter_has_bounds(db):
    user = await db.get_or_create_user(telegram_id=404)
    vf = await db.create_filter(
        user_id=user.id,
        name="Salary bounded",
        keywords=["Python"],
        city=None,
        salary_min=150000,
        salary_max=250000,
        employment_types=[],
        sites=["hh"],
    )
    scheduler = Scheduler(db, bot=object())

    unknown_salary = VacancyData(
        source="hh",
        source_id="sal-unknown",
        title="Python Developer",
        company="Unknown Co",
        salary_text=None,
        salary_min=None,
        salary_max=None,
        url="https://example.com/unknown",
        published_at=datetime.now(timezone.utc),
    )

    await scheduler._process_vacancy(unknown_salary, vf, user, ["Python"], [], [], None)

    assert user.id in scheduler._user_buffers
    assert len(scheduler._user_buffers[user.id]) == 1
    assert user.id in scheduler.last_results


class FakeSearchScraper:
    def __init__(self):
        self.calls = []

    async def search(self, keywords, city=None):
        self.calls.append((list(keywords), city))
        if keywords == ["Программист 1С"]:
            return [
                VacancyData(
                    source="hh",
                    source_id="one-c",
                    title="Программист 1С",
                    company="1C Studio",
                    url="https://example.com/one-c",
                    description="Разработка и поддержка конфигураций 1С",
                )
            ]
        return []

    async def close(self):
        pass


@pytest.mark.asyncio
async def test_scheduler_searches_sites_with_short_synonym_queries_not_joined_string(db):
    user = await db.get_or_create_user(telegram_id=505)
    vf = await db.create_filter(
        user_id=user.id,
        name="1С поиск",
        keywords=["1С Программист", "Python"],
        city=None,
        salary_min=None,
        salary_max=None,
        employment_types=[],
        sites=["hh"],
    )
    scheduler = Scheduler(db, bot=object())
    fake_scraper = FakeSearchScraper()
    scheduler._scrapers["hh"] = fake_scraper

    await scheduler._check_filter(vf, user)

    assert fake_scraper.calls[0] == (["1С Программист"], None)
    assert (["Программист 1С"], None) in fake_scraper.calls
    assert all(len(call_keywords) == 1 for call_keywords, _ in fake_scraper.calls)
    assert len(scheduler._user_buffers[user.id]) == 1
    assert scheduler.last_results[user.id][0][2].title == "Программист 1С"


@pytest.mark.asyncio
async def test_single_filter_web_check_includes_already_sent_vacancies(db):
    class AlreadySentScraper:
        async def search(self, keywords, city=None):
            return [VacancyData(
                source="hh",
                source_id="python-existing",
                title="Python Developer",
                company="Good Co",
                url="https://example.com/python-existing",
                description="Backend development with Python",
            )]

        async def close(self):
            pass

    user = await db.get_or_create_user(telegram_id=606)
    vf = await db.create_filter(
        user_id=user.id,
        name="Python search",
        keywords=["Python"],
        city=None,
        salary_min=None,
        salary_max=None,
        employment_types=[],
        sites=["hh"],
    )
    existing = await db.add_vacancy(VacancyData(
        source="hh",
        source_id="python-existing",
        title="Python Developer",
        company="Good Co",
        url="https://example.com/python-existing",
        description="Backend development with Python",
    ))
    await db.mark_sent(user.id, existing.id, filter_id=vf.id)

    scheduler = Scheduler(db, bot=object())
    scheduler._scrapers["hh"] = AlreadySentScraper()

    await scheduler.run_check_for_filter(vf.id)

    results = scheduler.get_last_results()
    assert len(results) == 1
    assert results[0]["id"] == existing.id
    assert results[0]["filter_id"] == vf.id
    assert user.id not in scheduler._user_buffers


def test_scheduler_matches_russian_phrase_synonyms_without_regex_boundaries(db):
    scheduler = Scheduler(db, bot=object())
    vacancy = VacancyData(
        source="hh",
        source_id="one-c-match",
        title="Ученик программиста 1С",
        company="1C Studio",
        url="https://example.com/one-c-match",
    )

    assert scheduler._matches_keywords(vacancy, ["1С Программист", "Программист 1С"]) is True


def test_scheduler_matches_one_c_with_latin_and_cyrillic_c(db):
    scheduler = Scheduler(db, bot=object())
    vacancy = VacancyData(
        source="superjob",
        source_id="one-c-latin",
        title="Программист 1C",
        company="1C Studio",
        url="https://example.com/one-c-latin",
    )

    assert scheduler._matches_keywords(vacancy, ["1С Программист", "Программист 1С"]) is True
