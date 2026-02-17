"""
REST API handlers for domain management.
Provides CRUD endpoints for domain (tenant) operations.
"""

from __future__ import annotations

from .handler import create_app

__all__ = ("create_app",)
