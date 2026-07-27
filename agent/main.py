from __future__ import annotations

# pyrefly: ignore [missing-import]
import uvicorn
# pyrefly: ignore [missing-import]
from fastapi import FastAPI

from config import settings
# pyrefly: ignore [missing-import]
from middleware.auth import APIKeyMiddleware
from routes import health, services, system, logs

app = FastAPI(
    title="Servitor Agent",
    description="LAN-only API for managing game server services and system power state.",
    version="1.0.0",
    docs_url=None,   # Disable Swagger UI in production
    redoc_url=None,
)

app.add_middleware(APIKeyMiddleware)

app.include_router(health.router)
app.include_router(services.router)
app.include_router(system.router)
app.include_router(logs.router)


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        log_level="info",
    )
