import logging
import asyncio
from collections import deque
from time import monotonic
from aiogram import Bot
from core.database.repository import Database
from scrapers.hh_ru import HHScraper
from scrapers.superjob_ru import SuperJobScraper
from scrapers.trudvsem_ru import TrudvsemScraper
from scrapers.rabota_ru import RabotaRuScraper
from scrapers.habr_career import HabrCareerScraper
from scrapers.base import VacancyData, BaseScraper
from bot.messages import format_vacancy_card
from bot.keyboards import build_vacancy_actions_keyboard, CITIES, get_synonyms
from utils.text_cleaner import clean_html
from core.config import settings

logger = logging.getLogger(__name__)


class Scheduler:
    def __init__(self, db: Database, bot: Bot):
        self.db = db
        self.bot = bot
        self._scrapers: dict[str, BaseScraper] = {}
        self._user_buffers: dict[int, list[tuple[int, str, str, str]]] = {}
        self._lock = asyncio.Lock()
        self.last_results: dict[int, list[tuple[int, str | None, VacancyData, int | None]]] = {}
        self.last_results_time: str | None = None
        self.event_queue: asyncio.Queue[dict] = asyncio.Queue(maxsize=100)
        self.event_log: deque[dict] = deque(maxlen=200)
        self._telegram_retry_queue: deque[tuple[int, str, str, str, str]] = deque(maxlen=1000)
        self._query_cache: dict[tuple[str, str, str | None], tuple[float, list[VacancyData]]] = {}
        self._check_queue: asyncio.Queue[tuple[str, int | None]] = asyncio.Queue(maxsize=50)
        self._check_worker_task: asyncio.Task | None = None

    @property
    def is_checking(self) -> bool:
        return self._lock.locked()

    async def _publish(self, event: dict):
        self.event_log.append({"ts": monotonic(), **event})
        try:
            self.event_queue.put_nowait(event)
        except asyncio.QueueFull:
            pass

    def get_event_log(self) -> list[dict]:
        return list(self.event_log)[-100:]

    MAX_RESULTS = 500
    NOISE_TITLE_WORDS = (
        "врач", "невролог", "медсестр", "фармацевт", "провизор", "стоматолог",
        "курьер", "водитель", "грузчик", "повар", "продавец", "кассир",
        "уборщик", "охранник", "кладовщик", "парикмахер", "мастер маникюра",
    )

    def get_last_results(self) -> list[dict]:
        """Return cached results from the last check as serializable dicts."""
        combined: list[tuple[int, str | None, VacancyData, int | None]] = []
        for items in self.last_results.values():
            combined.extend(items)
        # Keep most recent results capped
        combined = sorted(
            combined[-self.MAX_RESULTS:],
            key=lambda item: getattr(item[2], "_score", 0),
            reverse=True,
        )
        return [
            {
                "id": vac_id,
                "filter_id": filter_id,
                "filter_name": filter_name,
                "title": v.title,
                "company": v.company,
                "salary_text": v.salary_text,
                "city": v.city,
                "employment_type": v.employment_type,
                "experience": v.experience,
                "description": clean_html(v.description),
                "url": v.url,
                "source": v.source,
                "score": getattr(v, "_score", 0),
                "published_at": v.published_at.isoformat() if v.published_at else None,
            }
            for vac_id, filter_name, v, filter_id in combined
        ]

    def _get_scraper(self, site: str) -> BaseScraper | None:
        if site not in self._scrapers:
            cls_map = {
                "hh": HHScraper,
                "superjob": SuperJobScraper,
                "trudvsem": TrudvsemScraper,
                "rabota": RabotaRuScraper,
                "habr": HabrCareerScraper,
            }
            cls = cls_map.get(site)
            if cls:
                self._scrapers[site] = cls()
        return self._scrapers.get(site)

    async def close(self):
        if self._check_worker_task and not self._check_worker_task.done():
            self._check_worker_task.cancel()
            await asyncio.gather(self._check_worker_task, return_exceptions=True)
        for s in self._scrapers.values():
            try:
                await s.close()
            except Exception:
                pass
        self._scrapers.clear()

    def get_check_queue_status(self) -> dict:
        return {
            "queued": self._check_queue.qsize(),
            "worker_running": bool(self._check_worker_task and not self._check_worker_task.done()),
            "checking": self.is_checking,
        }

    async def enqueue_check(self, filter_id: int | None = None) -> dict:
        kind = "filter" if filter_id is not None else "all"
        self._check_queue.put_nowait((kind, filter_id))
        if self._check_worker_task is None or self._check_worker_task.done():
            self._check_worker_task = asyncio.create_task(self._check_queue_worker())
        status = self.get_check_queue_status()
        await self._publish({"type": "check_queued", "kind": kind, "filter_id": filter_id, **status})
        return status

    async def _check_queue_worker(self):
        while not self._check_queue.empty():
            kind, filter_id = await self._check_queue.get()
            try:
                if kind == "filter" and filter_id is not None:
                    await self.run_check_for_filter(filter_id)
                else:
                    await self.run_check()
            finally:
                self._check_queue.task_done()

    async def run_check_for_filter(self, filter_id: int):
        """Check only one specific filter and cache results without sending to Telegram."""
        if self._lock.locked():
            logger.info("Check already running, skipping.")
            return
        async with self._lock:
            from datetime import datetime, timezone
            self._user_buffers.clear()
            self.last_results.clear()
            self.last_results_time = datetime.now(timezone.utc).isoformat()
            await self._publish({"type": "check_started"})
            logger.info("Starting single-filter check for filter %s...", filter_id)
            vf = await self.db.get_filter(filter_id)
            if not vf or not vf.active:
                logger.info("Filter %s not found or inactive.", filter_id)
                await self._publish({"type": "check_complete", "total_found": 0})
                return
            user = await self.db.get_user(vf.user_id)
            if not user:
                await self._publish({"type": "check_complete", "total_found": 0})
                return
            await self._publish({"type": "filter_started", "filter_id": vf.id, "filter_name": vf.name})
            await self._check_filter(vf, user, notify=False)
            found = sum(len(v) for v in self.last_results.values())
            await self._publish({"type": "filter_done", "filter_id": vf.id, "filter_name": vf.name, "found": found})
            await self._publish({"type": "check_complete", "total_found": found})
            logger.info("Single-filter check completed.")

    async def cleanup(self, days: int = 7):
        logger.info("Cleaning up vacancies older than %d days...", days)
        await self.db.cleanup_old_vacancies(days)
        logger.info("Cleanup completed.")

    async def _send_to_telegram(self):
        """Send buffered vacancies to Telegram (fire-and-forget)."""
        snapshot = list(self._user_buffers.items())
        for user_id, items in snapshot:
            if not items:
                continue
            user = await self.db.get_user(user_id)
            if not user:
                continue
            if user.telegram_id <= 0:
                logger.info("Skip Telegram send for non-Telegram user_id=%s", user_id)
                continue
            header = f"🔍 <b>Найдено {len(items)} новых вакансий</b>"
            try:
                await self.bot.send_message(
                    chat_id=user.telegram_id,
                    text=header,
                )
            except Exception as e:
                logger.warning("Failed to send header: %s", e)
            for vac_id, source, url, card in items:
                if len(card) > 4000:
                    card = card[:4000].rsplit(" ", 1)[0] + "..."
                await self.db.enqueue_telegram_delivery(
                    user_id=user.id,
                    chat_id=user.telegram_id,
                    vacancy_id=vac_id,
                    source=source,
                    url=url,
                    message=card,
                )
        await self._drain_telegram_delivery_queue()
        stats = await self.db.get_telegram_delivery_stats()
        await self._publish({"type": "telegram_queue", **stats})

    async def _drain_telegram_retry_queue(self):
        if not self._telegram_retry_queue:
            return
        pending = list(self._telegram_retry_queue)
        self._telegram_retry_queue.clear()
        for chat_id, vac_id, source, url, card in pending:
            try:
                await self.bot.send_message(
                    chat_id=chat_id,
                    text=card,
                    reply_markup=build_vacancy_actions_keyboard(int(vac_id), source, url),
                    disable_web_page_preview=True,
                )
                await asyncio.sleep(0.5)
            except Exception as e:
                logger.warning("Retry send failed for vacancy %s: %s", vac_id, e)
                self._telegram_retry_queue.append((chat_id, vac_id, source, url, card))
        # Note: do NOT clear _user_buffers here — run_check/run_check_for_filter
        # clear before populating; clearing here races with concurrent checks.

    async def _drain_telegram_delivery_queue(self, limit: int = 50):
        pending = await self.db.get_pending_telegram_deliveries(limit=limit)
        for item in pending:
            try:
                await self.bot.send_message(
                    chat_id=item.chat_id,
                    text=item.message,
                    reply_markup=build_vacancy_actions_keyboard(item.vacancy_id or 0, item.source, item.url),
                    disable_web_page_preview=True,
                )
                await self.db.mark_telegram_delivery_sent(item.id)
                await asyncio.sleep(0.5)
            except Exception as e:
                logger.warning("Telegram delivery %s failed: %s", item.id, e)
                await self.db.mark_telegram_delivery_failed(item.id, str(e))

    async def retry_telegram_delivery_queue(self) -> dict[str, int]:
        restored = await self.db.retry_failed_telegram_deliveries()
        await self._drain_telegram_delivery_queue(limit=100)
        stats = await self.db.get_telegram_delivery_stats()
        await self._publish({"type": "telegram_retry", "restored": restored, **stats})
        return {"restored": restored, **stats}

    async def _safe_send_to_telegram(self):
        try:
            await self._send_to_telegram()
        except Exception as e:
            logger.error("Telegram send failed: %s", e)

    async def run_check(self):
        if self._lock.locked():
            logger.info("Check already running, skipping.")
            return
        async with self._lock:
            from datetime import datetime, timezone
            self._user_buffers.clear()
            self.last_results.clear()
            self.last_results_time = datetime.now(timezone.utc).isoformat()
            logger.info("Starting vacancy check...")
            await self._publish({"type": "check_started"})
            filters = await self.db.get_all_active_filters()
            if not filters:
                logger.info("No active filters, skipping check.")
                await self._publish({"type": "check_complete", "total_found": 0})
                return

            total_found = 0
            for vf in filters:
                await self._publish({"type": "filter_started", "filter_id": vf.id, "filter_name": vf.name})
                before = sum(len(v) for v in self._user_buffers.values())
                await self._check_filter(vf)
                after = sum(len(v) for v in self._user_buffers.values())
                found = after - before
                total_found += found
                await self._publish({"type": "filter_done", "filter_id": vf.id, "filter_name": vf.name, "found": found})

        # Lock released — results visible on web immediately
        await self._publish({"type": "check_complete", "total_found": total_found})
        logger.info("Search complete, %d found. Sending to Telegram...", total_found)

        # Send to Telegram in background — don't block web
        if total_found > 0:
            asyncio.create_task(self._safe_send_to_telegram())
        logger.info("Vacancy check completed.")

    async def _check_filter(self, vf, user=None, notify: bool = True):
        if user is None:
            user = await self.db.get_user(vf.user_id)
            if not user:
                return

        keywords = vf.get_keywords()
        search_terms = get_synonyms(keywords)
        city = vf.city
        sites = vf.get_sites()
        emp_types = vf.get_employment_types()
        exclude_kw = get_synonyms(vf.get_exclude_keywords())
        experience = vf.experience
        search_queries = self._build_search_queries(keywords, search_terms)

        for site_key in sites:
            scraper = self._get_scraper(site_key)
            if not scraper:
                continue
            seen: set[tuple[str, str]] = set()
            for query in search_queries[:settings.SEARCH_MAX_QUERIES]:
                vacancies = await self._search_with_cache(scraper, site_key, query, city)

                logger.info(
                    "Scraper %s returned %d vacancies for filter %s query %r",
                    site_key, len(vacancies), vf.id, query,
                )
                for idx, vac_data in enumerate(vacancies, start=1):
                    if idx % 20 == 0:
                        await asyncio.sleep(0)
                    dedupe_key = (vac_data.source, vac_data.source_id or vac_data.url)
                    if dedupe_key in seen:
                        continue
                    seen.add(dedupe_key)
                    try:
                        await self._process_vacancy(
                            vac_data, vf, user, search_terms, emp_types, exclude_kw, experience, notify=notify,
                        )
                    except Exception as e:
                        logger.warning("Process vacancy error: %s", e)

    async def preview_filter(self, filter_id: int) -> list[dict]:
        self.last_results.clear()
        vf = await self.db.get_filter(filter_id)
        if not vf:
            return []
        user = await self.db.get_user(vf.user_id)
        if not user:
            return []
        await self._check_filter(vf, user, notify=False)
        return self.get_last_results()

    async def diagnose_filter(self, filter_id: int) -> dict:
        vf = await self.db.get_filter(filter_id)
        if not vf:
            return {"ok": False, "message": "Filter not found"}
        user = await self.db.get_user(vf.user_id)
        if not user:
            return {"ok": False, "message": "User not found"}

        keywords = vf.get_keywords()
        search_terms = get_synonyms(keywords)
        queries = self._build_search_queries(keywords, search_terms)
        emp_types = vf.get_employment_types()
        exclude_kw = get_synonyms(vf.get_exclude_keywords())
        site_stats = []

        for site_key in vf.get_sites():
            scraper = self._get_scraper(site_key)
            if not scraper:
                continue
            stats = {
                "site": site_key,
                "raw": 0,
                "passed": 0,
                "rejected": {
                    "keyword": 0,
                    "noise": 0,
                    "exclude": 0,
                    "employment": 0,
                    "city": 0,
                    "experience": 0,
                    "salary": 0,
                    "blocklist": 0,
                },
                "samples": [],
            }
            seen: set[tuple[str, str]] = set()
            for query in queries[: min(8, settings.SEARCH_MAX_QUERIES)]:
                try:
                    vacancies = await self._search_with_cache(scraper, site_key, query, vf.city, suppress_errors=False)
                except Exception as e:
                    stats["error"] = str(e)
                    continue
                for vac in vacancies:
                    key = (vac.source, vac.source_id or vac.url)
                    if key in seen:
                        continue
                    seen.add(key)
                    stats["raw"] += 1
                    reason = await self._reject_reason(vac, vf, user, search_terms, emp_types, exclude_kw, vf.experience)
                    if reason:
                        stats["rejected"][reason] += 1
                        continue
                    stats["passed"] += 1
                    if len(stats["samples"]) < 5:
                        stats["samples"].append({
                            "title": vac.title,
                            "company": vac.company,
                            "source": vac.source,
                            "city": vac.city,
                            "score": self._score_vacancy(vac, search_terms),
                        })
            site_stats.append(stats)

        return {
            "ok": True,
            "filter_id": vf.id,
            "filter_name": vf.name,
            "queries": queries,
            "sites": site_stats,
        }

    async def _process_vacancy(
        self, vac_data: VacancyData, vf, user,
        keywords: list[str], emp_types: list[str],
        exclude_keywords: list[str] | None = None,
        experience: str | None = None,
        notify: bool = True,
    ):
        if not self._matches_keywords(vac_data, keywords):
            return
        score = self._score_vacancy(vac_data, keywords)
        if self._is_noise_mismatch(vac_data, keywords, score):
            return
        if exclude_keywords and self._has_excluded(vac_data, exclude_keywords):
            return
        if emp_types:
            # Keep vacancies with unknown employment type; reject only explicit mismatches.
            if vac_data.employment_type and vac_data.employment_type not in emp_types:
                return
        if vf.city:
            city_label = CITIES.get(vf.city, vf.city).casefold()
            if not vac_data.city or city_label not in vac_data.city.casefold():
                return
        if experience:
            # Keep vacancies with unknown experience; reject only explicit mismatches.
            if vac_data.experience and vac_data.experience != experience:
                return
        if vf.salary_min is not None or vf.salary_max is not None:
            cand_min = vac_data.salary_min or 0
            cand_max = vac_data.salary_max if vac_data.salary_max is not None else 10**9
            filt_min = vf.salary_min or 0
            filt_max = vf.salary_max if vf.salary_max is not None else 10**9
            if cand_max < filt_min or cand_min > filt_max:
                return

        vac = await self.db.add_vacancy(vac_data)
        setattr(vac_data, "_score", score)

        if await self.db.is_blocked(user.id, vac_data.company, vac_data.title):
            return

        if not notify:
            self.last_results.setdefault(user.id, []).append((vac.id, vf.name, vac_data, vf.id))
            return

        if await self.db.is_sent(user.id, vac.id):
            self.last_results.setdefault(user.id, []).append((vac.id, vf.name, vac_data, vf.id))
            return

        card = format_vacancy_card(vac_data)
        try:
            self._user_buffers.setdefault(user.id, []).append((vac.id, vac_data.source, vac_data.url, card))
            self.last_results.setdefault(user.id, []).append((vac.id, vf.name, vac_data, vf.id))
            await self.db.mark_sent(user.id, vac.id, filter_id=vf.id)
            logger.info("Buffered vacancy %s for user %s", vac_data.title[:50], user.telegram_id)
        except Exception as e:
            logger.warning("Failed to buffer vacancy: %s", e)

    def _build_search_queries(self, keywords: list[str], search_terms: list[str]) -> list[str]:
        """Query external sites with short alternatives instead of one joined synonym string."""
        raw_queries = [*keywords, *search_terms]
        queries = [query.strip() for query in raw_queries if query and query.strip()]
        return list(dict.fromkeys(queries))

    async def _search_with_cache(
        self,
        scraper: BaseScraper,
        site_key: str,
        query: str,
        city: str | None,
        suppress_errors: bool = True,
    ) -> list[VacancyData]:
        cache_key = (site_key, query.casefold(), city)
        now = monotonic()
        cached = self._query_cache.get(cache_key)
        if cached and now - cached[0] <= settings.SEARCH_CACHE_SECONDS:
            return cached[1]
        try:
            vacancies = await scraper.search(keywords=[query], city=city)
        except Exception as e:
            logger.warning("Scraper %s error for query %r: %s", site_key, query, e)
            if not suppress_errors:
                raise
            return []
        self._query_cache[cache_key] = (now, vacancies)
        if len(self._query_cache) > 300:
            oldest = sorted(self._query_cache, key=lambda key: self._query_cache[key][0])[:50]
            for key in oldest:
                self._query_cache.pop(key, None)
        return vacancies

    async def _reject_reason(
        self, vac_data: VacancyData, vf, user,
        keywords: list[str], emp_types: list[str],
        exclude_keywords: list[str] | None,
        experience: str | None,
    ) -> str | None:
        if not self._matches_keywords(vac_data, keywords):
            return "keyword"
        score = self._score_vacancy(vac_data, keywords)
        if self._is_noise_mismatch(vac_data, keywords, score):
            return "noise"
        if exclude_keywords and self._has_excluded(vac_data, exclude_keywords):
            return "exclude"
        if emp_types and vac_data.employment_type and vac_data.employment_type not in emp_types:
            return "employment"
        if vf.city:
            city_label = CITIES.get(vf.city, vf.city).casefold()
            if not vac_data.city or city_label not in vac_data.city.casefold():
                return "city"
        if experience and vac_data.experience and vac_data.experience != experience:
            return "experience"
        if vf.salary_min is not None or vf.salary_max is not None:
            cand_min = vac_data.salary_min or 0
            cand_max = vac_data.salary_max if vac_data.salary_max is not None else 10**9
            filt_min = vf.salary_min or 0
            filt_max = vf.salary_max if vf.salary_max is not None else 10**9
            if cand_max < filt_min or cand_min > filt_max:
                return "salary"
        if await self.db.is_blocked(user.id, vac_data.company, vac_data.title):
            return "blocklist"
        return None

    def _score_vacancy(self, vac: VacancyData, keywords: list[str]) -> int:
        title = self._normalize_search_text(vac.title or "")
        desc = self._normalize_search_text(vac.description or "")
        score = 0
        for kw in keywords:
            query = self._normalize_search_text(kw.strip()) if kw else ""
            if not query:
                continue
            if query in title:
                score += 60
            elif query in desc:
                score += 20
            tokens = [token for token in query.split() if len(token) > 1]
            if tokens and all(token in title for token in tokens):
                score += 30
        if vac.salary_text:
            score += 5
        if vac.published_at:
            score += 5
        if self._title_has_noise(title):
            score -= 45
        return max(0, min(score, 100))

    def _matches_keywords(self, vac: VacancyData, keywords: list[str]) -> bool:
        if not keywords:
            return True
        title_haystack = self._normalize_search_text(vac.title or "")
        full_haystack = self._normalize_search_text(f"{vac.title} {vac.description or ''}")
        for kw in keywords:
            query = self._normalize_search_text(kw.strip()) if kw else ""
            if not query:
                continue
            if query in title_haystack:
                return True
            tokens = [token for token in query.split() if len(token) > 1]
            if len(tokens) > 1:
                if all(token in title_haystack for token in tokens):
                    return True
                if query in full_haystack and self._title_has_role_anchor(title_haystack):
                    return True
                continue
            if query in full_haystack and self._title_has_role_anchor(title_haystack):
                return True
        return False

    def _has_excluded(self, vac: VacancyData, exclude_keywords: list[str]) -> bool:
        haystack = self._normalize_search_text(f"{vac.title} {vac.description or ''}")
        return any(self._normalize_search_text(kw.strip()) in haystack for kw in exclude_keywords if kw and kw.strip())

    def _normalize_search_text(self, text: str) -> str:
        return text.casefold().replace("1\u0441", "1c")

    def _title_has_role_anchor(self, title: str) -> bool:
        anchors = (
            "developer", "engineer", "devops", "sre", "qa", "tester", "testing",
            "support", "analyst", "administrator", "admin", "designer", "manager",
            "разработчик", "инженер", "администратор", "аналитик", "тестировщик",
            "тестирован", "поддержк", "дизайнер", "менеджер", "специалист",
            "программист", "консультант", "архитектор",
        )
        return any(anchor in title for anchor in anchors)

    def _title_has_noise(self, title: str) -> bool:
        return any(word in title for word in self.NOISE_TITLE_WORDS)

    def _is_noise_mismatch(self, vac: VacancyData, keywords: list[str], score: int) -> bool:
        title = self._normalize_search_text(vac.title or "")
        if not self._title_has_noise(title):
            return False
        normalized_keywords = [self._normalize_search_text(kw) for kw in keywords if kw]
        title_matches = any(kw and kw in title for kw in normalized_keywords)
        return not title_matches and score < 30
