from dataclasses import asdict

from fastapi import APIRouter, Query, Request

router = APIRouter(prefix="/api", tags=["dashboard"])


@router.get("/sensors")
async def sensors(request: Request):
    """Liveness of every known sensor + its last stored value."""
    state = request.app.state
    result = []
    for item in state.monitor.snapshot():
        last = await state.provider.get_last_reading(item["sensor_id"])
        result.append({
            **item,
            "last_value": last.value if last else None,
            "last_reading_at": last.timestamp if last else None,
        })
    return result


@router.get("/readings")
async def readings(request: Request, limit: int = Query(30, ge=1, le=500)):
    rows = await request.app.state.provider.get_recent_readings(limit)
    return [asdict(r) for r in rows]


@router.get("/decisions")
async def decisions(request: Request, limit: int = Query(30, ge=1, le=200)):
    return [asdict(d) for d in request.app.state.provider.get_decisions(limit)]


@router.get("/warnings")
async def warnings(request: Request, limit: int = Query(30, ge=1, le=200)):
    return [asdict(w) for w in request.app.state.provider.get_warnings(limit)]
