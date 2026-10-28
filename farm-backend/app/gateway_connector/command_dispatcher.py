"""Forwards irrigation decisions to the field gateway.

Prototype: there is no real field gateway, so "dispatching" means logging what
would be sent. In the full system this publishes an MQTT/REST command that the
field gateway relays to the valve.
"""
import logging

from app.models import IRRIGATE, Decision

log = logging.getLogger("dispatch")


class FieldGatewayDispatcher:
    def dispatch(self, decision: Decision) -> None:
        if decision.action == IRRIGATE:
            log.info("-> field gateway: open valve of zone '%s' and deliver %.1f L",
                     decision.sensor_id, decision.water_liters)
        else:
            log.debug("-> field gateway: no command for zone '%s'", decision.sensor_id)
