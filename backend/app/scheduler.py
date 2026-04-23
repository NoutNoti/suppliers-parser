import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.db.session import async_session
from app.services.product import ProductService

logger = logging.getLogger(__name__)

PARSE_INTERVAL_HOURS = 2

_scheduler: AsyncIOScheduler | None = None


async def run_parse_job() -> None:
    logger.info("Scheduled parse job started")
    async with async_session() as session:
        service = ProductService(session=session)
        try:
            await service.parse_all_and_store()
            await service.categorize_uncategorized()
        except Exception:
            logger.exception("Parse job failed")


def start_scheduler() -> AsyncIOScheduler:
    global _scheduler
    if _scheduler is not None:
        return _scheduler

    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        run_parse_job,
        trigger=IntervalTrigger(hours=PARSE_INTERVAL_HOURS),
        id="parse_all_suppliers",
        max_instances=1,
        coalesce=True,
        replace_existing=True,
    )
    scheduler.start()
    _scheduler = scheduler
    logger.info("Scheduler started, parsing every %d hours", PARSE_INTERVAL_HOURS)
    return scheduler


def stop_scheduler() -> None:
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
