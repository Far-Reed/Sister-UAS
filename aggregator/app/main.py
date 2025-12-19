from fastapi import FastAPI, HTTPException
from app.db import get_pool
from pydantic import BaseModel
from asyncpg.exceptions import UniqueViolationError
import json

app = FastAPI()

@app.on_event("startup")
async def startup():
    app.state.pool = await get_pool()

@app.on_event("shutdown")
async def shutdown():
    await app.state.pool.close()


class IngestEvent(BaseModel):
    topic: str
    event_id: str
    source: str
    payload: dict


@app.post("/ingest")
async def ingest(event: IngestEvent):
    query = """
        INSERT INTO processed_events (
            topic,
            event_id,
            source,
            payload,
            received_at,
            status
        )
        VALUES ($1, $2, $3, $4::jsonb, NOW(), 'received')
    """

    async with app.state.pool.acquire() as conn:
        # 1️⃣ selalu dihitung
        await conn.execute(
            "UPDATE agg_stats SET received = received + 1 WHERE id = 1"
        )

        try:
            # 2️⃣ dedup atomik via UNIQUE(topic, event_id)
            await conn.execute(
                query,
                event.topic,
                event.event_id,
                event.source,
                json.dumps(event.payload)
            )

            # 3️⃣ event unik
            await conn.execute(
                "UPDATE agg_stats SET unique_processed = unique_processed + 1 WHERE id = 1"
            )

            return {"status": "accepted", "event_id": event.event_id}

        except UniqueViolationError:
            # 4️⃣ duplicate yang sah secara bisnis
            await conn.execute(
                "UPDATE agg_stats SET duplicate_dropped = duplicate_dropped + 1 WHERE id = 1"
            )
            raise HTTPException(status_code=409, detail="duplicate event")

@app.get("/stats")
async def get_stats():
    async with app.state.pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT received, unique_processed, duplicate_dropped
            FROM agg_stats
            WHERE id = 1
        """)

        if not row:
            raise HTTPException(status_code=500, detail="stats not initialized")

        return {
            "received": row["received"],
            "unique_processed": row["unique_processed"],
            "duplicate_dropped": row["duplicate_dropped"],
        }

