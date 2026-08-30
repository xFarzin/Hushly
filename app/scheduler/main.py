from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.scheduler.jobs import cleanup_expired_links, cleanup_expired_tokens

def setup_scheduler() -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler()

    # Run every hour
    scheduler.add_job(cleanup_expired_links, 'interval', hours=1)
    # Run every day
    scheduler.add_job(cleanup_expired_tokens, 'interval', days=1)

    return scheduler
