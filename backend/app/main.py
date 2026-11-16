"""StegaShield FastAPI application entrypoint.

Configures CORS, rate limiting, security headers, anonymous session cookies,
lifecycle hooks, and REST API routing.
"""

import asyncio
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator
import uuid

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
from starlette.middleware.base import BaseHTTPMiddleware

from app.api import api_router
from app.config import settings
import app.db.session as db_session_module
from app.services.file_store import file_store


async def _periodic_file_cleanup() -> None:
    """Background task that runs periodically to purge files exceeding the 30-min TTL."""
    while True:
        try:
            await asyncio.sleep(300)  # Every 5 minutes
            with db_session_module.SessionLocal() as db:
                file_store.cleanup_expired_files(db)
        except asyncio.CancelledError:
            break
        except Exception:
            pass


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan context manager for startup and shutdown procedures."""
    # 1. Initialize DB tables
    db_session_module.init_db()

    # 2. Start background TTL cleanup task
    cleanup_task = asyncio.create_task(_periodic_file_cleanup())

    try:
        yield
    finally:
        cleanup_task.cancel()
        try:
            await cleanup_task
        except asyncio.CancelledError:
            pass


# Rate Limiter setup
limiter = Limiter(key_func=get_remote_address, default_limits=["120/minute"])

app = FastAPI(
    title="StegaShield API",
    description="Academic-grade steganography, distortion analysis, and steganalysis experimentation laboratory API.",
    version="1.0.0",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# Security Headers & Session Cookie Middleware
class SecurityAndSessionMiddleware(BaseHTTPMiddleware):
    """Enforces HTTP security headers and establishes anonymous session cookies."""

    async def dispatch(self, request: Request, call_next: Any) -> Response:
        session_id = request.cookies.get("stegashield_session")
        set_cookie = False
        if not session_id:
            session_id = str(uuid.uuid4())
            set_cookie = True
        request.state.session_id = session_id

        response: Response = await call_next(request)

        if set_cookie:
            response.set_cookie(
                key="stegashield_session",
                value=session_id,
                httponly=True,
                samesite="lax",
                path="/",
            )

        # Enforce security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Content-Security-Policy"] = "default-src 'self'"

        return response


app.add_middleware(SecurityAndSessionMiddleware)
app.add_middleware(SlowAPIMiddleware)

# CORS Middleware
allowed_origins = [settings.FRONTEND_ORIGIN]
for local_origin in ("http://localhost:3000", "http://127.0.0.1:3000"):
    if local_origin not in allowed_origins:
        allowed_origins.append(local_origin)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include v1 REST API routes
app.include_router(api_router)


@app.get("/", tags=["Root"])
def root_info() -> dict[str, str]:
    """Root metadata endpoint."""
    return {
        "name": "StegaShield API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/v1/health",
    }
