import pytest
from datetime import datetime, timezone

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


def test_scheduler_does_not_match_multiword_keyword_by_scattered_description_tokens(db):
    scheduler = Scheduler(db, bot=object())
    vacancy = VacancyData(
        source="hh",
        source_id="false-positive-support",
        title="Врач-невролог",
        company="Clinic",
        description="Нужен специалист. Есть технической оснащение и программа поддержки пациентов.",
        url="https://example.com/neurologist",
    )

    assert scheduler._matches_keywords(vacancy, ["Специалист технической поддержки"]) is False


def test_scheduler_does_not_match_single_word_keyword_only_in_description(db):
    scheduler = Scheduler(db, bot=object())
    vacancy = VacancyData(
        source="superjob",
        source_id="false-positive-single-token-support",
        title="Врач общей практики",
        company="Clinic",
        description="Есть внутренняя техподдержка для сотрудников.",
        url="https://example.com/doctor",
    )

    assert scheduler._matches_keywords(vacancy, ["Техподдержка"]) is False


def test_scheduler_matches_description_keyword_when_title_has_role_anchor(db):
    scheduler = Scheduler(db, bot=object())
    vacancy = VacancyData(
        source="habr",
        source_id="terraform-devops",
        title="DevOps инженер",
        company="Cloud Co",
        description="Инфраструктура как код: Terraform, Kubernetes, CI/CD.",
        url="https://example.com/devops",
    )

    assert scheduler._matches_keywords(vacancy, ["Terraform"]) is True


@pytest.mark.asyncio
async def test_scheduler_repeat_check_keeps_results_without_duplicate_telegram_send(db):
    class RepeatScraper:
        async def search(self, keywords, city=None):
            return [VacancyData(
                source="hh",
                source_id="repeat-1",
                title="Python Developer",
                company="Repeat Co",
                url="https://example.com/repeat-1",
                description="Backend development with Python",
            )]

        async def close(self):
            pass

    user = await db.get_or_create_user(telegram_id=707)
    await db.create_filter(
        user_id=user.id,
        name="Python repeat",
        keywords=["Python"],
        city=None,
        salary_min=None,
        salary_max=None,
        employment_types=[],
        sites=["hh"],
    )

    scheduler = Scheduler(db, bot=object())
    scheduler._scrapers["hh"] = RepeatScraper()

    await scheduler.run_check()
    first_results = scheduler.get_last_results()
    assert len(first_results) == 1
    assert user.id in scheduler._user_buffers
    assert len(scheduler._user_buffers[user.id]) == 1

    scheduler._user_buffers.clear()
    await scheduler.run_check()
    second_results = scheduler.get_last_results()
    assert len(second_results) == 1
    assert second_results[0]["id"] == first_results[0]["id"]
    assert user.id not in scheduler._user_buffers


@pytest.mark.asyncio
async def test_scheduler_single_filter_checks_work_for_different_filters_sequentially(db):
    class MultiFilterScraper:
        async def search(self, keywords, city=None):
            query = keywords[0]
            if "Python" in query:
                return [VacancyData(
                    source="hh",
                    source_id="mf-python",
                    title="Python Developer",
                    company="Py Co",
                    url="https://example.com/mf-python",
                )]
            if "Java" in query:
                return [VacancyData(
                    source="hh",
                    source_id="mf-java",
                    title="Java Developer",
                    company="Java Co",
                    url="https://example.com/mf-java",
                )]
            return []

        async def close(self):
            pass

    user = await db.get_or_create_user(telegram_id=808)
    f1 = await db.create_filter(
        user_id=user.id,
        name="Python only",
        keywords=["Python"],
        city=None,
        salary_min=None,
        salary_max=None,
        employment_types=[],
        sites=["hh"],
    )
    f2 = await db.create_filter(
        user_id=user.id,
        name="Java only",
        keywords=["Java"],
        city=None,
        salary_min=None,
        salary_max=None,
        employment_types=[],
        sites=["hh"],
    )

    scheduler = Scheduler(db, bot=object())
    scheduler._scrapers["hh"] = MultiFilterScraper()

    await scheduler.run_check_for_filter(f1.id)
    results_1 = scheduler.get_last_results()
    assert len(results_1) == 1
    assert results_1[0]["filter_id"] == f1.id
    assert "Python" in results_1[0]["title"]

    await scheduler.run_check_for_filter(f2.id)
    results_2 = scheduler.get_last_results()
    assert len(results_2) == 1
    assert results_2[0]["filter_id"] == f2.id
    assert "Java" in results_2[0]["title"]


@pytest.mark.asyncio
async def test_scheduler_run_check_collects_results_for_all_active_filters(db):
    class MultiFilterScraper:
        async def search(self, keywords, city=None):
            query = keywords[0]
            if "Python" in query:
                return [VacancyData(
                    source="hh",
                    source_id="all-python",
                    title="Python Developer",
                    company="Py Co",
                    url="https://example.com/all-python",
                )]
            if "Java" in query:
                return [VacancyData(
                    source="hh",
                    source_id="all-java",
                    title="Java Developer",
                    company="Java Co",
                    url="https://example.com/all-java",
                )]
            return []

        async def close(self):
            pass

    user = await db.get_or_create_user(telegram_id=818)
    python_filter = await db.create_filter(
        user_id=user.id,
        name="Python all",
        keywords=["Python"],
        city=None,
        salary_min=None,
        salary_max=None,
        employment_types=[],
        sites=["hh"],
    )
    java_filter = await db.create_filter(
        user_id=user.id,
        name="Java all",
        keywords=["Java"],
        city=None,
        salary_min=None,
        salary_max=None,
        employment_types=[],
        sites=["hh"],
    )

    scheduler = Scheduler(db, bot=object())
    scheduler._scrapers["hh"] = MultiFilterScraper()

    await scheduler.run_check()

    results = scheduler.get_last_results()
    result_filter_ids = {item["filter_id"] for item in results}
    assert result_filter_ids == {python_filter.id, java_filter.id}
    assert {item["title"] for item in results} == {"Python Developer", "Java Developer"}


@pytest.mark.asyncio
async def test_scheduler_single_filter_check_resets_results_for_each_filter(db):
    class SplitScraper:
        async def search(self, keywords, city=None):
            if "Python" in keywords[0]:
                return [VacancyData(
                    source="hh",
                    source_id="only-py",
                    title="Python Developer",
                    company="Py Co",
                    url="https://example.com/only-py",
                )]
            return [VacancyData(
                source="hh",
                source_id="only-java",
                title="Java Developer",
                company="Java Co",
                url="https://example.com/only-java",
            )]

        async def close(self):
            pass

    user = await db.get_or_create_user(telegram_id=909)
    py_filter = await db.create_filter(
        user_id=user.id,
        name="Python",
        keywords=["Python"],
        city=None,
        salary_min=None,
        salary_max=None,
        employment_types=[],
        sites=["hh"],
    )
    java_filter = await db.create_filter(
        user_id=user.id,
        name="Java",
        keywords=["Java"],
        city=None,
        salary_min=None,
        salary_max=None,
        employment_types=[],
        sites=["hh"],
    )

    scheduler = Scheduler(db, bot=object())
    scheduler._scrapers["hh"] = SplitScraper()

    await scheduler.run_check_for_filter(py_filter.id)
    py_results = scheduler.get_last_results()
    assert len(py_results) == 1
    assert py_results[0]["filter_id"] == py_filter.id

    await scheduler.run_check_for_filter(java_filter.id)
    java_results = scheduler.get_last_results()
    assert len(java_results) == 1
    assert java_results[0]["filter_id"] == java_filter.id


@pytest.mark.asyncio
async def test_scheduler_rejects_unknown_employment_type_when_filter_is_set(db):
    user = await db.get_or_create_user(telegram_id=1001)
    vf = await db.create_filter(
        user_id=user.id,
        name="Remote preferred",
        keywords=["Python"],
        city=None,
        salary_min=None,
        salary_max=None,
        employment_types=["remote"],
        sites=["hh"],
    )
    scheduler = Scheduler(db, bot=object())
    vacancy = VacancyData(
        source="hh",
        source_id="unknown-emp",
        title="Python Developer",
        company="Unknown Emp Co",
        employment_type=None,
        url="https://example.com/unknown-emp",
    )

    await scheduler._process_vacancy(vacancy, vf, user, ["Python"], ["remote"], [], None)
    assert user.id not in scheduler._user_buffers


@pytest.mark.asyncio
async def test_scheduler_infers_employment_type_from_description(db):
    user = await db.get_or_create_user(telegram_id=1006)
    vf = await db.create_filter(
        user_id=user.id,
        name="Remote",
        keywords=["Python"],
        city=None,
        salary_min=None,
        salary_max=None,
        employment_types=["remote"],
        sites=["hh"],
    )
    scheduler = Scheduler(db, bot=object())
    vacancy = VacancyData(
        source="hh",
        source_id="remote-in-description",
        title="Python Developer",
        company="Remote Text Co",
        employment_type=None,
        description="Работа полностью удаленно, гибкий график",
        url="https://example.com/remote-in-description",
    )

    await scheduler._process_vacancy(vacancy, vf, user, ["Python"], ["remote"], [], None)

    assert user.id in scheduler._user_buffers
    assert len(scheduler._user_buffers[user.id]) == 1


@pytest.mark.asyncio
async def test_scheduler_rejects_remote_primary_vacancy_for_full_filter(db):
    user = await db.get_or_create_user(telegram_id=1004)
    vf = await db.create_filter(
        user_id=user.id,
        name="Full time",
        keywords=["Python"],
        city=None,
        salary_min=None,
        salary_max=None,
        employment_types=["full"],
        sites=["hh"],
    )
    scheduler = Scheduler(db, bot=object())
    vacancy = VacancyData(
        source="hh",
        source_id="remote-full",
        title="Python Developer",
        company="Remote Full Co",
        employment_type="remote",
        employment_types=["full", "remote"],
        url="https://example.com/remote-full",
    )

    await scheduler._process_vacancy(vacancy, vf, user, ["Python"], ["full"], [], None)

    assert user.id not in scheduler._user_buffers


@pytest.mark.asyncio
async def test_scheduler_matches_remote_primary_vacancy_to_remote_filter(db):
    user = await db.get_or_create_user(telegram_id=1007)
    vf = await db.create_filter(
        user_id=user.id,
        name="Remote",
        keywords=["Python"],
        city=None,
        salary_min=None,
        salary_max=None,
        employment_types=["remote"],
        sites=["hh"],
    )
    scheduler = Scheduler(db, bot=object())
    vacancy = VacancyData(
        source="hh",
        source_id="remote-full-for-remote",
        title="Python Developer",
        company="Remote Full Co",
        employment_type="remote",
        employment_types=["full", "remote"],
        url="https://example.com/remote-full-for-remote",
    )

    await scheduler._process_vacancy(vacancy, vf, user, ["Python"], ["remote"], [], None)

    assert user.id in scheduler._user_buffers
    assert len(scheduler._user_buffers[user.id]) == 1


@pytest.mark.asyncio
async def test_scheduler_rejects_remote_only_vacancy_for_full_filter(db):
    user = await db.get_or_create_user(telegram_id=1005)
    vf = await db.create_filter(
        user_id=user.id,
        name="Full only",
        keywords=["Python"],
        city=None,
        salary_min=None,
        salary_max=None,
        employment_types=["full"],
        sites=["hh"],
    )
    scheduler = Scheduler(db, bot=object())
    vacancy = VacancyData(
        source="hh",
        source_id="remote-only",
        title="Python Developer",
        company="Remote Only Co",
        employment_type="remote",
        employment_types=["remote"],
        url="https://example.com/remote-only",
    )

    await scheduler._process_vacancy(vacancy, vf, user, ["Python"], ["full"], [], None)

    assert user.id not in scheduler._user_buffers


@pytest.mark.asyncio
async def test_scheduler_rejects_unknown_experience_when_filter_is_set(db):
    user = await db.get_or_create_user(telegram_id=1002)
    vf = await db.create_filter(
        user_id=user.id,
        name="1-3 years only",
        keywords=["Python"],
        city=None,
        salary_min=None,
        salary_max=None,
        employment_types=[],
        sites=["hh"],
        experience="1-3",
    )
    scheduler = Scheduler(db, bot=object())
    unknown = VacancyData(
        source="hh",
        source_id="unknown-exp",
        title="Python Developer",
        company="Unknown Exp Co",
        experience=None,
        url="https://example.com/unknown-exp",
    )
    mismatch = VacancyData(
        source="hh",
        source_id="senior-exp",
        title="Python Developer",
        company="Senior Co",
        experience="6+",
        url="https://example.com/senior-exp",
    )
    match = VacancyData(
        source="hh",
        source_id="match-exp",
        title="Python Developer",
        company="Match Exp Co",
        experience="1-3",
        url="https://example.com/match-exp",
    )

    await scheduler._process_vacancy(unknown, vf, user, ["Python"], [], [], "1-3")
    await scheduler._process_vacancy(mismatch, vf, user, ["Python"], [], [], "1-3")
    assert user.id not in scheduler._user_buffers

    await scheduler._process_vacancy(match, vf, user, ["Python"], [], [], "1-3")
    assert len(scheduler._user_buffers[user.id]) == 1


@pytest.mark.asyncio
async def test_scheduler_diagnostics_reports_scraper_errors_with_cache_wrapper(db):
    class BrokenScraper:
        async def search(self, keywords, city=None):
            raise RuntimeError("source is down")

        async def close(self):
            pass

    user = await db.get_or_create_user(telegram_id=1003)
    vf = await db.create_filter(
        user_id=user.id,
        name="Broken source",
        keywords=["Python"],
        city=None,
        salary_min=None,
        salary_max=None,
        employment_types=[],
        sites=["hh"],
    )
    scheduler = Scheduler(db, bot=object())
    scheduler._scrapers["hh"] = BrokenScraper()

    diagnostics = await scheduler.diagnose_filter(vf.id)

    assert diagnostics["ok"] is True
    assert diagnostics["sites"][0]["error"] == "source is down"


def test_habr_parser_keeps_card_without_meta():
    from scrapers.habr_career import HabrCareerScraper

    html = """
    <div class="vacancy-card">
      <a href="/vacancies/123">Python Developer</a>
      <div class="vacancy-card__company-title">ACME</div>
    </div>
    """
    scraper = HabrCareerScraper.__new__(HabrCareerScraper)
    vacancies = scraper._parse_html(html)

    assert len(vacancies) == 1
    assert vacancies[0].title == "Python Developer"
