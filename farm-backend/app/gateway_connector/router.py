"""HTTP endpoint through which readings enter the Farm Backend."""
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request

from app.models import Reading, ReadingIn

log = logging.getLogger("gateway")
router = APIRouter(prefix="/gateway", tags=["gateway connector"])


@router.post("/readings", status_code=201)
async def receive_reading(payload: ReadingIn, request: Request):
    state = request.app.state
    timestamp = payload.timestamp or datetime.now(timezone.utc)
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)
    reading = Reading(payload.sensor_id, timestamp, payload.value)

    # 1) the sensor is alive, no matter what happens next with the database
    state.monitor.record_heartbeat(reading.sensor_id)

    # 2) persist through the Farm Data Provider
    try:
        await state.provider.store_reading(reading)
    except Exception:
        log.exception("could not persist reading of %s", reading.sensor_id)
        raise HTTPException(status_code=503, detail="farm database unavailable")

    log.debug("reading sensor=%s value=%.2f", reading.sensor_id, reading.value)
    return {"status": "stored"}
