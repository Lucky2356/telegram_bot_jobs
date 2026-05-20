import logging
import re
from aiogram import Bot
from core.database.repository import Database
from scrapers.hh_ru import HHScraper
from scrapers.superjob_ru import SuperJobScraper
from scrapers.trudvsem_ru import TrudvsemScraper
from scrapers.rabota_ru import RabotaRuScraper
from scrapers.habr_career import HabrCareerScraper
from scrapers.base import VacancyData, BaseScraper
from bot.messages import format_vacancy_card
from bot.keyboards import build_vacancy_actions_keyboard, CITIES

logger = logging.getLogger(__name__)


class Scheduler:
    def __init__(self, db: Database, bot: Bot):
        self.db = db
        self.bot = bot
        self._scrapers: dict[str, BaseScraper] = {}
        self._user_buffers: dict[int, list[str]] = {}

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

    async def run_check(self):
        logger.info("Starting vacancy check...")
        self._user_buffers.clear()
        filters = await self.db.get_all_active_filters()
        if not filters:
            logger.info("No active filters, skipping check.")
            return

        for vf in filters:
            await self._check_filter(vf)

        for user_id, vacancies in self._user_buffers.items():
            if not vacancies:
                continue
            header = f"🔍 <b>Найдено {len(vacancies)} новых вакансий</b>\n\n"
            body = "\n\n".join(vacancies)
            try:
                user = await self.db.get_user(user_id)
                if user:
                    await self.bot.send_message(
                        chat_id=user.telegram_id,
                        text=header + body,
                        disable_web_page_preview=True,
                    )
            except Exception as e:
                logger.warning("Failed to send digest: %s", e)

        self._user_buffers.clear()
        logger.info("Vacancy check completed.")

    async def _check_filter(self, vf):
        user = await self.db.get_user(vf.user_id)
        if not user:
            return

        keywords = vf.get_keywords()
        city = vf.city
        sites = vf.get_sites()
        emp_types = vf.get_employment_types()
        exclude_kw = vf.get_exclude_keywords()
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
                        vac_data, vf, user, keywords, emp_types, exclude_kw, experience,
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

        card = format_vacancy_card(vac_data) + "\n\n⚡"
        try:
            if user.telegram_id not in self._user_buffers:
                self._user_buffers[user.telegram_id] = []
            self._user_buffers[user.telegram_id].append(card)
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
