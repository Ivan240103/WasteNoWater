"""Irrigation Planner.

Follows the sequence in architecture document section 7.4.2:
  Farm Data Provider fetches the data -> Planner computes the decision ->
  Farm Data Provider publishes it -> Gateway Connector forwards it to the field gateway.

Key behaviour for the prototype (TNF-1.3): if a sensor is DOWN the cycle does NOT stop;
the last valid measurement stored in the database is used instead.
"""
from __future__ import annotations

import asyncio
import logging
import time
from datetime import datetime, timezone

from app.config import Settings
from app.irrigation_planner.anomaly import detect_anomaly
from app.irrigation_planner.rules import decide
from app.models import ANOMALY, Decision, PlannerInput, Reading, Warning

log = logging.getLogger("planner")

TNF_2_2_LIMIT_SECONDS = 180  # predictions within 3 minutes


class IrrigationPlanner:
    def __init__(self, provider, monitor, dispatcher, settings: Settings):
        self._provider = provider
        self._monitor = monitor
        self._dispatcher = dispatcher
        self._settings = settings
        self._last_flagged: dict[str, datetime] = {}  # avoid repeating the same anomaly alert

    async def run_cycle(self) -> list[Decision]:
        started = time.perf_counter()
        decisions: list[Decision] = []
        for sensor_id in self._monitor.known_sensors():
            decision = await self._plan_for(sensor_id)
            if decision:
                decisions.append(decision)
        elapsed = time.perf_counter() - started
        level = logging.INFO if elapsed < TNF_2_2_LIMIT_SECONDS else logging.ERROR
        log.log(level, "planning cycle finished: %d decisions in %.3fs (TNF-2.2 limit %ds)",
                len(decisions), elapsed, TNF_2_2_LIMIT_SECONDS)
        return decisions

    async def _plan_for(self, sensor_id: str) -> Decision | None:
        readings = await self._provider.get_last_readings(sensor_id, 2)
        if not readings:
            log.debug("sensor=%s has no stored reading yet, skipping", sensor_id)
            return None

        latest = readings[0]
        previous = readings[1].value if len(readings) > 1 else None
        stale = self._monitor.is_down(sensor_id)

        if not stale:
            self._check_anomaly(latest, previous)

        now = datetime.now(timezone.utc)
        decision = decide(
            PlannerInput(sensor_id, latest.value, latest.timestamp, is_stale=stale),
            now, self._settings)

        self._provider.publish_decision(decision)
        self._dispatcher.dispatch(decision)

        tag = "CACHED" if stale else "fresh "
        log.info("sensor=%-8s [%s] value=%5.1f age=%5.1fs -> %-8s %5.1f L | %s",
                 sensor_id, tag, latest.value, decision.data_age_seconds,
                 decision.action, decision.water_liters, decision.reason)
        return decision

    def _check_anomaly(self, latest: Reading, previous: float | None) -> None:
        if self._last_flagged.get(latest.sensor_id) == latest.timestamp:
            return
        reason = detect_anomaly(latest.value, previous, self._settings)
        if reason:
            self._last_flagged[latest.sensor_id] = latest.timestamp
            log.warning("sensor=%s ANOMALY -> %s (operator alerted before irrigation)",
                        latest.sensor_id, reason)
            self._provider.publish_warning(
                Warning(ANOMALY, latest.sensor_id, reason, datetime.now(timezone.utc)))

    async def run(self, interval_seconds: float) -> None:
        log.info("irrigation planner started (cycle every %ss)", interval_seconds)
        while True:
            try:
                await self.run_cycle()
            except Exception:
                log.exception("planning cycle failed")
            await asyncio.sleep(interval_seconds)
