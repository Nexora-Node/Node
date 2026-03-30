"""
Nexora Backend - FastAPI Application
"""

import sys
import os
from contextlib import asynccontextmanager

# Allow running from project root (Railway) or from backend/ folder (local)
_here = os.path.dirname(os.path.abspath(__file__))
if _here not in sys.path:
    sys.path.insert(0, _here)

from fastapi import FastAPI
from database import engine, Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    import models  # noqa: ensure all models are registered before create_all
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Nexora API",
    description="Backend API for Nexora distributed node network",
    version="2.0.0",
    lifespan=lifespan,
)

from routes import user_routes, node_routes, points_routes, security_routes
from routes import debug_routes, chain_routes

app.include_router(user_routes.router)
app.include_router(node_routes.router)
app.include_router(points_routes.router)
app.include_router(security_routes.router)
app.include_router(debug_routes.router)
app.include_router(chain_routes.router)


@app.get("/")
def root():
    return {"service": "Nexora API", "version": "2.0.0", "status": "running"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
