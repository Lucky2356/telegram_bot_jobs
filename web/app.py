import asyncio
import uvicorn
from pydantic import BaseModel
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from core.config import settings
from core.database.repository import Database
from core.scheduler import Scheduler
from bot.keyboards import EMPLOYMENT_TYPES, SITES, KEYWORDS_BY_GROUP, CITIES, SALARIES


class FilterUpdate(BaseModel):
    name: str
    keywords: list[str]
    city: str | None = None
    salary_min: int | None = None
    salary_max: int | None = None
    employment_types: list[str]
    sites: list[str]


def create_web_app(db: Database, scheduler: Scheduler | None = None) -> FastAPI:
    app = FastAPI(title="Job Bot Dashboard")
    templates = Jinja2Templates(directory="web/templates")

    @app.get("/", response_class=HTMLResponse)
    async def dashboard(request: Request):
        filters = await db.get_all_active_filters()
        history = await db.get_recent_sent(limit=30)
        return templates.TemplateResponse(
            request, "index.html",
            {
                "filters": filters,
                "history": history,
                "employment_types": EMPLOYMENT_TYPES,
                "sites": SITES,
                "keyword_groups": KEYWORDS_BY_GROUP,
                "cities": CITIES,
                "salaries": SALARIES,
            },
        )

    @app.get("/api/filters")
    async def api_filters():
        filters = await db.get_all_active_filters()
        return [
            {
                "id": vf.id,
                "name": vf.name,
                "keywords": vf.get_keywords(),
                "city": vf.city,
                "salary_min": vf.salary_min,
                "salary_max": vf.salary_max,
                "employment_types": vf.get_employment_types(),
                "sites": vf.get_sites(),
                "active": vf.active,
            }
            for vf in filters
        ]

    @app.get("/api/filters/{filter_id}")
    async def api_get_filter(filter_id: int):
        vf = await db.get_filter(filter_id)
        if vf is None:
            return {"ok": False, "message": "Filter not found"}
        return {
            "id": vf.id,
            "name": vf.name,
            "keywords": vf.get_keywords(),
            "city": vf.city,
            "salary_min": vf.salary_min,
            "salary_max": vf.salary_max,
            "employment_types": vf.get_employment_types(),
            "sites": vf.get_sites(),
            "active": vf.active,
        }

    @app.put("/api/filters/{filter_id}")
    async def api_update_filter(filter_id: int, data: FilterUpdate):
        vf = await db.update_filter(
            filter_id=filter_id,
            name=data.name,
            keywords=data.keywords,
            city=data.city,
            salary_min=data.salary_min,
            salary_max=data.salary_max,
            employment_types=data.employment_types,
            sites=data.sites,
        )
        if vf is None:
            return {"ok": False, "message": "Filter not found"}, 404
        return {"ok": True, "filter": {
            "id": vf.id,
            "name": vf.name,
            "keywords": vf.get_keywords(),
            "city": vf.city,
            "salary_min": vf.salary_min,
            "salary_max": vf.salary_max,
            "employment_types": vf.get_employment_types(),
            "sites": vf.get_sites(),
            "active": vf.active,
        }}

    @app.post("/api/filters/{filter_id}/toggle")
    async def api_toggle(filter_id: int):
        active = await db.toggle_filter(filter_id)
        return {"ok": True, "active": active}

    @app.delete("/api/filters/{filter_id}")
    async def api_delete(filter_id: int):
        await db.delete_filter(filter_id)
        return {"ok": True}

    @app.post("/api/check_now")
    async def api_check_now():
        if scheduler:
            asyncio.create_task(scheduler.run_check())
            return {"ok": True, "message": "Check started"}
        return {"ok": False, "message": "Scheduler not available"}

    @app.get("/api/history")
    async def api_history():
        history = await db.get_recent_sent(limit=50)
        return [
            {
                "vacancy_title": v.title,
                "company": v.company,
                "salary": v.salary_text,
                "source": v.source,
                "url": v.url,
                "sent_at": sv.sent_at.isoformat() if sv.sent_at else None,
            }
            for sv, v, u in history
        ]

    return app


async def run_web(db: Database, scheduler: Scheduler | None = None):
    app = create_web_app(db, scheduler)
    config = uvicorn.Config(
        app,
        host=settings.WEB_HOST,
        port=settings.WEB_PORT,
        log_level="info",
    )
    server = uvicorn.Server(config)
    await server.serve()
