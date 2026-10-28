# WasteNoWater

Prototype that demonstrates the **Farm Backend** of the Smart Irrigation architecture:
it ingests sensor telemetry, notices when a sensor goes down, and keeps irrigating using
that sensor's **last valid measurement** (TNF-1.3, TNF-1.4, FR-6, FR-8, FR-4, TNF-2.2).

## Run

```bash
docker compose up --build
```

| URL | What |
|---|---|
| http://localhost:3000 | React dashboard (sensors, warnings, decisions, latest DB readings, kill/revive buttons) |
| http://localhost:8000/docs | Farm Backend OpenAPI docs |
| http://localhost:8001/docs | Sensor emulator control API |

The **main output is the backend log**: `docker compose logs -f farm-backend`

## Demo script (the "sensor goes down" scenario)

1. `docker compose up --build`, then follow the backend log. Every 5 s you see one decision per sensor, tagged `[fresh ]`.
2. Kill a sensor (dashboard button, or `curl -X POST localhost:8001/sensors/soil-2/down`). The emulator flips its `is_up` bool to `false` and stops sending.
3. After `SENSOR_TIMEOUT_SECONDS` (15 s) the log shows `sensor=soil-2 DOWN -> ...` and a warning appears on the dashboard.
4. Look at the planner lines: `soil-2` is still planned, now tagged `[CACHED]`, using the last value stored in PostgreSQL. All other sensors continue normally. Nothing stopped.
5. Revive it (`curl -X POST localhost:8001/sensors/soil-2/up`): `RECOVERED` is logged and decisions go back to `[fresh ]`.

Verify the persisted data: `docker compose exec db psql -U farm -c "select * from sensor_readings order by timestamp desc limit 10;"`

## Layout

```
docker-compose.yml
CLAUDE.md                  project context / memory for AI assistants (read this first)
db/                        PostgreSQL image + init.sql (table sensor_readings)
farm_backend/              Python service  <- the focus
  app/
    main.py                composition root: wiring + background loops
    config.py              all tunables, via environment variables
    models.py              DTOs
    data/                  Farm Data Provider + Repository (only code that touches the DB)
    gateway_connector/     POST /gateway/readings, sensor liveness monitor, command dispatcher
    irrigation_planner/    rules.py (if/else), anomaly.py, planner.py (cycle + cached fallback)
    dashboard_api/         read-only /api/* endpoints for the UI
    auth/  weather/        placeholders (not implemented, documented why)
  tests/                   pytest, no database needed
sensor_simulator/          emulated hardware: random readings + up/down control API
ui/                        React (Vite) dashboard served by nginx
```

The `farm_backend/app` sub-packages mirror the components of the architecture document
(section 7.2.1 logical view, 7.3.1 repository structure).

## Tests

```bash
cd farm_backend && pip install -r requirements.txt pytest && python -m pytest
```

## Tuning

Environment variables in `docker-compose.yml`: `SENSOR_TIMEOUT_SECONDS` (document value: 300),
`PLANNING_INTERVAL_SECONDS`, `MOISTURE_LOW/HIGH/TARGET`, `LOG_LEVEL=DEBUG` (prints every reading),
and on the emulator `SEND_INTERVAL_SECONDS`, `ANOMALY_PROBABILITY`.

## Not in the prototype (by design)

Authentication (FR-5), weather integration (FR-3), PID control (FR-4 is plain if/else), MQTT + real
field gateway (replaced by HTTP from the emulator), manual overrides (FR-7), PDF reports / regulator
backend (FR-10), Kubernetes, cloud sync. Decisions and warnings live in memory + logs, not in the DB.
