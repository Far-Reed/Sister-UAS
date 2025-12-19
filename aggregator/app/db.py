import asyncpg
import os

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://user:password@storage:5432/db"
)

async def get_pool():
    return await asyncpg.create_pool(DATABASE_URL)
