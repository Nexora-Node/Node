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
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Import models so all tables are registered before create_all
    import models  # noqa
    # Run migration first (adds tokens, claimed_tokens, last_claim_at columns)
    try:
        from migrate_tokens import migrate
        migrate()
    except Exception as e:
        print(f"WARNING: Migration error: {e}")
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        print(f"WARNING: Could not create tables: {e}")
        print("App will start anyway — DB may not be ready yet.")
    yield


app = FastAPI(
    title="Nexora API",
    description="Backend API for Nexora distributed node network",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://node-delta-ten.vercel.app",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from routes import user_routes, node_routes, token_routes, security_routes
from routes import chain_routes, mining_routes

app.include_router(user_routes.router)
app.include_router(node_routes.router)
app.include_router(token_routes.router)
app.include_router(security_routes.router)
app.include_router(chain_routes.router)
app.include_router(mining_routes.router)


@app.get("/")
def root():
    return {"service": "Nexora API", "version": "2.0.0", "status": "running"}


@app.get("/health")
def health_check():
    import os
    db_url = os.environ.get("DATABASE_URL", "NOT SET")
    db_type = "postgresql" if "postgresql" in db_url or "postgres" in db_url else "sqlite"
    return {"status": "healthy", "db": db_type}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
