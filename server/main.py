"""WonderwallAi API Server — FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from server.config import get_settings
from server.middleware import SecurityHeadersMiddleware

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s — %(message)s",
)
logger = logging.getLogger("wonderwallai.server")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle manager."""
    settings = get_settings()
    logger.info(f"Starting WonderwallAi API Server ({settings.environment})")

    # --- STARTUP ---

    # 1. Initialize database
    from server.db.engine import init_db

    await init_db()

    # 2. Pre-load shared embedding model
    from server.instance_cache import warm_shared_model

    warm_shared_model()

    logger.info(f"Server ready on port {settings.port}")

    yield

    # --- SHUTDOWN ---
    from server.db.engine import close_db
    from server.instance_cache import clear_cache

    clear_cache()
    await close_db()
    logger.info("Server shut down cleanly")


settings = get_settings()

app = FastAPI(
    title="WonderwallAi API",
    description="AI Firewall as a Service — protect your LLM applications",
    version="0.1.0",
    lifespan=lifespan,
)

# --- Middleware ---
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True if "*" not in settings.cors_origin_list else False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Routers ---
from server.api.health import router as health_router
from server.api.admin import router as admin_router
from server.api.scan import router as scan_router
from server.api.config import router as config_router
from server.api.canary import router as canary_router
from server.api.files import router as files_router
from server.api.usage import router as usage_router

app.include_router(health_router)
app.include_router(admin_router)
app.include_router(scan_router)
app.include_router(config_router)
app.include_router(canary_router)
app.include_router(files_router)
app.include_router(usage_router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "server.main:app",
        host="0.0.0.0",
        port=settings.port,
        reload=settings.is_development,
    )
