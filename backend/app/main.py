"""
LogWatch — FastAPI entry point.

Mounts all routers, configures CORS, initialises the database on startup,
and starts Telegram integration in either polling or webhook mode.
"""
import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import init_db
from .config import settings
from .routers import machines, logs, issues, commands, agent, telegram
from .services.telegram_poller import start_polling, stop_polling
from .services.telegram_bot import register_webhook

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle."""
    await init_db()
    logging.info("Database initialised")

    poll_task = None
    if settings.TELEGRAM_BOT_TOKEN:
        if settings.TELEGRAM_MODE == "webhook" and settings.TELEGRAM_WEBHOOK_URL:
            # Webhook mode — register the URL with Telegram
            ok = await register_webhook(settings.TELEGRAM_WEBHOOK_URL)
            if ok:
                logging.info("Telegram webhook registered: %s", settings.TELEGRAM_WEBHOOK_URL)
            else:
                logging.error("Failed to register Telegram webhook — falling back to polling")
                poll_task = asyncio.create_task(start_polling())
        else:
            # Polling mode (default)
            poll_task = asyncio.create_task(start_polling())
            logging.info("Telegram polling started")
    else:
        logging.info("Telegram not configured — disabled")

    yield

    if poll_task:
        stop_polling()
        poll_task.cancel()
        try:
            await poll_task
        except asyncio.CancelledError:
            pass
    logging.info("Shutting down")


app = FastAPI(
    title="LogWatch",
    description="Distributed Log Monitoring & AI Remediation System",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow dashboard frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routers
app.include_router(machines.router)
app.include_router(logs.router)
app.include_router(issues.router)
app.include_router(commands.router)
app.include_router(agent.router)
app.include_router(telegram.router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "logwatch-server"}
