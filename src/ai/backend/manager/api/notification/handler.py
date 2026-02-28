"""Backward-compatibility shim for the notification handler module.

All handler logic has been migrated to:

* ``api.rest.notification.handler`` — NotificationHandler class

This module is kept for import compatibility during the transition period.
"""

from __future__ import annotations

from ai.backend.manager.api.rest.notification.handler import NotificationHandler

__all__ = ("NotificationHandler",)
