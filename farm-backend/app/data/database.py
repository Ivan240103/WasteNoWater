"""Connection pool creation, with retries so the backend survives a slow DB start-up."""
import asyncio
import logging

import asyncpg

log = logging.getLogger("data")


async def create_pool(dsn: str, attempts: int = 15, delay_seconds: float = 2.0) -> asyncpg.Pool:
    for attempt in range(1, attempts + 1):
        try:
            pool = await asyncpg.create_pool(dsn, min_size=1, max_size=10)
            log.info("connected to the Farm Database")
            return pool
        except (OSError, asyncpg.PostgresError) as exc:
            log.warning("database not ready (%d/%d): %s", attempt, attempts, exc)
            await asyncio.sleep(delay_seconds)
    raise RuntimeError("could not connect to the Farm Database")
