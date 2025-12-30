from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .routers import dhcp, arp, vlans, interfaces, shapers

app = FastAPI(
    title="OPNsense Monitor",
    description="API for monitoring OPNsense firewall",
    version="1.0.0",
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(dhcp.router)
app.include_router(arp.router)
app.include_router(vlans.router)
app.include_router(interfaces.router)
app.include_router(shapers.router)


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "ok", "service": "OPNsense Monitor"}


@app.get("/config")
async def get_config():
    """Get frontend config (refresh interval)."""
    settings = get_settings()
    return {"refresh_interval": settings.refresh_interval}
