import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI
from src.utils.logger import logger

scheduler = AsyncIOScheduler()

async def on_day_change():
    try:
        pass

    except Exception as e:
        await logger.aerror(f"Error in on_day_change: {e}")

async def on_loop_10m():
    try:
        ...

    except Exception as e:
        await logger.aerror(f"Error in on_loop_10m: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler.start()
    try:
        scheduler.add_job(on_day_change, "cron", hour=0, minute=0)
        scheduler.add_job(on_loop_10m, "interval", minutes=10, next_run_time=datetime.now())

        yield

    finally:    
        scheduler.shutdown(wait=True)
