import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from app.config import settings
from app.api.routes import router as api_router
from app.bot.handlers import user as user_handler
from app.bot.handlers import messaging as msg_handler
from app.bot.handlers import admin as admin_handler
from app.bot.middlewares import DBSessionMiddleware, UserContextMiddleware, RateLimitMiddleware
from app.scheduler.main import setup_scheduler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=settings.bot_token)
dp = Dispatcher(storage=MemoryStorage())

# Setup middlewares
dp.update.middleware(DBSessionMiddleware())
dp.update.middleware(UserContextMiddleware())
dp.message.middleware(RateLimitMiddleware())
dp.callback_query.middleware(RateLimitMiddleware())

# Include routers
dp.include_router(user_handler.router)
dp.include_router(msg_handler.router)
dp.include_router(admin_handler.router)

scheduler = setup_scheduler()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting up...")
    scheduler.start()

    # Run polling in background
    bot_task = asyncio.create_task(dp.start_polling(bot))

    yield

    # Shutdown
    logger.info("Shutting down...")
    scheduler.shutdown()
    bot_task.cancel()
    await bot.session.close()

app = FastAPI(
    title="Hushly",
    docs_url=None, # Disable Swagger
    redoc_url=None, # Disable ReDoc
    lifespan=lifespan
)

app.include_router(api_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
