"""
Base adapters for converting DTOs to repository query objects.

Re-exported for backward compatibility; defined in the data layer.
"""

from __future__ import annotations

from ai.backend.manager.data.filter.adapter import BaseFilterAdapter

__all__ = ["BaseFilterAdapter"]
