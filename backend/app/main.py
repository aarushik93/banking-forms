from __future__ import annotations

from contextlib import asynccontextmanager

import structlog
from fastapi import APIRouter, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from app.config import get_settings, validate_production_settings
from app.database import SessionLocal
from app.logging_conf import RequestContextMiddleware, configure_logging
from app.routers import admin, applications, funds, health, lookups
from app.seed import seed_funds
from app.services.bsb import get_bsb_service

log = structlog.get_logger("app")


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    validate_production_settings(settings)
    try:
        with SessionLocal() as db:
            seed_funds(db)
    except SQLAlchemyError:
        if settings.env == "prod":
            raise
        log.warning(
            "fund_seed_skipped",
            hint="database schema missing — run `alembic upgrade head`",
        )
    if settings.env != "test":
        # Warm the BSB directory cache; non-fatal — lookups degrade gracefully.
        get_bsb_service().refresh()
    log.info(
        "startup",
        env=settings.env,
        kyc_provider=settings.kyc_provider,
        email_provider=settings.email_provider,
        bsb_directory_entries=get_bsb_service().entry_count(),
    )
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_json)
    is_prod = settings.env == "prod"
    app = FastAPI(
        title="Managed Funds Application API",
        version="1.0.0",
        lifespan=lifespan,
        docs_url=None if is_prod else "/docs",
        redoc_url=None,
        openapi_url=None if is_prod else "/openapi.json",
    )
    app.add_middleware(RequestContextMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    api = APIRouter(prefix="/api/v1")
    api.include_router(funds.router)
    api.include_router(lookups.router)
    api.include_router(applications.router)
    api.include_router(admin.router)
    app.include_router(api)

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        log.exception("unhandled_error", path=request.url.path)
        return JSONResponse(status_code=500, content={"detail": "Internal server error"})

    return app


app = create_app()
