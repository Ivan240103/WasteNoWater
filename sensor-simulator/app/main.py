"""Sensor emulator: stands in for the field hardware + field gateway.

  * every SEND_INTERVAL_SECONDS each sensor that is UP posts a random reading to the Farm Backend
  * a tiny control API flips the sensor's `is_up` bool, so you can kill / revive sensors on demand
"""
import asyncio
import logging
import os
import random
from contextlib import asynccontextmanager
from datetime import datetime, timezone

import httpx
from fastapi import FastAPI, HTTPException

from app.sensors import SimulatedSensor

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)-7s simulator | %(message)s",
                    datefmt="%H:%M:%S")
log = logging.getLogger("simulator")

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
SEND_INTERVAL = float(os.getenv("SEND_INTERVAL_SECONDS", "2"))
SENSOR_IDS = [s.strip() for s in os.getenv("SENSOR_IDS", "soil-1,soil-2,soil-3,soil-4").split(",") if s.strip()]
ANOMALY_PROBABILITY = float(os.getenv("ANOMALY_PROBABILITY", "0.01"))

rng = random.Random()
sensors = {sid: SimulatedSensor(sid, rng, ANOMALY_PROBABILITY) for sid in SENSOR_IDS}


async def publish_loop():
    async with httpx.AsyncClient(base_url=BACKEND_URL, timeout=5.0) as client:
        while True:
            for sensor in sensors.values():
                if not sensor.is_up:
                    continue                      # a dead sensor sends nothing
                payload = {
                    "sensor_id": sensor.sensor_id,
                    "value": sensor.next_value(),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
                try:
                    r = await client.post("/gateway/readings", json=payload)
                    r.raise_for_status()
                except httpx.HTTPError as exc:
                    log.warning("could not deliver reading of %s: %s", sensor.sensor_id, exc)
            await asyncio.sleep(SEND_INTERVAL)


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("emulating sensors %s -> %s every %ss", SENSOR_IDS, BACKEND_URL, SEND_INTERVAL)
    task = asyncio.create_task(publish_loop())
    yield
    task.cancel()
    await asyncio.gather(task, return_exceptions=True)


app = FastAPI(title="Sensor emulator (prototype)", lifespan=lifespan)


def _get(sensor_id: str) -> SimulatedSensor:
    if sensor_id not in sensors:
        raise HTTPException(404, f"unknown sensor {sensor_id}")
    return sensors[sensor_id]


@app.get("/sensors")
async def list_sensors():
    return [{"sensor_id": s.sensor_id, "is_up": s.is_up, "value": round(s.value, 2)}
            for s in sensors.values()]


@app.post("/sensors/{sensor_id}/down")
async def sensor_down(sensor_id: str):
    sensor = _get(sensor_id)
    sensor.is_up = False                         # true -> false
    log.warning("sensor %s is now DOWN (no more readings will be sent)", sensor_id)
    return {"sensor_id": sensor_id, "is_up": False}


@app.post("/sensors/{sensor_id}/up")
async def sensor_up(sensor_id: str):
    sensor = _get(sensor_id)
    sensor.is_up = True                          # false -> true
    log.info("sensor %s is back UP", sensor_id)
    return {"sensor_id": sensor_id, "is_up": True}


@app.get("/health")
async def health():
    return {"status": "ok"}
