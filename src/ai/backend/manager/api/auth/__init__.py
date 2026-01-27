"""
Auth API module providing authentication middleware, decorators, and REST API handlers.

This module provides:
- Authentication middleware for HMAC, JWT, and hook-based authentication
- Authorization decorators (@auth_required, @admin_required, @superadmin_required)
- REST API handlers for auth operations (authorize, signup, signout, etc.)
"""

from __future__ import annotations

from typing import Any

from aiohttp import web

from .decorators import (
    admin_required,
    auth_required,
    auth_required_for_method,
    superadmin_required,
)
from .middleware import auth_middleware
from .utils import (
    _extract_auth_params,
    check_date,
    sign_request,
    validate_ip,
)


def create_app(
    default_cors_options: Any,
) -> tuple[web.Application, list[Any]]:
    """Create aiohttp application for auth API endpoints.

    Note: This wrapper defers handler import to avoid circular imports:
        dto.context -> services.processors -> repositories.repositories
        -> repositories.session.repository -> api.session -> api.auth/__init__
        -> api.auth/handler -> dto.context (circular!)

    Root cause: repositories.session.repository imports api.session.find_dependency_sessions
    TODO: Move find_dependency_sessions to repository layer, then remove this wrapper.
    """
    from .handler import create_app as _create_app

    return _create_app(default_cors_options)


__all__ = (
    # Middleware
    "auth_middleware",
    # Decorators
    "auth_required",
    "auth_required_for_method",
    "admin_required",
    "superadmin_required",
    # Utilities
    "check_date",
    "sign_request",
    "validate_ip",
    "_extract_auth_params",  # exposed for testing
    # App factory
    "create_app",
)
