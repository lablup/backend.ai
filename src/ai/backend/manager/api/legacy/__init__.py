"""
Legacy API handlers.

This module contains old function-based handlers preserved for regression testing.
These handlers should NOT be used in production - use the new class-based handlers instead.

Contents:
- auth: Legacy auth handlers (replaced by api/auth/ package)
"""

from __future__ import annotations

from . import auth

__all__ = ("auth",)
