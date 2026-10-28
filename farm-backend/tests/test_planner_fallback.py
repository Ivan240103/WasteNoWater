"""The core behaviour the prototype must demonstrate (TNF-1.3):
a sensor goes down -> the system keeps operating with its last valid measurement."""
import asyncio
from datetime import datetime, timedelta, timezone

from app.data.farm_data_provider import FarmDataProvider
from app.gateway_connector.command_dispatcher import FieldGatewayDispatcher
from app.gateway_connector.sensor_monitor import SensorMonitor
from app.irrigation_planner.planner import IrrigationPlanner
from app.models import IRRIGATE, Reading
from tests.fakes import FakeClock, FakeRepository, make_settings


def build():
    clock = FakeClock()
    provider = FarmDataProvider(FakeRepository())
    monitor = SensorMonitor(provider, 15, ["soil-1", "soil-2"], clock=clock)
    planner = IrrigationPlanner(provider, monitor, FieldGatewayDispatcher(), make_settings())
    return clock, provider, monitor, planner


def test_planner_keeps_working_with_last_valid_value_when_sensor_is_down():
    async def scenario():
        clock, provider, monitor, planner = build()
        t0 = datetime.now(timezone.utc) - timedelta(minutes=1)

        # both sensors report; soil-2 is dry
        for sid, val in (("soil-1", 45.0), ("soil-2", 20.0)):
            monitor.record_heartbeat(sid)
            await provider.store_reading(Reading(sid, t0, val))

        decisions = {d.sensor_id: d for d in await planner.run_cycle()}
        assert not decisions["soil-2"].based_on_cached_data       # fresh at this point

        # soil-2 stops sending; soil-1 keeps going
        clock.advance(20)
        monitor.record_heartbeat("soil-1")
        await provider.store_reading(Reading("soil-1", datetime.now(timezone.utc), 46.0))
        monitor.check()
        assert monitor.is_down("soil-2")

        decisions = {d.sensor_id: d for d in await planner.run_cycle()}
        assert set(decisions) == {"soil-1", "soil-2"}              # nobody was dropped
        d2 = decisions["soil-2"]
        assert d2.based_on_cached_data is True                     # TNF-1.3
        assert d2.action == IRRIGATE and d2.water_liters == 24.0   # used the last valid 20.0
        assert not decisions["soil-1"].based_on_cached_data

    asyncio.run(scenario())


def test_sensor_without_any_reading_is_skipped_not_fatal():
    async def scenario():
        _, provider, monitor, planner = build()
        await provider.store_reading(Reading("soil-1", datetime.now(timezone.utc), 40.0))
        decisions = await planner.run_cycle()
        assert [d.sensor_id for d in decisions] == ["soil-1"]      # soil-2 never reported

    asyncio.run(scenario())
