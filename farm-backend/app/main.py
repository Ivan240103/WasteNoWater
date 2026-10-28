"""Farm Backend entry point: wires the components together and starts the background loops."""
import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import load_settings
from app.dashboard_api.router import router as dashboard_router
from app.data.database import create_pool
from app.data.farm_data_provider import FarmDataProvider
from app.data.reading_repository import ReadingRepository
from app.gateway_connector.command_dispatcher import FieldGatewayDispatcher
from app.gateway_connector.router import router as gateway_router
from app.gateway_connector.sensor_monitor import SensorMonitor
from app.irrigation_planner.planner import IrrigationPlanner
from app.logging_config import setup_logging

log = logging.getLogger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = load_settings()
    setup_logging(settings.log_level)

    pool = await create_pool(settings.database_url)
    provider = FarmDataProvider(ReadingRepository(pool))
    monitor = SensorMonitor(provider, settings.sensor_timeout_seconds, settings.expected_sensors)
    for sensor_id in await provider.known_sensor_ids():   # sensors seen in earlier runs
        monitor.register(sensor_id)
    planner = IrrigationPlanner(provider, monitor, FieldGatewayDispatcher(), settings)

    app.state.settings = settings
    app.state.provider = provider
    app.state.monitor = monitor
    app.state.planner = planner

    tasks = [
        asyncio.create_task(monitor.run(settings.monitor_interval_seconds)),
        asyncio.create_task(planner.run(settings.planning_interval_seconds)),
    ]
    log.info("Farm Backend ready. Tracking sensors: %s", ", ".join(monitor.known_sensors()))
    try:
        yield
    finally:
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        await pool.close()


app = FastAPI(title="Smart Irrigation - Farm Backend (prototype)", lifespan=lifespan)
app.include_router(gateway_router)
app.include_router(dashboard_router)


@app.get("/health", tags=["ops"])
async def health():
    return {"status": "ok"}
