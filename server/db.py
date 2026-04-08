"""Lakebase (PostgreSQL) async connection pool with OAuth token refresh."""

import asyncio
import asyncpg
from typing import Optional, Any
from server.config import (
    LAKEBASE_HOST,
    LAKEBASE_PORT,
    LAKEBASE_DATABASE,
    LAKEBASE_USER,
    LAKEBASE_PASSWORD,
    get_oauth_token,
)


class LakebasePool:
    """Async database pool with OAuth token refresh support."""

    def __init__(self):
        self._pool: Optional[asyncpg.Pool] = None
        self._demo_mode = False
        self._refresh_task: Optional[asyncio.Task] = None

    async def get_pool(self) -> Optional[asyncpg.Pool]:
        if self._demo_mode:
            return None
        if self._pool is not None:
            return self._pool
        try:
            password = LAKEBASE_PASSWORD if LAKEBASE_PASSWORD else get_oauth_token()
            self._pool = await asyncpg.create_pool(
                host=LAKEBASE_HOST,
                port=LAKEBASE_PORT,
                database=LAKEBASE_DATABASE,
                user=LAKEBASE_USER,
                password=password,
                ssl="require",
                min_size=2,
                max_size=10,
                command_timeout=30,
            )
            return self._pool
        except Exception as e:
            print(f"[Lakebase] Connection failed: {e}")
            self._demo_mode = True
            return None

    async def refresh_token(self):
        if self._pool:
            await self._pool.close()
            self._pool = None
        self._demo_mode = False
        await self.get_pool()

    async def start_refresh_loop(self):
        async def _loop():
            while True:
                await asyncio.sleep(45 * 60)
                try:
                    await self.refresh_token()
                    print("[Lakebase] Token refreshed")
                except Exception as e:
                    print(f"[Lakebase] Token refresh failed: {e}")
        self._refresh_task = asyncio.create_task(_loop())

    async def close(self):
        if self._refresh_task:
            self._refresh_task.cancel()
        if self._pool:
            await self._pool.close()

    async def fetch(self, sql: str, *args) -> list[dict[str, Any]]:
        if self._demo_mode:
            return []
        pool = await self.get_pool()
        if not pool:
            return []
        async with pool.acquire() as conn:
            rows = await conn.fetch(sql, *args)
            return [dict(r) for r in rows]

    async def fetchrow(self, sql: str, *args) -> Optional[dict[str, Any]]:
        if self._demo_mode:
            return None
        pool = await self.get_pool()
        if not pool:
            return None
        async with pool.acquire() as conn:
            row = await conn.fetchrow(sql, *args)
            return dict(row) if row else None

    async def execute(self, sql: str, *args) -> str:
        if self._demo_mode:
            return "DEMO"
        pool = await self.get_pool()
        if not pool:
            return "NO_POOL"
        async with pool.acquire() as conn:
            return await conn.execute(sql, *args)

    @property
    def is_demo_mode(self) -> bool:
        return self._demo_mode


db = LakebasePool()
