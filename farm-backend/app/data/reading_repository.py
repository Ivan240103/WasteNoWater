"""Repository pattern: all SQL for the sensor_readings table lives here."""
from __future__ import annotations

import asyncpg

from app.models import Reading


class ReadingRepository:
    def __init__(self, pool: asyncpg.Pool):
        self._pool = pool

    async def insert(self, reading: Reading) -> None:
        await self._pool.execute(
            'INSERT INTO sensor_readings (sensor_id, "timestamp", value) '
            "VALUES ($1, $2, $3) ON CONFLICT DO NOTHING",
            reading.sensor_id, reading.timestamp, reading.value,
        )

    async def get_last(self, sensor_id: str, limit: int = 1) -> list[Reading]:
        """Most recent readings of one sensor, newest first."""
        rows = await self._pool.fetch(
            'SELECT sensor_id, "timestamp", value FROM sensor_readings '
            'WHERE sensor_id = $1 ORDER BY "timestamp" DESC LIMIT $2',
            sensor_id, limit,
        )
        return [Reading(r["sensor_id"], r["timestamp"], r["value"]) for r in rows]

    async def get_recent(self, limit: int = 50) -> list[Reading]:
        """Most recent readings of all sensors, newest first."""
        rows = await self._pool.fetch(
            'SELECT sensor_id, "timestamp", value FROM sensor_readings '
            'ORDER BY "timestamp" DESC LIMIT $1',
            limit,
        )
        return [Reading(r["sensor_id"], r["timestamp"], r["value"]) for r in rows]

    async def list_sensor_ids(self) -> list[str]:
        rows = await self._pool.fetch("SELECT DISTINCT sensor_id FROM sensor_readings ORDER BY 1")
        return [r["sensor_id"] for r in rows]
