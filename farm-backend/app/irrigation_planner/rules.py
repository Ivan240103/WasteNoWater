"""Irrigation decision: deliberately just if/else (the real system uses PID control)."""
from __future__ import annotations

from datetime import datetime

from app.config import Settings
from app.models import IRRIGATE, SKIP, Decision, PlannerInput


def decide(inp: PlannerInput, now: datetime, settings: Settings) -> Decision:
    age = max((now - inp.measured_at).total_seconds(), 0.0)
    source = "last valid (cached) value" if inp.is_stale else "fresh value"

    if inp.value < settings.moisture_low:
        liters = round((settings.moisture_target - inp.value) * settings.liters_per_moisture_point, 1)
        action = IRRIGATE
        reason = (f"soil moisture {inp.value:.1f}% < {settings.moisture_low:.0f}% "
                  f"-> irrigate towards {settings.moisture_target:.0f}% [{source}]")
    elif inp.value > settings.moisture_high:
        liters, action = 0.0, SKIP
        reason = f"soil moisture {inp.value:.1f}% > {settings.moisture_high:.0f}% -> soil already wet [{source}]"
    else:
        liters, action = 0.0, SKIP
        reason = f"soil moisture {inp.value:.1f}% is adequate -> no irrigation [{source}]"

    return Decision(
        sensor_id=inp.sensor_id,
        action=action,
        water_liters=liters,
        reason=reason,
        based_on_cached_data=inp.is_stale,
        data_age_seconds=round(age, 1),
        created_at=now,
    )
