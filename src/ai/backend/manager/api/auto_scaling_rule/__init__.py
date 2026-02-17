"""
REST API handlers for auto-scaling rule system.
Provides CRUD endpoints for auto-scaling rules.
"""

from __future__ import annotations

from .handler import create_app

__all__ = ("create_app",)
