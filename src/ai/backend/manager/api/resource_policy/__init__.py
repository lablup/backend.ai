"""
REST API handlers for resource policy management.
Provides CRUD endpoints for keypair, user, and project resource policy operations.
"""

from __future__ import annotations

from .handler import create_app

__all__ = ("create_app",)
