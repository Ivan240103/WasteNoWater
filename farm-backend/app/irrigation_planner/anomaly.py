"""Anomalous telemetry detection (FR-8). Returns a human-readable reason or None."""
from __future__ import annotations

from app.config import Settings


def detect_anomaly(value: float, previous: float | None, settings: Settings) -> str | None:
    if value < 0 or value > 100:
        return f"implausible soil moisture value {value:.1f}% (valid range 0-100)"
    if value <= settings.extreme_dry:
        return f"extreme soil dryness: {value:.1f}%"
    if previous is not None and abs(value - previous) > settings.max_jump:
        return f"sudden change from {previous:.1f}% to {value:.1f}%"
    return None
