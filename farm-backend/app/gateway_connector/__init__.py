"""Gateway Connector: entry point of field data and exit point of irrigation commands.

  router.py              receives sensor readings (HTTP, as forwarded by the field gateway)
  sensor_monitor.py      detects sensors that stopped sending data (FR-6, TNF-1.4)
  command_dispatcher.py  forwards irrigation decisions towards the field gateway
"""
