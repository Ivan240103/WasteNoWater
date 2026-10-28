"""Sensor liveness watchdog.

Architecture document, section 7.4: "the Gateway Connector notices the data absence
for five consecutive minutes, emits a warning to the Farm Data Provider ..."

Every incoming reading is a heartbeat. A sensor silent for longer than the timeout
is marked DOWN and a warning is published. When data arrives again the sensor is
marked UP and a recovery notice is published.
"""
from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable

from app.models import SENSOR_DOWN, SENSOR_RECOVERED, Warning

log = logging.getLogger("monitor")


@dataclass
class _SensorState:
    last_seen: float
    down: bool = False


class SensorMonitor:
    def __init__(self, provider, timeout_seconds: float,
                 expected_sensors=(), clock: Callable[[], float] = time.monotonic):
        self._provider = provider
        self._timeout = timeout_seconds
        self._clock = clock
        self._sensors: dict[str, _SensorState] = {}
        for sensor_id in expected_sensors:
            self.register(sensor_id)

    # ---- registry --------------------------------------------------------
    def register(self, sensor_id: str) -> None:
        """Start tracking a sensor. Gets a full timeout of grace before being flagged."""
        if sensor_id not in self._sensors:
            self._sensors[sensor_id] = _SensorState(last_seen=self._clock())

    def known_sensors(self) -> list[str]:
        return sorted(self._sensors)

    def is_down(self, sensor_id: str) -> bool:
        state = self._sensors.get(sensor_id)
        return bool(state and state.down)

    # ---- events ----------------------------------------------------------
    def record_heartbeat(self, sensor_id: str) -> None:
        """Called for every reading received from the field."""
        self.register(sensor_id)
        state = self._sensors[sensor_id]
        state.last_seen = self._clock()
        if state.down:
            state.down = False
            message = f"Sensor {sensor_id} is sending data again."
            log.warning("sensor=%s RECOVERED -> back to normal operation", sensor_id)
            self._provider.publish_warning(
                Warning(SENSOR_RECOVERED, sensor_id, message, datetime.now(timezone.utc)))

    def check(self) -> list[str]:
        """Flag every sensor that has been silent for too long. Returns the newly DOWN ones."""
        now = self._clock()
        newly_down = []
        for sensor_id, state in self._sensors.items():
            silent_for = now - state.last_seen
            if silent_for > self._timeout and not state.down:
                state.down = True
                newly_down.append(sensor_id)
                message = (f"No data from {sensor_id} for {silent_for:.0f}s "
                           f"(timeout {self._timeout:.0f}s). Irrigation continues using "
                           f"its last valid measurement.")
                log.warning("sensor=%s DOWN -> %s", sensor_id, message)
                self._provider.publish_warning(
                    Warning(SENSOR_DOWN, sensor_id, message, datetime.now(timezone.utc)))
        return newly_down

    def snapshot(self) -> list[dict]:
        now = self._clock()
        return [
            {"sensor_id": sid,
             "status": "DOWN" if st.down else "UP",
             "seconds_since_last_data": round(now - st.last_seen, 1)}
            for sid, st in sorted(self._sensors.items())
        ]

    # ---- background loop -------------------------------------------------
    async def run(self, interval_seconds: float) -> None:
        log.info("sensor monitor started (timeout=%ss, check every %ss)",
                 self._timeout, interval_seconds)
        while True:
            try:
                self.check()
            except Exception:  # never let the watchdog die
                log.exception("monitor check failed")
            await asyncio.sleep(interval_seconds)
