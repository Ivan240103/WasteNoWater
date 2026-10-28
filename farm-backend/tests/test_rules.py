from datetime import datetime, timezone

from app.irrigation_planner.anomaly import detect_anomaly
from app.irrigation_planner.rules import decide
from app.models import IRRIGATE, SKIP, PlannerInput
from tests.fakes import make_settings

NOW = datetime.now(timezone.utc)
S = make_settings()


def _decide(value, stale=False):
    return decide(PlannerInput("soil-1", value, NOW, stale), NOW, S)


def test_dry_soil_triggers_irrigation():
    d = _decide(20.0)
    assert d.action == IRRIGATE
    assert d.water_liters == 24.0  # (50 - 20) * 0.8


def test_adequate_soil_skips():
    assert _decide(45.0).action == SKIP


def test_wet_soil_skips():
    assert _decide(75.0).action == SKIP


def test_stale_flag_is_carried_into_the_decision():
    d = _decide(20.0, stale=True)
    assert d.based_on_cached_data is True
    assert "cached" in d.reason


def test_anomalies():
    assert detect_anomaly(105, None, S)          # implausible
    assert detect_anomaly(5, 8, S)               # extreme dryness
    assert detect_anomaly(70, 30, S)             # sudden jump
    assert detect_anomaly(45, 44, S) is None     # normal
