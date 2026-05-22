import pytest
from httpx import AsyncClient, ASGITransport
from core.database.repository import Database
from web.app import create_web_app


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
