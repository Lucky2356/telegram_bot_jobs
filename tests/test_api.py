import asyncio
import pytest
from httpx import AsyncClient, ASGITransport
from core.database.repository import Database
from core.config import settings
from web.app import create_web_app
from web.auth import hash_password


class FakeScheduler:
    is_checking = False
    run_check_called = False
    run_check_filter_calls: list[int] = []
    last_results_time = "2026-01-01T00:00:00+00:00"

    async def run_check(self):
        self.run_check_called = True
        return None

    async def run_check_for_filter(self, filter_id: int):
        self.run_check_filter_calls.append(filter_id)
        return None

    async def preview_filter(self, filter_id: int):
        return [{"id": 1, "filter_id": filter_id, "title": "Preview"}]

    async def diagnose_filter(self, filter_id: int):
        return {
            "ok": True,
            "filter_id": filter_id,
            "filter_name": "Diagnostics",
            "queries": ["Python"],
            "sites": [],
        }

    def get_event_log(self):
        return [{"type": "check_started"}]

    def _get_scraper(self, site: str):
        class FakeScraper:
            async def search(self, keywords, city=None):
                return []
        return FakeScraper()


@pytest.fixture
def app(db: Database):
    return create_web_app(db, scheduler=None)


@pytest.mark.asyncio
async def test_get_config(app, db):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/config")
        assert resp.status_code == 200
        data = resp.json()
        assert "employment_types" in data
        assert "sites" in data
        assert "cities" in data
        assert "salaries" in data
        assert "keyword_groups" in data


@pytest.mark.asyncio
async def test_create_and_list_filters(app, db):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        create_resp = await client.post(
            "/api/filters",
            json={
                "name": "Python Dev",
                "keywords": ["Python"],
                "city": None,
                "salary_min": None,
                "salary_max": None,
                "employment_types": ["full"],
                "sites": ["hh"],
                "experience": None,
                "exclude_keywords": [],
            },
        )
        assert create_resp.status_code == 200
        created = create_resp.json()
        assert created["ok"] is True
        assert created["filter"]["name"] == "Python Dev"

        list_resp = await client.get("/api/filters")
        assert list_resp.status_code == 200
        filters = list_resp.json()
        assert len(filters) >= 1
        assert filters[0]["name"] == "Python Dev"


@pytest.mark.asyncio
async def test_create_filter_normalizes_input_and_defaults_to_all_sites(app, db):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        create_resp = await client.post(
            "/api/filters",
            json={
                "name": "  Custom  ",
                "keywords": [" Python ", "Python", "Django"],
                "city": None,
                "salary_min": None,
                "salary_max": None,
                "employment_types": ["remote", "remote"],
                "sites": [],
                "experience": None,
                "exclude_keywords": ["стажер", " стажер "],
            },
        )

    assert create_resp.status_code == 200
    created = create_resp.json()["filter"]
    assert created["name"] == "Custom"
    assert created["keywords"] == ["Python", "Django"]
    assert created["exclude_keywords"] == ["стажер"]
    assert created["employment_types"] == ["remote"]
    assert set(created["sites"]) == {"hh", "superjob", "rabota", "habr", "trudvsem"}


@pytest.mark.asyncio
async def test_create_filter_rejects_empty_keywords(app, db):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/filters",
            json={
                "name": "Empty",
                "keywords": ["  "],
                "city": None,
                "salary_min": None,
                "salary_max": None,
                "employment_types": [],
                "sites": ["hh"],
                "experience": None,
                "exclude_keywords": [],
            },
        )

    assert resp.status_code == 400
    assert resp.json()["ok"] is False


@pytest.mark.asyncio
async def test_create_filter_rejects_invalid_enum_values(app, db):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/filters",
            json={
                "name": "Invalid",
                "keywords": ["Python"],
                "city": "unknown-city",
                "salary_min": -1,
                "salary_max": None,
                "employment_types": ["full"],
                "sites": ["hh"],
                "experience": None,
                "exclude_keywords": [],
            },
        )

    assert resp.status_code == 400
    assert resp.json()["ok"] is False


@pytest.mark.asyncio
async def test_web_filter_actions_are_limited_to_current_user(app, db):
    current_user = await db.get_or_create_user(telegram_id=111, username="current")
    other_user = await db.get_or_create_user(telegram_id=222, username="other")
    foreign_filter = await db.create_filter(
        user_id=other_user.id,
        name="Other User Filter",
        keywords=["Python"],
        city=None,
        salary_min=None,
        salary_max=None,
        employment_types=[],
        sites=["hh"],
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        toggle_resp = await client.post(f"/api/filters/{foreign_filter.id}/toggle")
        delete_resp = await client.delete(f"/api/filters/{foreign_filter.id}")

    assert current_user.id != other_user.id
    assert toggle_resp.status_code == 403
    assert delete_resp.status_code == 403
    assert await db.get_filter(foreign_filter.id) is not None


@pytest.mark.asyncio
async def test_toggle_filter_api(app, db):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        create_resp = await client.post(
            "/api/filters",
            json={
                "name": "Toggle Me",
                "keywords": ["Python"],
                "city": None,
                "salary_min": None,
                "salary_max": None,
                "employment_types": ["full"],
                "sites": ["hh"],
            },
        )
        filter_id = create_resp.json()["filter"]["id"]

        toggle_resp = await client.post(f"/api/filters/{filter_id}/toggle")
        assert toggle_resp.json()["active"] is False

        toggle_resp = await client.post(f"/api/filters/{filter_id}/toggle")
        assert toggle_resp.json()["active"] is True


@pytest.mark.asyncio
async def test_delete_filter_api(app, db):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        create_resp = await client.post(
            "/api/filters",
            json={
                "name": "Delete Me",
                "keywords": ["x"],
                "city": None,
                "salary_min": None,
                "salary_max": None,
                "employment_types": [],
                "sites": ["hh"],
            },
        )
        filter_id = create_resp.json()["filter"]["id"]

        delete_resp = await client.delete(f"/api/filters/{filter_id}")
        assert delete_resp.status_code == 200

        get_resp = await client.get(f"/api/filters/{filter_id}")
        assert get_resp.json()["ok"] is False


@pytest.mark.asyncio
async def test_get_stats(app, db):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert "total_filters" in data
        assert "active_filters" in data
        assert "total_vacancies" in data
        assert "total_sent" in data


@pytest.mark.asyncio
async def test_get_status(app, db):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/status")
        assert resp.status_code == 200
        data = resp.json()
        for parser in ("hh", "superjob", "trudvsem", "rabota", "habr"):
            assert parser in data


@pytest.mark.asyncio
async def test_health_endpoint(app, db):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/health")

    assert resp.status_code == 200
    assert resp.json()["ok"] is True


@pytest.mark.asyncio
async def test_health_endpoint_stays_public_when_auth_enabled(db):
    original_password = settings.WEB_PASSWORD
    settings.WEB_PASSWORD = "secret-pass"
    try:
        secured_app = create_web_app(db, scheduler=None)
        transport = ASGITransport(app=secured_app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/health")

        assert resp.status_code == 200
        assert resp.json()["ok"] is True
    finally:
        settings.WEB_PASSWORD = original_password


@pytest.mark.asyncio
async def test_login_rate_limit_returns_429(db):
    original_password = settings.WEB_PASSWORD
    original_limit = settings.WEB_LOGIN_RATE_LIMIT
    original_window = settings.WEB_RATE_LIMIT_WINDOW_SECONDS
    settings.WEB_PASSWORD = "secret-pass"
    settings.WEB_LOGIN_RATE_LIMIT = 2
    settings.WEB_RATE_LIMIT_WINDOW_SECONDS = 60
    try:
        secured_app = create_web_app(db, scheduler=None)
        transport = ASGITransport(app=secured_app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            first = await client.post("/api/auth/login", json={"password": "bad-pass"})
            second = await client.post("/api/auth/login", json={"password": "bad-pass"})
            third = await client.post("/api/auth/login", json={"password": "bad-pass"})

        assert first.status_code == 401
        assert second.status_code == 401
        assert third.status_code == 429
    finally:
        settings.WEB_PASSWORD = original_password
        settings.WEB_LOGIN_RATE_LIMIT = original_limit
        settings.WEB_RATE_LIMIT_WINDOW_SECONDS = original_window


@pytest.mark.asyncio
async def test_check_now_rate_limit_returns_429(db):
    original_limit = settings.WEB_ACTION_RATE_LIMIT
    original_window = settings.WEB_RATE_LIMIT_WINDOW_SECONDS
    settings.WEB_ACTION_RATE_LIMIT = 1
    settings.WEB_RATE_LIMIT_WINDOW_SECONDS = 60
    try:
        app = create_web_app(db, scheduler=FakeScheduler())
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            first = await client.post("/api/check_now")
            second = await client.post("/api/check_now")

        assert first.status_code == 200
        assert second.status_code == 429
    finally:
        settings.WEB_ACTION_RATE_LIMIT = original_limit
        settings.WEB_RATE_LIMIT_WINDOW_SECONDS = original_window


@pytest.mark.asyncio
async def test_save_and_get_saved(app, db):
    from scrapers.base import VacancyData
    vac = await db.add_vacancy(VacancyData(source="hh", source_id="api_save", title="API Saved", url="url"))

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        save_resp = await client.post(f"/api/vacancies/{vac.id}/save")
        assert save_resp.status_code == 200

        saved_resp = await client.get("/api/saved")
        assert saved_resp.status_code == 200
        saved = saved_resp.json()
        assert len(saved) == 1
        assert saved[0]["vacancy_title"] == "API Saved"


@pytest.mark.asyncio
async def test_block_vacancy(app, db):
    from scrapers.base import VacancyData
    vac = await db.add_vacancy(VacancyData(source="hh", source_id="api_block", title="Block Me", company="Spam Inc", url="url"))

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        block_resp = await client.post(f"/api/vacancies/{vac.id}/block")
        assert block_resp.status_code == 200

        blocks = await db.get_blocklist()
        assert len(blocks) == 1
        assert blocks[0].pattern == "Spam Inc"


@pytest.mark.asyncio
async def test_clone_filter(app, db):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        create_resp = await client.post(
            "/api/filters",
            json={
                "name": "Original",
                "keywords": ["Python"],
                "city": None,
                "salary_min": None,
                "salary_max": None,
                "employment_types": [],
                "sites": ["hh"],
            },
        )
        filter_id = create_resp.json()["filter"]["id"]

        clone_resp = await client.post(f"/api/filters/{filter_id}/clone")
        assert clone_resp.status_code == 200
        assert clone_resp.json()["filter"]["name"] == "Копия — Original"


@pytest.mark.asyncio
async def test_not_found_endpoints_return_404(app, db):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        update_resp = await client.put(
            "/api/filters/999999",
            json={
                "name": "Missing",
                "keywords": ["Python"],
                "city": None,
                "salary_min": None,
                "salary_max": None,
                "employment_types": [],
                "sites": ["hh"],
                "experience": None,
                "exclude_keywords": [],
            },
        )
        assert update_resp.status_code == 404
        assert update_resp.json()["ok"] is False

        clone_resp = await client.post("/api/filters/999999/clone")
        assert clone_resp.status_code == 404
        assert clone_resp.json()["ok"] is False

        save_resp = await client.post("/api/vacancies/999999/save")
        assert save_resp.status_code == 404
        assert save_resp.json()["ok"] is False

        block_resp = await client.post("/api/vacancies/999999/block")
        assert block_resp.status_code == 404
        assert block_resp.json()["ok"] is False


@pytest.mark.asyncio
async def test_login_wrong_password_returns_401(db):
    original_password = settings.WEB_PASSWORD
    settings.WEB_PASSWORD = "secret-pass"
    try:
        secured_app = create_web_app(db, scheduler=None)
        transport = ASGITransport(app=secured_app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post("/api/auth/login", json={"password": "bad-pass"})
            assert resp.status_code == 401
            assert resp.json()["ok"] is False
    finally:
        settings.WEB_PASSWORD = original_password


@pytest.mark.asyncio
async def test_web_filter_creation_uses_real_telegram_user(app, db):
    await db.get_or_create_user(telegram_id=0, username="web_user")
    real_user = await db.get_or_create_user(telegram_id=123456, username="real")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        create_resp = await client.post(
            "/api/filters",
            json={
                "name": "Shared Filter",
                "keywords": ["Python"],
                "city": None,
                "salary_min": None,
                "salary_max": None,
                "employment_types": [],
                "sites": ["hh"],
                "experience": None,
                "exclude_keywords": [],
            },
        )
        assert create_resp.status_code == 200
        filter_id = create_resp.json()["filter"]["id"]

    vf = await db.get_filter(filter_id)
    assert vf.user_id == real_user.id


@pytest.mark.asyncio
async def test_web_user_data_is_merged_into_real_user(app, db):
    web_user = await db.get_or_create_user(telegram_id=0, username="web_user")
    real_user = await db.get_or_create_user(telegram_id=654321, username="real")
    old_filter = await db.create_filter(
        user_id=web_user.id,
        name="Old Web Filter",
        keywords=["React"],
        city=None,
        salary_min=None,
        salary_max=None,
        employment_types=[],
        sites=["hh"],
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/saved")
        assert resp.status_code == 200

    moved = await db.get_filter(old_filter.id)
    assert moved.user_id == real_user.id


@pytest.mark.asyncio
async def test_events_endpoint_smoke_without_scheduler(db):
    app = create_web_app(db, scheduler=None)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/events")
        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("text/event-stream")


@pytest.mark.asyncio
async def test_check_filter_endpoint_starts_background_task(db):
    scheduler = FakeScheduler()
    app = create_web_app(db, scheduler=scheduler)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        create_resp = await client.post(
            "/api/filters",
            json={
                "name": "Background check",
                "keywords": ["Python"],
                "city": None,
                "salary_min": None,
                "salary_max": None,
                "employment_types": [],
                "sites": ["hh"],
                "experience": None,
                "exclude_keywords": [],
            },
        )
        filter_id = create_resp.json()["filter"]["id"]
        resp = await client.post(f"/api/filters/{filter_id}/check")
        assert resp.status_code == 200
        await asyncio.sleep(0)

    assert filter_id in scheduler.run_check_filter_calls


@pytest.mark.asyncio
async def test_export_and_import_filters_api(db):
    app = create_web_app(db, scheduler=FakeScheduler())
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        create_resp = await client.post(
            "/api/filters",
            json={
                "name": "Exported",
                "keywords": ["Python"],
                "city": None,
                "salary_min": None,
                "salary_max": None,
                "employment_types": [],
                "sites": ["hh"],
                "experience": None,
                "exclude_keywords": [],
            },
        )
        assert create_resp.status_code == 200

        export_resp = await client.get("/api/filters/export")
        assert export_resp.status_code == 200
        exported = export_resp.json()
        assert exported["filters"][0]["name"] == "Exported"

        import_resp = await client.post("/api/filters/import", json={"filters": exported["filters"], "replace": False})
        assert import_resp.status_code == 200
        assert import_resp.json()["ok"] is True


@pytest.mark.asyncio
async def test_preview_diagnostics_health_and_logs_api(db):
    scheduler = FakeScheduler()
    app = create_web_app(db, scheduler=scheduler)
    user = await db.get_or_create_user(telegram_id=1)
    vf = await db.create_filter(
        user_id=user.id,
        name="API diagnostic",
        keywords=["Python"],
        city=None,
        salary_min=None,
        salary_max=None,
        employment_types=[],
        sites=["hh"],
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        preview_resp = await client.post(f"/api/filters/{vf.id}/preview")
        diagnostics_resp = await client.get(f"/api/filters/{vf.id}/diagnostics")
        health_resp = await client.get("/api/parsers/health")
        logs_resp = await client.get("/api/events/logs")

    assert preview_resp.status_code == 200
    assert preview_resp.json()["items"][0]["filter_id"] == vf.id
    assert diagnostics_resp.status_code == 200
    assert diagnostics_resp.json()["filter_id"] == vf.id
    assert health_resp.status_code == 200
    assert logs_resp.status_code == 200
    assert logs_resp.json()[0]["type"] == "check_started"


@pytest.mark.asyncio
async def test_hashed_web_password_login(db):
    original_password = settings.WEB_PASSWORD
    original_hash = settings.WEB_PASSWORD_HASH
    settings.WEB_PASSWORD = ""
    settings.WEB_PASSWORD_HASH = hash_password("secret-pass")
    try:
        secured_app = create_web_app(db, scheduler=None)
        transport = ASGITransport(app=secured_app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            bad = await client.post("/api/auth/login", json={"password": "bad-pass"})
            good = await client.post("/api/auth/login", json={"password": "secret-pass"})

        assert bad.status_code == 401
        assert good.status_code == 200
        assert good.json()["token"]
    finally:
        settings.WEB_PASSWORD = original_password
        settings.WEB_PASSWORD_HASH = original_hash


@pytest.mark.asyncio
async def test_logout_invalidates_existing_token(db):
    original_password = settings.WEB_PASSWORD
    settings.WEB_PASSWORD = "secret-pass"
    try:
        secured_app = create_web_app(db, scheduler=None)
        transport = ASGITransport(app=secured_app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            login = await client.post("/api/auth/login", json={"password": "secret-pass"})
            token = login.json()["token"]
            ok_before = await client.get("/api/config", headers={"Authorization": f"Bearer {token}"})
            logout = await client.post("/api/auth/logout", headers={"Authorization": f"Bearer {token}"})
            denied_after = await client.get("/api/config", headers={"Authorization": f"Bearer {token}"})

        assert ok_before.status_code == 200
        assert logout.status_code == 200
        assert denied_after.status_code == 401
    finally:
        settings.WEB_PASSWORD = original_password


@pytest.mark.asyncio
async def test_security_headers_and_hash_password_endpoint(app, db):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        config_resp = await client.get("/api/config")
        hash_resp = await client.post("/api/auth/hash-password", json={"password": "long-secret"})

    assert config_resp.headers["x-content-type-options"] == "nosniff"
    assert config_resp.headers["x-frame-options"] == "DENY"
    assert hash_resp.status_code == 200
    assert hash_resp.json()["hash"].startswith("pbkdf2_sha256$")


@pytest.mark.asyncio
async def test_delivery_status_and_filter_performance_api(db):
    app = create_web_app(db, scheduler=FakeScheduler())
    user = await db.get_or_create_user(telegram_id=777)
    vf = await db.create_filter(
        user_id=user.id,
        name="Performance",
        keywords=["Python"],
        city=None,
        salary_min=None,
        salary_max=None,
        employment_types=[],
        sites=["hh"],
    )

    from scrapers.base import VacancyData
    vac = await db.add_vacancy(VacancyData(source="hh", source_id="perf", title="Python Developer", url="url"))
    await db.mark_sent(user.id, vac.id, filter_id=vf.id)
    await db.enqueue_telegram_delivery(user.id, user.telegram_id, vac.id, "hh", "url", "message")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        delivery_resp = await client.get("/api/delivery/status")
        performance_resp = await client.get("/api/filters/performance")

    assert delivery_resp.status_code == 200
    assert delivery_resp.json()["pending"] == 1
    assert performance_resp.status_code == 200
    assert performance_resp.json()[0]["filter_name"] == "Performance"


@pytest.mark.asyncio
async def test_delivery_recent_retry_and_cleanup_api(db):
    app = create_web_app(db, scheduler=None)
    user = await db.get_or_create_user(telegram_id=778)

    from scrapers.base import VacancyData
    vac = await db.add_vacancy(VacancyData(source="hh", source_id="delivery_retry", title="Python Developer", url="url"))
    item = await db.enqueue_telegram_delivery(user.id, user.telegram_id, vac.id, "hh", "url", "message")
    for _ in range(10):
        await db.mark_telegram_delivery_failed(item.id, "network")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        recent_resp = await client.get("/api/delivery/recent")
        retry_resp = await client.post("/api/delivery/retry")
        cleanup_resp = await client.post("/api/delivery/cleanup")

    assert recent_resp.status_code == 200
    assert recent_resp.json()[0]["status"] == "failed"
    assert retry_resp.status_code == 200
    assert retry_resp.json()["restored"] == 1
    assert cleanup_resp.status_code == 200
    assert cleanup_resp.json()["ok"] is True


@pytest.mark.asyncio
async def test_backup_export_api(db):
    app = create_web_app(db, scheduler=None)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/backup/export")
        list_resp = await client.get("/api/backup/list")

    assert resp.status_code == 200
    assert resp.json()["version"] == 1
    assert "filters" in resp.json()
    assert list_resp.status_code == 200
    assert isinstance(list_resp.json(), list)


@pytest.mark.asyncio
async def test_bad_vacancy_feedback_updates_filter_exclusions(app, db):
    user = await db.get_or_create_user(telegram_id=123)
    vf = await db.create_filter(
        user_id=user.id,
        name="Support",
        keywords=["техподдержка"],
        city=None,
        salary_min=None,
        salary_max=None,
        employment_types=[],
        sites=["hh"],
    )

    from scrapers.base import VacancyData
    vac = await db.add_vacancy(VacancyData(source="hh", source_id="bad_feedback", title="Врач-невролог", url="url"))

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            f"/api/vacancies/{vac.id}/feedback",
            json={"filter_id": vf.id, "action": "exclude_noise"},
        )

    assert resp.status_code == 200
    assert "врач" in resp.json()["applied"]
    updated = await db.get_filter(vf.id)
    assert "врач" in updated.get_exclude_keywords()


@pytest.mark.asyncio
async def test_filter_recommendations_endpoint(db):
    scheduler = FakeScheduler()
    app = create_web_app(db, scheduler=scheduler)
    user = await db.get_or_create_user(telegram_id=1)
    vf = await db.create_filter(
        user_id=user.id,
        name="Recommendations",
        keywords=["Python"],
        city=None,
        salary_min=None,
        salary_max=None,
        employment_types=[],
        sites=["hh"],
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get(f"/api/filters/{vf.id}/recommendations")

    assert resp.status_code == 200
    assert resp.json()["filter_id"] == vf.id
