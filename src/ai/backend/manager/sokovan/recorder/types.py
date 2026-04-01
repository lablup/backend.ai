from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import TypeVar
from uuid import UUID

from pydantic import BaseModel

# Generic type variable for entity IDs
# Bound to UUID to ensure all entity IDs are UUID-based
EntityIdT = TypeVar("EntityIdT", bound=UUID)


class StepStatus(StrEnum):
    """Status of an execution step or phase."""

    SUCCESS = "success"
    FAILED = "failed"


class StepRecord(BaseModel):
    """Represents a recorded execution step (completed)."""

    name: str  # e.g., "check_quota", "pull_image"
    status: StepStatus
    started_at: datetime
    ended_at: datetime
    detail: str | None
    error_code: str | None = None


class PhaseRecord(BaseModel):
    """Represents a recorded phase containing multiple steps.

    Depth is limited to Phase → Step (no nested phases).
    """

    name: str  # e.g., "provisioner", "validator"
    status: StepStatus  # Phase's own status
    started_at: datetime
    ended_at: datetime
    detail: str | None
    steps: list[StepRecord]


class ExecutionRecord(BaseModel):
    """Top-level execution record for an entity.

    Contains phases, each with their steps.
    """

    started_at: datetime
    ended_at: datetime
    phases: list[PhaseRecord]


class RecordBuildData(BaseModel):
    """Data required for building execution records.

    Contains shared phases that apply to the entity.
    """

    started_at: datetime
    ended_at: datetime
    shared_phases: list[PhaseRecord]
