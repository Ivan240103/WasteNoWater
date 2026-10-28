# CLAUDE.md - project context for AI assistants

> Keep this file up to date. Paste/upload it at the start of any new chat about this project.

## Who / what
University of Groningen, Software Architecture 2026-27, **Group 5: Smart Farming**
(Divyashri Ravichandran, Maria Voicu, Anh Khoi Nguyen Ho, Ivan De Simone, Joel Kiers).
Source document: *Group_5_Software_Architecture_Document.pdf* (v0.8, 84 pages).
We are building a **prototype of the Farm Backend (Python)** to support the architecture evaluation
(document sections 8.1-8.3, tests PVT-1..PVT-4).

## System in one paragraph (from the document)
Local-first, microservice Smart Irrigation system for Mediterranean farms (Docker on a local Kubernetes
cluster, 2 replicas per service). Soil sensors -> MQTT -> **Field Gateway** (Mosquitto + queue managers +
MQTT<->REST translator) -> **Farm Backend** (Python) -> **Farm DB** (PostgreSQL) and **UI** (React);
irrigation commands go back through the gateway to valves. **Regulator Backend** (Node.js) reads the DB and
produces PDF reports. Separate **User DB**. Weather from Open-Meteo. Cloud (AWS) only as backup/sync.
Key ADRs: HDD-01 local-first storage, HDD-02 Open-Meteo, HDD-03 JWT + AES-128 over MQTT, HDD-04 field gateway;
SD-01 microservices, SD-02 MQTT, SD-03 push pattern; Repository pattern + DTOs in the backend.

## Farm Backend components (doc 7.2.1)
Farm Data Provider (only DB access; stores readings/decisions/overrides, publishes to dashboard),
Dashboard Backend, Authentication Component, Gateway Connector (receives readings, notices missing data,
forwards pending commands), Irrigation Planner (computes water per zone, talks only via the Farm Data
Provider), Weather Component.
Failure scenario (doc 7.4): no data from a sensor for 5 min -> Gateway Connector warns -> Farm Data Provider
publishes warning to UI -> fetches the **last reading** from the Farm DB -> Planner keeps going with it.

## Requirements the prototype targets
Doc 8.3 says it verifies **FR-4, FR-8, TNF-1.3, TNF-2.2**; PVT-4 = disconnect a sensor, next decision uses last
valid value, operator notified within 10 min (TNF-1.3, TNF-1.4). Also touches FR-1, FR-2, FR-6.
- FR-1 gather telemetry; FR-2 persist it; FR-4 decide irrigation (PID in the doc, if/else here);
  FR-6 detect unresponsive sensor; FR-8 flag anomalies.
- TNF-1.3 on sensor failure keep operating with last valid measurement; TNF-1.4 alert within 10 min;
  TNF-2.2 prediction within 3 min.
- UC1 numbers (not load-tested yet): <=1000 sensors, 2 KB/15 min, 100 ms persist.

## Decisions made with the user in chat (prototype scope)
1. Focus: Farm Backend in Python. Priority = backend with clear file separation; UI is NOT a priority.
2. Hardware is emulated: a separate service sends random data to the backend. A sensor going down is a
   simple bool `is_up` true -> false in the emulator (a down sensor simply stops sending).
3. Irrigation decision is not vital: simple if/else, output goes to the logs.
4. Docker Compose with >=3 services: Python backend, PostgreSQL, React UI (+ the emulator as a 4th).
5. DB schema minimal: table `sensor_readings(sensor_id, timestamp, value)`.
6. One folder per service: `farm_backend/`, `db/`, `ui/`, `sensor_simulator/`.
7. Sensor timeout is configurable; default 15 s for demos (doc: 5 min = SENSOR_TIMEOUT_SECONDS=300).
8. Decisions/warnings are kept in memory + logs (not in DB) to respect the single-table schema.
9. User asked that everything discussed in the chat be kept as memory -> this file is that memory.

## Status
Done and tested (unit tests + manual end-to-end run against real PostgreSQL 16 without Docker):
ingest endpoint, persistence, liveness monitor (DOWN/RECOVERED), planner with cached fallback, anomaly
flags, dashboard API, emulator with kill/revive, React dashboard (builds).
NOT yet verified: `docker compose up --build` itself (Dockerfiles/nginx proxy were not run in the authoring sandbox).

## Possible next steps
- PVT-1 / PVT-3 load test script (1000 sensors, burst of 1000 req/s, measure loss + 100 ms latency).
- PVT-2: gateway-side caching / resync (FR-9) - needs a field-gateway emulation with a queue.
- Persist decisions + notifications (tables irrigation_decision, farm_device_notification).
- Swap HTTP ingest for MQTT (Mosquitto) to match SD-02; JWT auth (FR-5); Open-Meteo weather (FR-3).
- Manual override endpoint (FR-7); PID instead of if/else (FR-4).

## Conventions
Python 3.12, FastAPI, asyncpg, no ORM (Repository pattern). Sub-packages mirror the doc's components.
Logger names: gateway, monitor, planner, dispatch, data. Config only via env vars (`app/config.py`).
