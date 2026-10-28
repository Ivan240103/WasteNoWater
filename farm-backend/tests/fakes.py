"""In-memory stand-ins so the logic can be tested without PostgreSQL."""
from app.config import Settings


class FakeRepository:
    def __init__(self):
        self.rows = []

    async def insert(self, reading):
        self.rows.append(reading)

    async def get_last(self, sensor_id, limit=1):
        mine = [r for r in self.rows if r.sensor_id == sensor_id]
        return sorted(mine, key=lambda r: r.timestamp, reverse=True)[:limit]

    async def get_recent(self, limit=50):
        return sorted(self.rows, key=lambda r: r.timestamp, reverse=True)[:limit]

    async def list_sensor_ids(self):
        return sorted({r.sensor_id for r in self.rows})


class FakeClock:
    def __init__(self):
        self.t = 1000.0

    def __call__(self):
        return self.t

    def advance(self, seconds):
        self.t += seconds


def make_settings(**overrides) -> Settings:
    base = dict(
        database_url="unused", log_level="INFO",
        expected_sensors=("soil-1",), sensor_timeout_seconds=15, monitor_interval_seconds=1,
        planning_interval_seconds=5, moisture_low=30, moisture_high=60, moisture_target=50,
        liters_per_moisture_point=0.8, extreme_dry=10, max_jump=25,
    )
    base.update(overrides)
    return Settings(**base)
