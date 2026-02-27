"""Backward-compatibility shim for the auth module.

All authentication/authorization logic has been migrated to:

* ``api.rest.middleware.auth`` — auth_middleware + decorators
* ``api.rest.auth`` — AuthHandler + register_routes()

This module re-exports the public names so that existing code that does
``from ai.backend.manager.api.auth import auth_required`` continues to
work during the transition period.
"""

from __future__ import annotations

from ai.backend.manager.api.rest.middleware.auth import (
    _extract_auth_params,
    admin_required,
    admin_required_for_method,
    auth_middleware,
    auth_required,
    auth_required_for_method,
    check_date,
    get_handler_attr,
    set_handler_attr,
    sign_request,
    superadmin_required,
    superadmin_required_for_method,
    validate_ip,
)

__all__ = (
    "_extract_auth_params",
    "admin_required",
    "admin_required_for_method",
    "auth_middleware",
    "auth_required",
    "auth_required_for_method",
    "check_date",
    "get_handler_attr",
    "set_handler_attr",
    "sign_request",
    "superadmin_required",
    "superadmin_required_for_method",
    "validate_ip",
)
