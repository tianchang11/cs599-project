from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import time

from app.core.config import settings
from app.core.exceptions import AppError
from app.db.database import init_db, close_db

logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.app_name}...")
    try:
        await init_db()
        logger.info("Database initialized")
    except Exception as e:
        logger.warning(f"Database initialization failed: {e}")
    yield
    logger.info("Shutting down...")
    await close_db()


app = FastAPI(
    title=settings.app_name,
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_origin_regex=settings.cors_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    request_id = request.headers.get("X-Request-Id", "N/A")
    response = await call_next(request)
    duration = (time.time() - start) * 1000
    logger.info(
        f"{request.method} {request.url.path} -> {response.status_code} ({duration:.1f}ms) [req:{request_id}]"
    )
    response.headers["X-Request-Id"] = request_id
    return response


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):
    logger.warning(f"AppError: {exc.code} - {exc.message}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"code": exc.code, "detail": exc.message},
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


@app.get("/health")
async def health():
    return {"status": "ok", "service": settings.app_name, "version": "2.0.0"}


@app.get("/ready")
async def ready():
    from sqlalchemy import text as sa_text
    from app.db.database import async_session
    checks = {}
    db_status = "ok"
    try:
        async with async_session() as session:
            await session.execute(sa_text("SELECT 1"))
        db_status = "ok"
    except Exception as e:
        db_status = f"error: {e}"

    checks["database"] = db_status
    all_ok = db_status == "ok"

    return JSONResponse(
        status_code=200 if all_ok else 503,
        content={"status": "ok" if all_ok else "degraded", "checks": checks},
    )


from app.api.routes import auth, research, library, upload
app.include_router(auth.router, prefix="/api/settings", tags=["settings"])
app.include_router(research.router, prefix="/api/research", tags=["research"])
app.include_router(library.router, prefix="/api/library", tags=["library"])
app.include_router(upload.router, prefix="/api/upload", tags=["upload"])
