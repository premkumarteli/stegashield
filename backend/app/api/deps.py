"""API Dependencies for session scoping and database access."""

import uuid

from fastapi import Request

from app.db.session import get_db


def get_session_id(request: Request) -> str:
    """Retrieve session identifier from request state, cookie, or generate a fresh UUID."""
    if hasattr(request.state, "session_id") and request.state.session_id:
        return str(request.state.session_id)
    cookie_sid = request.cookies.get("stegashield_session")
    if cookie_sid:
        return cookie_sid
    new_sid = str(uuid.uuid4())
    request.state.session_id = new_sid
    return new_sid


__all__ = ["get_db", "get_session_id"]
