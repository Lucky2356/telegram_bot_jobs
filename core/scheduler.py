import logging
import asyncio
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

logger = logging.getLogger(__name__)


class Scheduler:
    def __init__(self, db: Database, bot: Bot):
        self.db = db
        self.bot = bot
        self._scrapers: dict[str, BaseScraper] = {}
        self._user_buffers: dict[int, list[tuple[int, str, str, str]]] = {}
        self._lock = asyncio.Lock()
        self.last_results: dict[int, list[tuple[int, str | None, VacancyData]]] = {}
        self.last_results_time: str | None = None
        self.event_queue: asyncio.Queue[dict] = asyncio.Queue(maxsize=100)

    @property
    def is_checking(self) -> bool:
        return self._lock.locked()

    async def _publish(self, event: dict):
        try:
            await self.event_queue.put(event)
        except asyncio.QueueFull:
            pass

    def get_last_results(self) -> list[dict]:
        """Return cached results from the last check as serializable dicts."""
        combined: list[tuple[int, str | None, VacancyData]] = []
        for items in self.last_results.values():
            combined.extend(items)
        from datetime import datetime, timezone
        return [
            {
                "id": vac_id,
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
                "published_at": v.published_at.isoformat() if v.published_at else None,
            }
            for vac_id, filter_name, v in combined
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
        for s in self._scrapers.values():
            try:
                await s.close()
            except Exception:
                pass
        self._scrapers.clear()

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
            await self._check_filter(vf, user)
            found = sum(len(v) for v in self._user_buffers.values())
            await self._publish({"type": "filter_done", "filter_id": vf.id, "filter_name": vf.name, "found": found})
            self._user_buffers.clear()
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
            header = f"🔍 <b>Найдено {len(items)} новых вакансий</b>"
            try:
                await self.bot.send_message(
                    chat_id=user.telegram_id,
                    text=header,
                )
            except Exception as e:
                logger.warning("Failed to send header: %s", e)
            for vac_id, source, url, card in items:
                try:
                    if len(card) > 4000:
                        card = card[:4000].rsplit(" ", 1)[0] + "..."
                    await self.bot.send_message(
                        chat_id=user.telegram_id,
                        text=card,
                        reply_markup=build_vacancy_actions_keyboard(vac_id, source, url),
                        disable_web_page_preview=True,
                    )
                    await asyncio.sleep(0.5)
                except Exception as e:
                    logger.warning("Failed to send vacancy %s: %s", vac_id, e)
        # Note: do NOT clear _user_buffers here — run_check/run_check_for_filter
        # clear before populating; clearing here races with concurrent checks.

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

    async def _check_filter(self, vf, user=None):
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

        for site_key in sites:
            scraper = self._get_scraper(site_key)
            if not scraper:
                continue
            try:
                vacancies = await scraper.search(keywords=keywords, city=city)
            except Exception as e:
                logger.warning("Scraper %s error: %s", site_key, e)
                continue

            for vac_data in vacancies:
                try:
                    await self._process_vacancy(
                        vac_data, vf, user, search_terms, emp_types, exclude_kw, experience,
                    )
                except Exception as e:
                    logger.warning("Process vacancy error: %s", e)

    async def _process_vacancy(
        self, vac_data: VacancyData, vf, user,
        keywords: list[str], emp_types: list[str],
        exclude_keywords: list[str] | None = None,
        experience: str | None = None,
    ):
        if not self._matches_keywords(vac_data, keywords):
            return
        if exclude_keywords and self._has_excluded(vac_data, exclude_keywords):
            return
        if emp_types and vac_data.employment_type and vac_data.employment_type not in emp_types:
            return
        if vf.city:
            city_label = CITIES.get(vf.city, vf.city).lower()
            if vac_data.city and city_label not in vac_data.city.lower():
                return
        if experience and vac_data.experience and vac_data.experience != experience:
            return
        if vf.salary_min is not None or vf.salary_max is not None:
            if vf.salary_min is not None and vac_data.salary_max is not None and vac_data.salary_max < vf.salary_min:
                return
            if vf.salary_max is not None and vac_data.salary_min is not None and vac_data.salary_min > vf.salary_max:
                return

        vac = await self.db.add_vacancy(vac_data)
        if vac is None:
            return

        if await self.db.is_sent(user.id, vac.id):
            return

        if await self.db.is_blocked(user.id, vac_data.company, vac_data.title):
            return

        card = format_vacancy_card(vac_data)
        try:
            self._user_buffers.setdefault(user.id, []).append((vac.id, vac_data.source, vac_data.url, card))
            self.last_results.setdefault(user.id, []).append((vac.id, vf.name, vac_data))
            await self.db.mark_sent(user.id, vac.id, filter_id=vf.id)
            logger.info("Buffered vacancy %s for user %s", vac_data.title[:50], user.telegram_id)
        except Exception as e:
            logger.warning("Failed to buffer vacancy: %s", e)

    def _matches_keywords(self, vac: VacancyData, keywords: list[str]) -> bool:
        title_lower = vac.title.lower()
        for kw in keywords:
            if kw.lower() in title_lower:
                return True
        if vac.description:
            desc_lower = vac.description.lower()
            for kw in keywords:
                if kw.lower() in desc_lower:
                    return True
        return False

    def _has_excluded(self, vac: VacancyData, exclude_keywords: list[str]) -> bool:
        text_lower = f"{vac.title} {vac.description or ''}".lower()
        for kw in exclude_keywords:
            if kw.lower() in text_lower:
                return True
        return False
