"""Generic reconciler markers shared across layers (bound for entity category enums)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class BaseReconcilerCategory(StrEnum):
    """Empty bound for per-entity reconcile category enums (history separation axis)."""


@dataclass(frozen=True)
class LastHistory:
    """The entity's latest reconcile-history row, used to classify a FAILURE.

    Absent (``None``) when the entity has no prior history in the fetched category;
    ``started_at`` is when this phase first began (kept stable across merges)."""

    phase: str
    attempts: int
    started_at: datetime


class HandlerOutcome(StrEnum):
    """What a reconcile handler may report per entity.

    Deliberately excludes NEED_RETRY/EXPIRED/GIVE_UP: those are the coordinator's
    classification of a FAILURE from history + policy, never a handler's call.
    """

    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    STALE = "STALE"
    SKIPPED = "SKIPPED"
