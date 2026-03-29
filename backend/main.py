"""
Nexora Backend - FastAPI Application
Main API application for Nexora distributed node network
"""

from fastapi import FastAPI
from database import init_db, engine
from models import Base
from routes import user_routes, node_routes, points_routes

# Create FastAPI app
app = FastAPI(
    title="Nexora API",
    description="Backend API for Nexora distributed node network",
    version="1.0.0"
)

# Include routers
app.include_router(user_routes.router)
app.include_router(node_routes.router)
app.include_router(points_routes.router)


@app.on_event("startup")
def startup_event():
    """Initialize database tables on startup"""
    Base.metadata.create_all(bind=engine)


@app.get("/")
def root():
    """Root endpoint"""
    return {
        "service": "Nexora API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
