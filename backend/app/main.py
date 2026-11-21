import logging
import sys
from pathlib import Path
from contextlib import asynccontextmanager

# Ensure backend root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.config import settings
from app.database import async_session_factory, engine, Base
from app.api.v1.api import api_router
from app.core.exceptions import (
    AppException,
    ConflictException,
    NotFoundException,
    ForbiddenException,
    UnauthorizedException,
    ValidationException,
)
from app.services.noshow_job import run_noshow_sweep

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("clinicq")

scheduler = AsyncIOScheduler()


async def scheduled_noshow_job():
    """Background evening job to sweep unattended appointments."""
    logger.info("Executing scheduled evening no-show sweep...")
    async with async_session_factory() as session:
        try:
            count = await run_noshow_sweep(session)
            logger.info(f"Scheduled no-show sweep completed: {count} appointments updated.")
        except Exception as e:
            logger.error(f"Error in scheduled no-show sweep: {e}", exc_info=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting ClinicQ API...")
    
    # Auto-create tables in dev/test if needed (in production Alembic runs migrations)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database schemas verified.")

    # Schedule evening no-show background sweep at 20:00 every day
    scheduler.add_job(
        scheduled_noshow_job,
        CronTrigger(hour=20, minute=0),
        id="evening_noshow_sweep",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("APScheduler started: evening no-show sweep scheduled for 20:00 daily.")

    yield

    # Shutdown
    logger.info("Shutting down ClinicQ API...")
    if scheduler.running:
        scheduler.shutdown(wait=False)
    await engine.dispose()


app = FastAPI(
    title="ClinicQ - Appointment & Queue System API",
    description="Production-grade API for clinic appointment scheduling, concurrency-safe booking, real-time live queue, and daily analytics.",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception Handlers
@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


@app.exception_handler(ConflictException)
async def conflict_exception_handler(request: Request, exc: ConflictException):
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"detail": exc.detail},
    )


@app.exception_handler(NotFoundException)
async def not_found_exception_handler(request: Request, exc: NotFoundException):
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": exc.detail},
    )


@app.exception_handler(ForbiddenException)
async def forbidden_exception_handler(request: Request, exc: ForbiddenException):
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content={"detail": exc.detail},
    )


@app.exception_handler(UnauthorizedException)
async def unauthorized_exception_handler(request: Request, exc: UnauthorizedException):
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"detail": exc.detail},
        headers=exc.headers or {"WWW-Authenticate": "Bearer"},
    )


@app.exception_handler(ValidationException)
async def validation_exception_handler(request: Request, exc: ValidationException):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.detail},
    )


@app.exception_handler(RequestValidationError)
async def fastapi_validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = []
    for error in exc.errors():
        field = " -> ".join(str(loc) for loc in error.get("loc", []))
        msg = error.get("msg")
        errors.append(f"{field}: {msg}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": "Validation error: " + "; ".join(errors), "errors": exc.errors()},
    )


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "service": "clinicq-backend",
        "version": "1.0.0",
        "reference_date": "2026-11-21",
    }


# Include API routers
app.include_router(api_router)
