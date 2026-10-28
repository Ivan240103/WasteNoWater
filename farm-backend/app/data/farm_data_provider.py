"""Farm Data Provider.

Facade used by every other Farm Backend component:
  * persistent data (sensor readings) -> delegated to the repository / Farm Database
  * dashboard feed (recent decisions and warnings) -> small in-memory buffers

In the full system decisions and notifications are also stored in the database
(tables irrigation_decision / farm_device_notification). The prototype keeps them
in memory + logs to honour the "single table" schema; this class is the only
thing that would change.
"""
from __future__ import annotations

from collections import deque

from app.models import Decision, Reading, Warning


class FarmDataProvider:
    def __init__(self, repository, max_events: int = 200):
        self._repo = repository
        self._decisions: deque[Decision] = deque(maxlen=max_events)
        self._warnings: deque[Warning] = deque(maxlen=max_events)

    # ---- persistent data -------------------------------------------------
    async def store_reading(self, reading: Reading) -> None:
        await self._repo.insert(reading)

    async def get_last_readings(self, sensor_id: str, n: int = 1) -> list[Reading]:
        return await self._repo.get_last(sensor_id, n)

    async def get_last_reading(self, sensor_id: str) -> Reading | None:
        rows = await self._repo.get_last(sensor_id, 1)
        return rows[0] if rows else None

    async def get_recent_readings(self, limit: int = 50) -> list[Reading]:
        return await self._repo.get_recent(limit)

    async def known_sensor_ids(self) -> list[str]:
        return await self._repo.list_sensor_ids()

    # ---- dashboard feed (publish / read) ---------------------------------
    def publish_decision(self, decision: Decision) -> None:
        self._decisions.append(decision)

    def publish_warning(self, warning: Warning) -> None:
        self._warnings.append(warning)

    def get_decisions(self, limit: int = 50) -> list[Decision]:
        return list(reversed(self._decisions))[:limit]

    def get_warnings(self, limit: int = 50) -> list[Warning]:
        return list(reversed(self._warnings))[:limit]
