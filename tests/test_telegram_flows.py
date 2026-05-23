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
