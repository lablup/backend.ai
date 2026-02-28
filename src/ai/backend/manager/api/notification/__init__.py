"""
REST API handlers for notification system.
Provides CRUD endpoints for notification channels and rules.
"""

from __future__ import annotations

from .handler import create_app

__all__ = ("create_app",)
