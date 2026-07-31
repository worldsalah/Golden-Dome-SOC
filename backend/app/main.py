import asyncio
import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from app.api import ai, alerts, assets, audit, auth, connectors, deployment, detection_rules, discovery, hotel, incidents, mitre, onboarding, organizations, posture, reports, risk, security, soar, threat, threat_intel, users, validation, wazuh
from app.config.settings import get_settings
from app.database.database import AsyncSessionLocal, Base, engine
from app.utils.logging import setup_logging
from app.services.soar_service import SoarService
from app.services.sync_worker import sync_worker_loop
from app.utils.seed import seed_database

logger = logging.getLogger(__name__)


def create_application() -> FastAPI:
    settings = get_settings()
    setup_logging()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        logger.info("Starting %s v%s", settings.APP_NAME, settings.APP_VERSION)
        if settings.DEBUG:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
        if settings.SEED_DEMO_DATA:
            async with AsyncSessionLocal() as session:
                await seed_database(session)
            async with AsyncSessionLocal() as session:
                await SoarService(session).seed_builtin_playbooks()
        sync_task = asyncio.create_task(sync_worker_loop())
        logger.info("Started Wazuh sync background worker")
        yield
        sync_task.cancel()
        try:
            await sync_task
        except asyncio.CancelledError:
            pass
        logger.info("Shutting down %s", settings.APP_NAME)
        await engine.dispose()

    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="Golden Dome SOC Platform backend API.",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )

    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*"] if settings.DEBUG else settings.trusted_hosts,
    )

    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(TenantIsolationMiddleware)

    # Each router defines its own sub-path; the common /api prefix is added here.
    app.include_router(auth.router, prefix="/api")
    app.include_router(alerts.router, prefix="/api")
    app.include_router(assets.router, prefix="/api")
    app.include_router(incidents.router, prefix="/api")
    app.include_router(mitre.router, prefix="/api")
    app.include_router(reports.router, prefix="/api")
    app.include_router(users.router, prefix="/api")
    app.include_router(ai.router, prefix="/api")
    app.include_router(threat_intel.router, prefix="/api")
    app.include_router(risk.router, prefix="/api")
    app.include_router(threat.router, prefix="/api")
    app.include_router(detection_rules.router, prefix="/api")
    app.include_router(wazuh.router, prefix="/api")
    app.include_router(soar.router, prefix="/api")
    app.include_router(validation.router, prefix="/api")
    app.include_router(organizations.router, prefix="/api")
    app.include_router(audit.router, prefix="/api")
    app.include_router(connectors.router, prefix="/api")
    app.include_router(onboarding.router, prefix="/api")
    app.include_router(discovery.router, prefix="/api")
    app.include_router(posture.router, prefix="/api")
    app.include_router(hotel.router, prefix="/api")
    app.include_router(deployment.router, prefix="/api")
    app.include_router(security.router, prefix="/api")

    @app.get("/health", tags=["Health"])
    async def health_check():
        return {"status": "healthy", "service": "backend", "version": settings.APP_VERSION}

    @app.get("/ready", tags=["Health"])
    async def readiness_check():
        checks = {"database": "unavailable", "redis": "unavailable"}
        try:
            async with AsyncSessionLocal() as session:
                await session.execute(text("SELECT 1"))
            checks["database"] = "healthy"
        except Exception:
            logger.exception("Database readiness check failed")

        try:
            import redis.asyncio as redis
            client = redis.from_url(settings.REDIS_URL, socket_connect_timeout=2, socket_timeout=2)
            await client.ping()
            await client.aclose()
            checks["redis"] = "healthy"
        except Exception:
            logger.exception("Redis readiness check failed")

        healthy = all(status == "healthy" for status in checks.values())
        payload = {"status": "ready" if healthy else "degraded", "checks": checks}
        return payload if healthy else JSONResponse(status_code=503, content=payload)

    @app.get("/", tags=["Root"])
    async def root():
        return {
            "name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "docs": "/docs",
        }

    return app


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        return response


class TenantIsolationMiddleware(BaseHTTPMiddleware):
    """Extract tenant_id from JWT and attach to request state for query scoping."""

    async def dispatch(self, request: Request, call_next):
        from app.security.jwt import decode_token
        auth = request.headers.get("authorization", "")
        if auth.startswith("Bearer "):
            token = auth[7:]
            payload = decode_token(token)
            if payload and payload.get("type") == "access":
                request.state.tenant_id = payload.get("tenant_id")
            else:
                request.state.tenant_id = None
        else:
            request.state.tenant_id = None
        return await call_next(request)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.time()
        response = await call_next(request)
        duration = time.time() - start
        logger.info(
            "%s %s %d - %.4fs - %s",
            request.method,
            request.url.path,
            response.status_code,
            duration,
            request.client.host if request.client else "unknown",
        )
        return response


app = create_application()
