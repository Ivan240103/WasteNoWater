"""Shared data types (the DTOs of the Farm Backend)."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from pydantic import BaseModel, Field

# ---- warning kinds
SENSOR_DOWN = "SENSOR_DOWN"
SENSOR_RECOVERED = "SENSOR_RECOVERED"
ANOMALY = "ANOMALY"

# ---- decision actions
IRRIGATE = "IRRIGATE"
SKIP = "SKIP"


class ReadingIn(BaseModel):
    """Payload accepted by POST /gateway/readings (what the field gateway forwards)."""
    sensor_id: str = Field(min_length=1, max_length=64)
    value: float = Field(allow_inf_nan=False)
    timestamp: datetime | None = None  # if omitted, the backend uses "now"


@dataclass(frozen=True)
class Reading:
    sensor_id: str
    timestamp: datetime
    value: float


@dataclass(frozen=True)
class PlannerInput:
    sensor_id: str
    value: float
    measured_at: datetime
    is_stale: bool  # True -> sensor is DOWN, value is its last valid measurement


@dataclass(frozen=True)
class Decision:
    sensor_id: str
    action: str                 # IRRIGATE | SKIP
    water_liters: float
    reason: str
    based_on_cached_data: bool
    data_age_seconds: float
    created_at: datetime


@dataclass(frozen=True)
class Warning:
    kind: str                   # SENSOR_DOWN | SENSOR_RECOVERED | ANOMALY
    sensor_id: str
    message: str
    created_at: datetime
