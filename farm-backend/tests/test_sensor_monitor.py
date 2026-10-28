from app.data.farm_data_provider import FarmDataProvider
from app.gateway_connector.sensor_monitor import SensorMonitor
from app.models import SENSOR_DOWN, SENSOR_RECOVERED
from tests.fakes import FakeClock, FakeRepository


def make():
    clock = FakeClock()
    provider = FarmDataProvider(FakeRepository())
    monitor = SensorMonitor(provider, timeout_seconds=15, expected_sensors=["soil-1", "soil-2"], clock=clock)
    return clock, provider, monitor


def test_silent_sensor_is_flagged_down_once():
    clock, provider, monitor = make()
    clock.advance(10)
    monitor.record_heartbeat("soil-1")      # soil-1 alive, soil-2 silent
    clock.advance(10)                       # soil-2 silent for 20s > 15s
    assert monitor.check() == ["soil-2"]
    assert monitor.is_down("soil-2") and not monitor.is_down("soil-1")
    assert monitor.check() == []            # no duplicate warning
    warnings = provider.get_warnings()
    assert len(warnings) == 1 and warnings[0].kind == SENSOR_DOWN


def test_sensor_recovers_when_data_returns():
    clock, provider, monitor = make()
    clock.advance(20)
    monitor.check()
    assert monitor.is_down("soil-1")
    monitor.record_heartbeat("soil-1")
    assert not monitor.is_down("soil-1")
    assert provider.get_warnings()[0].kind == SENSOR_RECOVERED


def test_unknown_sensor_gets_registered_on_first_reading():
    _, _, monitor = make()
    monitor.record_heartbeat("soil-99")
    assert "soil-99" in monitor.known_sensors()
