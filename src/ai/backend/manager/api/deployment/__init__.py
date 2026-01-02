"""
REST API handlers for deployment system.
Provides CRUD endpoints for deployments and revisions.
"""

from __future__ import annotations

from .handler import create_app

__all__ = ("create_app",)
