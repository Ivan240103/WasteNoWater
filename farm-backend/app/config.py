"""Runtime configuration, read from environment variables (see docker-compose.yml)."""
import os
from dataclasses import dataclass


def _csv(name: str, default: str) -> tuple[str, ...]:
    return tuple(s.strip() for s in os.getenv(name, default).split(",") if s.strip())


@dataclass(frozen=True)
class Settings:
    # --- infrastructure
    database_url: str
    log_level: str

    # --- sensor liveness (FR-6, TNF-1.3, TNF-1.4)
    # The architecture document says 5 minutes; the prototype uses seconds so a
    # demo does not take forever. Override with SENSOR_TIMEOUT_SECONDS=300 to
    # reproduce the document value.
    expected_sensors: tuple[str, ...]
    sensor_timeout_seconds: float
    monitor_interval_seconds: float

    # --- irrigation planner (FR-4, simplified to if/else rules)
    planning_interval_seconds: float
    moisture_low: float          # below this -> irrigate
    moisture_high: float         # above this -> soil already wet
    moisture_target: float       # irrigate until (theoretically) reaching this
    liters_per_moisture_point: float

    # --- anomaly detection (FR-8)
    extreme_dry: float           # at/below this value -> alert
    max_jump: float              # abs difference between consecutive readings


def load_settings() -> Settings:
    return Settings(
        database_url=os.getenv("DATABASE_URL", "postgresql://farm:farm@localhost:5432/farm"),
        log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
        expected_sensors=_csv("EXPECTED_SENSORS", "soil-1,soil-2,soil-3,soil-4"),
        sensor_timeout_seconds=float(os.getenv("SENSOR_TIMEOUT_SECONDS", "15")),
        monitor_interval_seconds=float(os.getenv("MONITOR_INTERVAL_SECONDS", "1")),
        planning_interval_seconds=float(os.getenv("PLANNING_INTERVAL_SECONDS", "5")),
        moisture_low=float(os.getenv("MOISTURE_LOW", "30")),
        moisture_high=float(os.getenv("MOISTURE_HIGH", "60")),
        moisture_target=float(os.getenv("MOISTURE_TARGET", "50")),
        liters_per_moisture_point=float(os.getenv("LITERS_PER_MOISTURE_POINT", "0.8")),
        extreme_dry=float(os.getenv("EXTREME_DRY", "10")),
        max_jump=float(os.getenv("MAX_JUMP", "25")),
    )
