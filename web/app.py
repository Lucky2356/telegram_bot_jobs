import asyncio
import json
import os
import logging
import shutil
from collections import defaultdict, deque
from datetime import datetime, timezone
from pathlib import Path
from time import monotonic
import uvicorn
from pydantic import BaseModel
from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse, StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.status import HTTP_401_UNAUTHORIZED
from core.config import settings
from core.database.repository import Database
from core.scheduler import Scheduler
from bot.keyboards import EMPLOYMENT_TYPES, SITES, KEYWORDS_BY_GROUP, CITIES, SALARIES, EXPERIENCE
from sqlalchemy.engine import make_url
from web.auth import create_token, password_is_valid, verify_token


REACT_BUILD_DIR = os.path.join(os.path.dirname(__file__), "frontend", "dist")


def _parse_cors_origins() -> list[str]:
    raw_origins = settings.WEB_CORS_ORIGINS.strip()
    if not raw_origins or raw_origins == "*":
        return ["*"]
    return [origin.strip() for origin in raw_origins.split(",") if origin.strip()]


class BlocklistAdd(BaseModel):
    pattern: str
    type: str = "company"


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


class FiltersImport(BaseModel):
    filters: list[FilterUpdate]
    replace: bool = False


class VacancyFeedback(BaseModel):
    filter_id: int | None = None
    action: str = "exclude_noise"


def _clean_unique(values: list[str]) -> list[str]:
    cleaned = [value.strip() for value in values if value and value.strip()]
    return list(dict.fromkeys(cleaned))


def _normalize_filter_payload(data: FilterUpdate) -> tuple[dict | None, JSONResponse | None]:
    keywords = _clean_unique(data.keywords)
    exclude_keywords = _clean_unique(data.exclude_keywords)
    sites = _clean_unique(data.sites) or list(SITES.keys())
    employment_types = _clean_unique(data.employment_types)
    name = data.name.strip()
    valid_sites = set(SITES)
    valid_employment = set(EMPLOYMENT_TYPES)

    if not name:
        return None, JSONResponse({"ok": False, "message": "Введите название фильтра"}, status_code=400)
    if not keywords:
        return None, JSONResponse({"ok": False, "message": "Выберите или введите ключевые слова"}, status_code=400)
    if any(site not in valid_sites for site in sites):
        return None, JSONResponse({"ok": False, "message": "Неизвестный источник вакансий"}, status_code=400)
    if data.city is not None and data.city not in CITIES:
        return None, JSONResponse({"ok": False, "message": "Неизвестный город"}, status_code=400)
    if data.experience is not None and data.experience not in EXPERIENCE:
        return None, JSONResponse({"ok": False, "message": "Неизвестный опыт работы"}, status_code=400)
    if any(emp not in valid_employment for emp in employment_types):
        return None, JSONResponse({"ok": False, "message": "Неизвестный тип занятости"}, status_code=400)
    if data.salary_min is not None and data.salary_max is not None and data.salary_min > data.salary_max:
        return None, JSONResponse({"ok": False, "message": "Минимальная зарплата не может быть больше максимальной"}, status_code=400)
    if (data.salary_min is not None and data.salary_min < 0) or (data.salary_max is not None and data.salary_max < 0):
        return None, JSONResponse({"ok": False, "message": "Зарплата не может быть отрицательной"}, status_code=400)

    return {
        "name": name,
        "keywords": keywords,
        "city": data.city,
        "salary_min": data.salary_min,
        "salary_max": data.salary_max,
        "employment_types": employment_types,
        "sites": sites,
        "exclude_keywords": exclude_keywords,
        "experience": data.experience,
    }, None


def _serialize_dt(value):
    return value.isoformat() if value else None


def _sqlite_database_path() -> Path | None:
    try:
        url = make_url(settings.DATABASE_URL)
    except Exception:
        return None
    if not url.drivername.startswith("sqlite"):
        return None
    database = url.database
    if not database or database == ":memory:":
        return None
    return Path(database).resolve()


def _is_recent(value, ttl_seconds: int) -> bool:
    if not value:
        return False
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return (datetime.now(timezone.utc) - value).total_seconds() <= ttl_seconds


def _config_warnings() -> list[dict[str, str]]:
    warnings = []
    if settings.WEB_HOST in {"0.0.0.0", "::"} and not (settings.WEB_PASSWORD or settings.WEB_PASSWORD_HASH):
        warnings.append({"level": "high", "message": "Веб-панель открыта наружу без пароля"})
    if settings.WEB_CORS_ORIGINS.strip() == "*":
        warnings.append({"level": "medium", "message": "WEB_CORS_ORIGINS=* лучше заменить на конкретные origin"})
    if not settings.JWT_SECRET:
        warnings.append({"level": "medium", "message": "JWT_SECRET не задан, используется локальный .jwt_secret"})
    if settings.WEB_PASSWORD and not settings.WEB_PASSWORD_HASH:
        warnings.append({"level": "low", "message": "WEB_PASSWORD лучше заменить на WEB_PASSWORD_HASH"})
    if not settings.SUPERJOB_API_KEY:
        warnings.append({"level": "low", "message": "SuperJob API key не настроен"})
    if not (settings.HH_CLIENT_ID and settings.HH_CLIENT_SECRET):
        warnings.append({"level": "low", "message": "HH OAuth не настроен, hh.ru может ограничивать выдачу"})
    return warnings


def _suggest_exclusions_from_title(title: str) -> list[str]:
    noise = (
        "врач", "невролог", "медицин", "медсестр", "фармацевт", "продавец",
        "кассир", "курьер", "водитель", "грузчик", "повар", "охранник",
    )
    text = title.casefold()
    return [word for word in noise if word in text][:5]


async def _get_first_user(db: Database):
    real_user = await db.get_first_real_user()
    if real_user is not None:
        web_user = await db.get_user_by_telegram_id(0)
        if web_user is not None and web_user.id != real_user.id:
            await db.merge_user_data(source_user_id=web_user.id, target_user_id=real_user.id)
            async with db.session_factory() as session:
                await session.delete(web_user)
                await session.commit()
        return real_user
    return await db.get_or_create_user(telegram_id=0, username="web_user")


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
    app.state.background_tasks = set()
    app.state.auth_token_version = 0
    rate_buckets = defaultdict(deque)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_parse_cors_origins(),
        allow_methods=["*"],
        allow_headers=["*"],
    )
    templates = Jinja2Templates(directory="web/templates")

    def _client_ip(request: Request) -> str:
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",", 1)[0].strip()
        return request.client.host if request.client else "unknown"

    def _is_rate_limited(key: str, limit: int) -> bool:
        if limit <= 0:
            return False
        now = monotonic()
        window = max(1, settings.WEB_RATE_LIMIT_WINDOW_SECONDS)
        bucket = rate_buckets[key]
        while bucket and now - bucket[0] > window:
            bucket.popleft()
        if len(bucket) >= limit:
            return True
        bucket.append(now)
        return False

    def _rate_limit_response() -> JSONResponse:
        return JSONResponse({"ok": False, "message": "Too many requests"}, status_code=429)

    @app.middleware("http")
    async def static_cache_middleware(request: Request, call_next):
        response = await call_next(request)
        path = request.url.path
        if path.startswith("/assets/"):
            response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
        elif path == "/" or path.endswith(".html"):
            response.headers["Cache-Control"] = "no-cache"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "connect-src 'self'; "
            "frame-ancestors 'none'; "
            "base-uri 'self';"
        )
        return response

    # Auth middleware
    if settings.WEB_PASSWORD or settings.WEB_PASSWORD_HASH:
        @app.middleware("http")
        async def auth_middleware(request: Request, call_next):
            path = request.url.path
            EXCLUDED_PREFIXES = ("/api/events",)
            EXCLUDED_PATHS = {"/api/health", "/api/auth/login", "/api/auth/hash-password"}
            if path.startswith("/api/") and path not in EXCLUDED_PATHS and not path.startswith(EXCLUDED_PREFIXES):
                auth = request.headers.get("Authorization", "")
                if not auth.startswith("Bearer ") or not verify_token(auth[7:], app.state.auth_token_version):
                    return HTMLResponse(
                        content=json.dumps({"ok": False, "message": "Unauthorized"}),
                        status_code=HTTP_401_UNAUTHORIZED,
                        headers={"Content-Type": "application/json"},
                    )
            return await call_next(request)

    # Mount React static assets if build exists
    assets_dir = os.path.join(REACT_BUILD_DIR, "assets")
    if os.path.isdir(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/", response_class=HTMLResponse)
    async def dashboard(request: Request):
        return await _serve_react_or_fallback(app, request, templates)

    class LoginData(BaseModel):
        password: str

    @app.post("/api/auth/login")
    async def api_login(data: LoginData, request: Request):
        if _is_rate_limited(f"login:{_client_ip(request)}", settings.WEB_LOGIN_RATE_LIMIT):
            return _rate_limit_response()
        auth_enabled = bool(settings.WEB_PASSWORD or settings.WEB_PASSWORD_HASH)
        if auth_enabled and password_is_valid(data.password):
            return {"ok": True, "token": create_token(app.state.auth_token_version), "ttl": settings.WEB_SESSION_TTL_SECONDS}
        if not auth_enabled:
            return {"ok": True, "token": create_token(app.state.auth_token_version), "ttl": settings.WEB_SESSION_TTL_SECONDS}
        return JSONResponse({"ok": False, "message": "Неверный пароль"}, status_code=HTTP_401_UNAUTHORIZED)

    @app.post("/api/auth/logout")
    async def api_logout():
        app.state.auth_token_version += 1
        return {"ok": True}

    @app.get("/api/auth/session")
    async def api_session():
        return {"ok": True, "ttl": settings.WEB_SESSION_TTL_SECONDS}

    class HashPasswordData(BaseModel):
        password: str

    @app.post("/api/auth/hash-password")
    async def api_hash_password(data: HashPasswordData, request: Request):
        if _is_rate_limited(f"hash_password:{_client_ip(request)}", 3):
            return _rate_limit_response()
        if len(data.password) < 8:
            return JSONResponse({"ok": False, "message": "Password must be at least 8 characters"}, status_code=400)
        from web.auth import hash_password
        return {"ok": True, "hash": hash_password(data.password)}

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

    @app.get("/api/health")
    async def api_health():
        return {
            "ok": True,
            "scheduler": bool(scheduler),
            "checking": scheduler.is_checking if scheduler else False,
            "warnings": _config_warnings(),
        }

    @app.get("/api/config/diagnostics")
    async def api_config_diagnostics():
        return {
            "warnings": _config_warnings(),
            "auth_enabled": bool(settings.WEB_PASSWORD or settings.WEB_PASSWORD_HASH),
            "cors_origins": _parse_cors_origins(),
            "database": make_url(settings.DATABASE_URL).drivername,
            "search_cache_seconds": settings.SEARCH_CACHE_SECONDS,
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
        payload, error = _normalize_filter_payload(data)
        if error:
            return error
        user = await _get_first_user(db)
        vf = await db.create_filter(
            user_id=user.id,
            **payload,
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

    @app.get("/api/filters/export")
    async def api_export_filters():
        filters = await db.get_all_filters()
        return {
            "version": 1,
            "filters": [
                {
                    "name": vf.name,
                    "keywords": vf.get_keywords(),
                    "city": vf.city,
                    "salary_min": vf.salary_min,
                    "salary_max": vf.salary_max,
                    "employment_types": vf.get_employment_types(),
                    "sites": vf.get_sites(),
                    "exclude_keywords": vf.get_exclude_keywords(),
                    "experience": vf.experience,
                }
                for vf in filters
            ],
        }

    @app.post("/api/filters/import")
    async def api_import_filters(data: FiltersImport):
        user = await _get_first_user(db)
        if data.replace:
            for vf in await db.get_all_filters():
                if vf.user_id == user.id:
                    await db.delete_filter(vf.id)
        created = []
        for item in data.filters:
            payload, error = _normalize_filter_payload(item)
            if error:
                return error
            vf = await db.create_filter(user_id=user.id, **payload)
            created.append({
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
            })
        return {"ok": True, "created": created}

    @app.get("/api/filters/performance")
    async def api_filter_performance(days: int = 30):
        days = max(1, min(days, 365))
        return await db.get_filter_performance(days=days)

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
        payload, error = _normalize_filter_payload(data)
        if error:
            return error
        vf = await db.update_filter(
            filter_id=filter_id,
            **payload,
        )
        if vf is None:
            return JSONResponse({"ok": False, "message": "Filter not found"}, status_code=404)
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
        user = await _get_first_user(db)
        vf = await db.get_filter(filter_id)
        if vf is None:
            return JSONResponse({"ok": False, "message": "Filter not found"}, status_code=404)
        if vf.user_id != user.id:
            return JSONResponse({"ok": False, "message": "Forbidden"}, status_code=403)
        active = await db.toggle_filter(filter_id)
        return {"ok": True, "active": active}

    @app.post("/api/filters/{filter_id}/clone")
    async def api_clone_filter(filter_id: int):
        vf = await db.get_filter(filter_id)
        if vf is None:
            return JSONResponse({"ok": False, "message": "Filter not found"}, status_code=404)
        user = await _get_first_user(db)
        if vf.user_id != user.id:
            return JSONResponse({"ok": False, "message": "Forbidden"}, status_code=403)
        cloned = await db.create_filter(
            user_id=user.id,
            name=f"Копия — {vf.name}",
            keywords=vf.get_keywords(),
            city=vf.city,
            salary_min=vf.salary_min,
            salary_max=vf.salary_max,
            employment_types=vf.get_employment_types(),
            sites=vf.get_sites(),
            exclude_keywords=vf.get_exclude_keywords(),
            experience=vf.experience,
        )
        return {"ok": True, "filter": {
            "id": cloned.id,
            "name": cloned.name,
            "keywords": cloned.get_keywords(),
            "city": cloned.city,
            "salary_min": cloned.salary_min,
            "salary_max": cloned.salary_max,
            "employment_types": cloned.get_employment_types(),
            "sites": cloned.get_sites(),
            "exclude_keywords": cloned.get_exclude_keywords(),
            "experience": cloned.experience,
            "active": cloned.active,
        }}

    @app.delete("/api/filters/{filter_id}")
    async def api_delete(filter_id: int):
        user = await _get_first_user(db)
        vf = await db.get_filter(filter_id)
        if vf is None:
            return JSONResponse({"ok": False, "message": "Filter not found"}, status_code=404)
        if vf.user_id != user.id:
            return JSONResponse({"ok": False, "message": "Forbidden"}, status_code=403)
        await db.delete_filter(filter_id)
        return {"ok": True}

    @app.get("/api/events")
    async def api_events(request: Request):
        if not scheduler:
            return StreamingResponse([], media_type="text/event-stream")
        async def event_generator():
            try:
                while True:
                    if await request.is_disconnected():
                        break
                    event = await scheduler.event_queue.get()
                    yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
            except asyncio.CancelledError:
                pass
        return StreamingResponse(event_generator(), media_type="text/event-stream")

    async def _run_task(coro, name: str):
        logging.getLogger(__name__).info("Background task '%s' started", name)
        try:
            await coro
            logging.getLogger(__name__).info("Background task '%s' finished", name)
        except Exception as e:
            logging.getLogger(__name__).error("Background task '%s' failed: %s", name, e, exc_info=True)

    @app.post("/api/check_now")
    async def api_check_now(request: Request, background_tasks: BackgroundTasks):
        if _is_rate_limited(f"check_all:{_client_ip(request)}", settings.WEB_ACTION_RATE_LIMIT):
            return _rate_limit_response()
        if scheduler:
            if hasattr(scheduler, "enqueue_check"):
                status = await scheduler.enqueue_check()
                return {"ok": True, "message": "Проверка поставлена в очередь!", "queue": status}
            background_tasks.add_task(_run_task, scheduler.run_check(), "check_all")
            return {"ok": True, "message": "Проверка запущена!"}
        return {"ok": False, "message": "Scheduler not available"}

    @app.post("/api/filters/{filter_id}/check")
    async def api_check_filter(filter_id: int, request: Request, background_tasks: BackgroundTasks):
        if _is_rate_limited(f"check_filter:{_client_ip(request)}", settings.WEB_ACTION_RATE_LIMIT):
            return _rate_limit_response()
        user = await _get_first_user(db)
        vf = await db.get_filter(filter_id)
        if vf is None:
            return JSONResponse({"ok": False, "message": "Filter not found"}, status_code=404)
        if vf.user_id != user.id:
            return JSONResponse({"ok": False, "message": "Forbidden"}, status_code=403)
        if scheduler:
            if hasattr(scheduler, "enqueue_check"):
                status = await scheduler.enqueue_check(filter_id)
                return {"ok": True, "message": "Проверка фильтра поставлена в очередь!", "queue": status}
            background_tasks.add_task(_run_task, scheduler.run_check_for_filter(filter_id), f"check_filter_{filter_id}")
            return {"ok": True, "message": "Проверка фильтра запущена!"}
        return {"ok": False, "message": "Scheduler not available"}

    @app.get("/api/tasks/status")
    async def api_tasks_status():
        if scheduler and hasattr(scheduler, "get_check_queue_status"):
            return scheduler.get_check_queue_status()
        return {"queued": 0, "worker_running": False, "checking": False}

    @app.post("/api/filters/{filter_id}/preview")
    async def api_preview_filter(filter_id: int):
        if not scheduler:
            return {"items": [], "checked_at": None, "checking": False}
        items = await scheduler.preview_filter(filter_id)
        return {"items": items, "checked_at": scheduler.last_results_time, "checking": False}

    @app.get("/api/filters/{filter_id}/diagnostics")
    async def api_filter_diagnostics(filter_id: int):
        if not scheduler:
            return JSONResponse({"ok": False, "message": "Scheduler not available"}, status_code=503)
        data = await scheduler.diagnose_filter(filter_id)
        if not data.get("ok"):
            return JSONResponse(data, status_code=404)
        return data

    @app.get("/api/parsers/health")
    async def api_parsers_health():
        if not scheduler:
            return []
        stored = {item.site: item for item in await db.get_parser_health()}
        if stored and all(_is_recent(item.checked_at, settings.WEB_PARSER_HEALTH_CACHE_SECONDS) for item in stored.values()):
            return [
                {
                    "site": item.site,
                    "ok": item.ok,
                    "count": item.count,
                    "latency_ms": item.latency_ms,
                    "error": item.error,
                    "checked_at": _serialize_dt(item.checked_at),
                    "cached": True,
                }
                for item in stored.values()
            ]
        results = []
        for site in SITES:
            scraper = scheduler._get_scraper(site)
            if not scraper:
                results.append({"site": site, "ok": False, "count": 0, "error": "not configured"})
                continue
            started = monotonic()
            try:
                vacancies = await scraper.search(["Python"], city=None)
                results.append({
                    "site": site,
                    "ok": True,
                    "count": len(vacancies),
                    "latency_ms": round((monotonic() - started) * 1000),
                })
            except Exception as e:
                results.append({
                    "site": site,
                    "ok": False,
                    "count": 0,
                    "latency_ms": round((monotonic() - started) * 1000),
                    "error": str(e),
                })
            await db.upsert_parser_health(
                site=results[-1]["site"],
                ok=results[-1]["ok"],
                count=results[-1]["count"],
                latency_ms=results[-1].get("latency_ms"),
                error=results[-1].get("error"),
            )
        return results

    @app.get("/api/events/logs")
    async def api_event_logs():
        return scheduler.get_event_log() if scheduler else []

    @app.get("/api/sources/health-history")
    async def api_sources_health_history():
        items = await db.get_parser_health()
        return [
            {
                "site": item.site,
                "ok": item.ok,
                "count": item.count,
                "latency_ms": item.latency_ms,
                "error": item.error,
                "checked_at": _serialize_dt(item.checked_at),
            }
            for item in items
        ]

    @app.get("/api/delivery/status")
    async def api_delivery_status():
        return await db.get_telegram_delivery_stats()

    @app.get("/api/delivery/recent")
    async def api_delivery_recent(limit: int = 30):
        limit = max(1, min(limit, 100))
        items = await db.get_recent_telegram_deliveries(limit=limit)
        return [
            {
                "id": item.id,
                "chat_id": item.chat_id,
                "vacancy_id": item.vacancy_id,
                "source": item.source,
                "url": item.url,
                "status": item.status,
                "attempts": item.attempts,
                "last_error": item.last_error,
                "created_at": _serialize_dt(item.created_at),
                "updated_at": _serialize_dt(item.updated_at),
            }
            for item in items
        ]

    @app.post("/api/delivery/retry")
    async def api_delivery_retry():
        if not scheduler:
            restored = await db.retry_failed_telegram_deliveries()
            return {"restored": restored, **await db.get_telegram_delivery_stats()}
        return await scheduler.retry_telegram_delivery_queue()

    @app.post("/api/delivery/cleanup")
    async def api_delivery_cleanup(days: int = 14):
        days = max(1, min(days, 365))
        deleted = await db.cleanup_telegram_deliveries(days=days)
        return {"ok": True, "deleted": deleted, **await db.get_telegram_delivery_stats()}

    @app.post("/api/backup")
    async def api_backup():
        db_path = _sqlite_database_path()
        if db_path is None or not db_path.exists():
            return JSONResponse({"ok": False, "message": "SQLite database file not found"}, status_code=400)
        backup_dir = Path(settings.BACKUP_DIR)
        backup_dir.mkdir(parents=True, exist_ok=True)
        name = f"vacancies-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}.db"
        target = backup_dir / name
        shutil.copy2(db_path, target)
        return {"ok": True, "file": str(target), "size": target.stat().st_size}

    @app.get("/api/backup/list")
    async def api_backup_list():
        backup_dir = Path(settings.BACKUP_DIR)
        if not backup_dir.exists():
            return []
        return [
            {
                "file": str(path),
                "name": path.name,
                "size": path.stat().st_size,
                "modified_at": datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat(),
            }
            for path in sorted(backup_dir.glob("*.db"), key=lambda item: item.stat().st_mtime, reverse=True)
        ][:50]

    @app.get("/api/backup/export")
    async def api_backup_export():
        filters = await db.get_all_filters()
        blocks = await db.get_blocklist()
        saved = await db.get_saved_vacancies()
        history = await db.get_recent_sent(limit=500)
        return {
            "version": 1,
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "filters": [
                {
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
            ],
            "blocklist": [
                {"pattern": item.pattern, "type": item.type, "created_at": _serialize_dt(item.created_at)}
                for item in blocks
            ],
            "saved": [
                {
                    "title": vacancy.title,
                    "company": vacancy.company,
                    "source": vacancy.source,
                    "url": vacancy.url,
                    "saved_at": _serialize_dt(saved_item.saved_at),
                }
                for saved_item, vacancy in saved
            ],
            "history": [
                {
                    "title": vacancy.title,
                    "company": vacancy.company,
                    "source": vacancy.source,
                    "url": vacancy.url,
                    "filter_name": vf.name if vf else None,
                    "sent_at": _serialize_dt(sent.sent_at),
                }
                for sent, vacancy, _user, vf in history
            ],
        }

    @app.get("/api/saved")
    async def api_saved():
        user = await _get_first_user(db)
        saved = await db.get_saved_vacancies(user.id)
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
        user = await _get_first_user(db)
        blocks = await db.get_blocklist(user.id)
        return [
            {"id": b.id, "pattern": b.pattern, "type": b.type}
            for b in blocks
        ]

    @app.post("/api/blocklist/{block_id}/delete")
    async def api_blocklist_delete(block_id: int):
        user = await _get_first_user(db)
        blocks = await db.get_blocklist(user.id)
        if not any(b.id == block_id for b in blocks):
            return JSONResponse({"ok": False, "message": "Not found"}, status_code=404)
        await db.remove_blocklist_by_id(block_id)
        return {"ok": True}

    @app.post("/api/blocklist/add")
    async def api_blocklist_add(data: BlocklistAdd):
        pattern = data.pattern.strip()
        if not pattern:
            return JSONResponse({"ok": False, "message": "Pattern is required"}, status_code=400)
        if data.type not in {"company", "keyword"}:
            return JSONResponse({"ok": False, "message": "Invalid blocklist type"}, status_code=400)
        user = await _get_first_user(db)
        await db.add_blocklist(user.id, pattern, data.type)
        return {"ok": True}

    @app.post("/api/vacancies/{vacancy_id}/save")
    async def api_vacancy_save(vacancy_id: int):
        user = await _get_first_user(db)
        vac = await db.get_vacancy_by_id(vacancy_id)
        if not vac:
            return JSONResponse({"ok": False, "message": "Vacancy not found"}, status_code=404)
        await db.save_vacancy(user.id, vacancy_id)
        return {"ok": True}

    @app.post("/api/vacancies/{vacancy_id}/unsave")
    async def api_vacancy_unsave(vacancy_id: int):
        user = await _get_first_user(db)
        await db.unsave_vacancy(user.id, vacancy_id)
        return {"ok": True}

    @app.post("/api/vacancies/{vacancy_id}/block")
    async def api_vacancy_block(vacancy_id: int):
        user = await _get_first_user(db)
        vac = await db.get_vacancy_by_id(vacancy_id)
        if not vac:
            return JSONResponse({"ok": False, "message": "Vacancy not found"}, status_code=404)
        if vac.company:
            await db.add_blocklist(user.id, vac.company, "company")
        else:
            await db.add_blocklist(user.id, vac.title, "keyword")
        return {"ok": True}

    @app.post("/api/vacancies/{vacancy_id}/feedback")
    async def api_vacancy_feedback(vacancy_id: int, data: VacancyFeedback):
        user = await _get_first_user(db)
        vac = await db.get_vacancy_by_id(vacancy_id)
        if not vac:
            return JSONResponse({"ok": False, "message": "Vacancy not found"}, status_code=404)

        suggestions = _suggest_exclusions_from_title(vac.title)
        applied: list[str] = []
        if data.action == "block_company" and vac.company:
            await db.add_blocklist(user.id, vac.company, "company")
            applied.append(f"company:{vac.company}")
        elif data.action == "exclude_noise" and data.filter_id and suggestions:
            vf = await db.get_filter(data.filter_id)
            if vf is None or vf.user_id != user.id:
                return JSONResponse({"ok": False, "message": "Filter not found"}, status_code=404)
            await db.append_filter_exclude_keywords(data.filter_id, suggestions)
            applied.extend(suggestions)
        elif data.action == "block_title":
            await db.add_blocklist(user.id, vac.title, "keyword")
            applied.append(f"title:{vac.title}")
        else:
            return {"ok": True, "applied": [], "suggestions": suggestions}
        return {"ok": True, "applied": applied, "suggestions": suggestions}

    @app.get("/api/filters/{filter_id}/recommendations")
    async def api_filter_recommendations(filter_id: int):
        if not scheduler:
            return {"filter_id": filter_id, "recommendations": []}
        diagnostics = await scheduler.diagnose_filter(filter_id)
        if not diagnostics.get("ok"):
            return JSONResponse(diagnostics, status_code=404)
        recommendations = []
        total_raw = sum(site.get("raw", 0) for site in diagnostics.get("sites", []))
        total_passed = sum(site.get("passed", 0) for site in diagnostics.get("sites", []))
        total_noise = sum(site.get("rejected", {}).get("noise", 0) for site in diagnostics.get("sites", []))
        total_keyword = sum(site.get("rejected", {}).get("keyword", 0) for site in diagnostics.get("sites", []))
        if total_raw > 0 and total_passed == 0:
            recommendations.append({
                "type": "no_results",
                "message": "Фильтр получает вакансии от источников, но все отсекает. Проверь город, зарплату и исключения.",
            })
        if total_noise >= 3:
            recommendations.append({
                "type": "noise",
                "message": "Много нерелевантных вакансий. Добавь шумовые слова в исключения или используй более точную должность.",
            })
        if total_raw > 0 and total_keyword / total_raw > 0.8:
            recommendations.append({
                "type": "keywords",
                "message": "Большинство вакансий не проходит по ключевым словам. Возможно, запрос слишком широкий для источников.",
            })
        return {"filter_id": filter_id, "recommendations": recommendations, "diagnostics": diagnostics}

    @app.delete("/api/saved/{saved_id}")
    async def api_saved_delete(saved_id: int):
        user = await _get_first_user(db)
        sv = await db.get_saved_vacancy_by_id(saved_id)
        if not sv:
            return JSONResponse({"ok": False, "message": "Not found"}, status_code=404)
        if sv.user_id != user.id:
            return JSONResponse({"ok": False, "message": "Forbidden"}, status_code=403)
        await db.unsave_vacancy(sv.user_id, sv.vacancy_id)
        return {"ok": True}

    @app.get("/api/status")
    async def api_status():
        return {
            "hh": bool(settings.HH_CLIENT_ID and settings.HH_CLIENT_SECRET),
            "superjob": bool(settings.SUPERJOB_API_KEY),
            "trudvsem": True,
            "rabota": True,
            "habr": True,
        }

    @app.get("/api/results")
    async def api_results():
        checking = scheduler.is_checking if scheduler else False
        if scheduler:
            items = scheduler.get_last_results()
            if items:
                return {"items": items, "checked_at": scheduler.last_results_time, "checking": checking}
        return {"items": [], "checked_at": None, "checking": False}

    @app.get("/api/history")
    async def api_history(page: int = 1, limit: int = 20):
        page = max(1, page)
        limit = max(1, min(limit, 100))
        offset_val = (page - 1) * limit
        history = await db.get_recent_sent(limit=limit, offset=offset_val)
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


async def run_web(db: Database, scheduler: Scheduler | None = None, shutdown_event: asyncio.Event | None = None):
    app = create_web_app(db, scheduler)
    config = uvicorn.Config(
        app,
        host=settings.WEB_HOST,
        port=settings.WEB_PORT,
        log_level="info",
    )
    server = uvicorn.Server(config)
    shutdown_task = None
    if shutdown_event is not None:
        async def _watch_shutdown():
            await shutdown_event.wait()
            server.should_exit = True

        shutdown_task = asyncio.create_task(_watch_shutdown())
    try:
        await server.serve()
    finally:
        if shutdown_task is not None:
            shutdown_task.cancel()
            await asyncio.gather(shutdown_task, return_exceptions=True)
