"""Generic reconciler markers shared across layers (bound for entity category enums)."""

from __future__ import annotations

from enum import StrEnum


class BaseReconcilerCategory(StrEnum):
    """Empty bound for per-entity reconcile category enums (history separation axis)."""
