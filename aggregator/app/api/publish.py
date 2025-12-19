from fastapi import APIRouter, HTTPException
router = APIRouter()

@router.post("/publish")
async def publish(event: dict):
    # validasi sederhana
    if not event.get("topic") or not event.get("event_id"):
        raise HTTPException(status_code=400, detail="invalid event")
    # TODO: insert ON CONFLICT + push to broker
    return {"status": "accepted"}
