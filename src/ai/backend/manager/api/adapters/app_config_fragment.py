"""AppConfigFragment adapter bridging DTOs and Processors.

Skeleton — concrete create / read / update / purge / search methods
are added together with the `AppConfigFragment` GraphQL / REST
surface in subsequent issues. Inherits ``BaseAdapter`` so it can be
wired into the central ``Adapters`` registry from day one.
"""

from __future__ import annotations

from .base import BaseAdapter


class AppConfigFragmentAdapter(BaseAdapter):
    """Adapter for AppConfigFragment domain operations."""
