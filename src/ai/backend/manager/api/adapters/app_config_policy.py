"""AppConfigPolicy adapter bridging DTOs and Processors.

Skeleton — concrete read methods (`get` / `search`) plus admin
mutations (`create` / `update` / `purge`) are added together with
the `AppConfigPolicy` GraphQL / REST surface in subsequent issues.
Inherits ``BaseAdapter`` so it can be wired into the central
``Adapters`` registry from day one.
"""

from __future__ import annotations

from .base import BaseAdapter


class AppConfigPolicyAdapter(BaseAdapter):
    """Adapter for AppConfigPolicy domain operations."""
