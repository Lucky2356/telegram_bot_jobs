import asyncio
import os
import uvicorn
from pydantic import BaseModel
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from core.config import settings
from core.database.repository import Database
from core.scheduler import Scheduler
from bot.keyboards import EMPLOYMENT_TYPES, SITES, KEYWORDS_BY_GROUP, CITIES, SALARIES, EXPERIENCE


REACT_BUILD_DIR = os.path.join(os.path.dirname(__file__), "frontend", "dist")


class FilterUpdate(BaseModel):
    name: str
    keywords: list[str]
    city: str | None = None
    salary_min: int | None = None
    salary_max: int | None = None
    employment_types: list[str]
    sites: list[str]
    experience: str | None = None
    exclude_keywords: list[str] = []


async def _get_first_user(db: Database):
    from sqlalchemy import select as sa_select
    from core.database.models import User as UserModel
    async with db.session_factory() as session:
        user = (await session.execute(sa_select(UserModel))).scalar_one_or_none()
        if user is None:
            user = UserModel(telegram_id=0, username="web_user")
            session.add(user)
            await session.commit()
            await session.refresh(user)
        return user


async def _serve_react_or_fallback(app: FastAPI, request: Request, templates: Jinja2Templates):
    """Serve React build if available, otherwise fallback to Jinja2 template."""
    index_path = os.path.join(REACT_BUILD_DIR, "index.html")
    if os.path.isfile(index_path):
        return FileResponse(index_path)
    # Fallback to old Jinja2 template
    filters = await app.state.db.get_all_active_filters()
    history = await app.state.db.get_recent_sent(limit=50)
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


def create_web_app(db: Database, scheduler: Scheduler | None = None) -> FastAPI:
    app = FastAPI(title="Job Bot Dashboard")
    app.state.db = db
    templates = Jinja2Templates(directory="web/templates")

    # Mount React static assets if build exists
    assets_dir = os.path.join(REACT_BUILD_DIR, "assets")
    if os.path.isdir(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/", response_class=HTMLResponse)
    async def dashboard(request: Request):
        return await _serve_react_or_fallback(app, request, templates)

    @app.get("/api/config")
    async def api_config():
        return {
            "employment_types": EMPLOYMENT_TYPES,
            "sites": SITES,
            "cities": CITIES,
            "experiences": EXPERIENCE,
            "salaries": SALARIES,
            "keyword_groups": KEYWORDS_BY_GROUP,
        }

    @app.get("/api/stats")
    async def api_stats():
        total_filters = await db.get_filter_count()
        active_filters = await db.get_active_filter_count()
        total_vacancies = await db.get_total_vacancy_count()
        total_sent = await db.get_total_sent_count()
        sent_by_source = await db.get_sent_by_source()
        sent_by_day = await db.get_sent_by_day(30)
        sent_last_7d = sum(
            d["count"] for d in await db.get_sent_by_day(7)
        )
        sent_last_30d = sum(d["count"] for d in sent_by_day)
        return {
            "total_filters": total_filters,
            "active_filters": active_filters,
            "total_vacancies": total_vacancies,
            "total_sent": total_sent,
            "sent_by_source": sent_by_source,
            "sent_by_day": sent_by_day,
            "sent_last_7d": sent_last_7d,
            "sent_last_30d": sent_last_30d,
        }

    @app.post("/api/filters")
    async def api_create_filter(data: FilterUpdate):
        user = await _get_first_user(db)
        vf = await db.create_filter(
            user_id=user.id if user else 1,
            name=data.name,
            keywords=data.keywords,
            city=data.city,
            salary_min=data.salary_min,
            salary_max=data.salary_max,
            employment_types=data.employment_types,
            sites=data.sites,
            exclude_keywords=data.exclude_keywords,
            experience=data.experience,
        )
        return {"ok": True, "filter": {
            "id": vf.id,
            "name": vf.name,
            "keywords": vf.get_keywords(),
            "city": vf.city,
            "salary_min": vf.salary_min,
            "salary_max": vf.salary_max,
            "employment_types": vf.get_employment_types(),
            "sites": vf.get_sites(),
            "exclude_keywords": vf.get_exclude_keywords(),
            "experience": vf.experience,
            "active": vf.active,
        }}

    @app.get("/api/filters")
    async def api_filters():
        filters = await db.get_all_filters()
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
                "exclude_keywords": vf.get_exclude_keywords(),
                "experience": vf.experience,
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
            "exclude_keywords": vf.get_exclude_keywords(),
            "experience": vf.experience,
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
            exclude_keywords=data.exclude_keywords,
            experience=data.experience,
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
            "exclude_keywords": vf.get_exclude_keywords(),
            "experience": vf.experience,
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
            return {"ok": True, "message": "Проверка запущена!"}
        return {"ok": False, "message": "Scheduler not available"}

    @app.post("/api/filters/{filter_id}/check")
    async def api_check_filter(filter_id: int):
        if scheduler:
            asyncio.create_task(scheduler.run_check_for_filter(filter_id))
            return {"ok": True, "message": "Проверка фильтра запущена!"}
        return {"ok": False, "message": "Scheduler not available"}

    @app.get("/api/saved")
    async def api_saved():
        saved = await db.get_saved_vacancies()
        return [
            {
                "id": sv.id,
                "vacancy_title": v.title,
                "company": v.company,
                "salary_text": v.salary_text,
                "city": v.city,
                "employment_type": v.employment_type,
                "description": v.description,
                "url": v.url,
                "source": v.source,
                "published_at": v.published_at.isoformat() if v.published_at else None,
                "saved_at": sv.saved_at.isoformat() if sv.saved_at else None,
            }
            for sv, v in saved
        ]

    @app.get("/api/blocklist")
    async def api_blocklist():
        blocks = await db.get_blocklist()
        return [
            {"id": b.id, "pattern": b.pattern, "type": b.type}
            for b in blocks
        ]

    @app.post("/api/blocklist/{block_id}/delete")
    async def api_blocklist_delete(block_id: int):
        async with db.session_factory() as session:
            from sqlalchemy import delete as sa_delete
            from core.database.models import Blocklist as BlockModel
            await session.execute(sa_delete(BlockModel).where(BlockModel.id == block_id))
            await session.commit()
        return {"ok": True}

    @app.get("/api/status")
    async def api_status():
        from core.config import settings as app_settings
        return {
            "hh": bool(app_settings.HH_CLIENT_ID and app_settings.HH_CLIENT_SECRET),
            "superjob": bool(app_settings.SUPERJOB_API_KEY),
            "trudvsem": True,
            "rabota": True,
            "habr": True,
        }

    @app.get("/api/results")
    async def api_results():
        if scheduler:
            return {
                "items": scheduler.get_last_results(),
                "checked_at": scheduler.last_results_time,
                "checking": scheduler._lock.locked(),
            }
        return {"items": [], "checked_at": None, "checking": False}

    @app.get("/api/history")
    async def api_history(page: int = 1, limit: int = 20):
        offset = (page - 1) * limit
        history = await db.get_recent_sent(limit=limit)
        return {
            "items": [
                {
                    "vacancy_title": v.title,
                    "company": v.company,
                    "salary": v.salary_text,
                    "source": v.source,
                    "url": v.url,
                    "filter_name": vf.name if vf else None,
                    "sent_at": sv.sent_at.isoformat() if sv.sent_at else None,
                }
                for sv, v, u, vf in history
            ],
            "page": page,
            "has_more": len(history) == limit,
        }

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
