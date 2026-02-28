"""Backward-compatibility shim for the notification adapter module.

All adapter logic has been migrated to:

* ``api.rest.notification.adapter`` — NotificationChannelAdapter, NotificationRuleAdapter

This module re-exports the public names so that existing code continues
to work during the transition period.
"""

from __future__ import annotations

from ai.backend.manager.api.rest.notification.adapter import (
    NotificationChannelAdapter,
    NotificationRuleAdapter,
)

__all__ = (
    "NotificationChannelAdapter",
    "NotificationRuleAdapter",
)
