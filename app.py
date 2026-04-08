"""Home Hospice Care Ops - FastAPI application serving API + React frontend."""

import os
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

from server.db import db
from server.routes import dashboard, providers, financials, quality


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("[Care Ops] Starting up...")
    await db.get_pool()
    if not db.is_demo_mode:
        await db.start_refresh_loop()
        print("[Care Ops] Lakebase connected")
    else:
        print("[Care Ops] Running in demo mode (no Lakebase)")
    yield
    print("[Care Ops] Shutting down...")
    await db.close()


app = FastAPI(
    title="Care Ops",
    description="Home Health & Hospice Operations Dashboard",
    version="1.0.0",
    lifespan=lifespan,
)


# Prevent browser from caching API responses so the frontend's
# 15-second polling always receives fresh data from Lakebase.
@app.middleware("http")
async def no_cache_api(request: Request, call_next):
    response = await call_next(request)
    if request.url.path.startswith("/api/"):
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response


app.include_router(dashboard.router)
app.include_router(providers.router)
app.include_router(financials.router)
app.include_router(quality.router)


@app.get("/api/health")
async def health():
    return {
        "status": "healthy",
        "lakebase": "connected" if not db.is_demo_mode else "demo_mode",
    }


# Serve React frontend
FRONTEND_DIST = Path(__file__).parent / "frontend" / "dist"

if FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")

    @app.get("/favicon.ico")
    async def favicon():
        fav = FRONTEND_DIST / "favicon.ico"
        if fav.exists():
            return FileResponse(fav)
        return JSONResponse(status_code=404, content={"detail": "Not found"})

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        if full_path.startswith("api/"):
            return JSONResponse(status_code=404, content={"detail": "Not found"})
        static_file = FRONTEND_DIST / full_path
        if static_file.is_file():
            return FileResponse(static_file)
        return FileResponse(FRONTEND_DIST / "index.html")


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
