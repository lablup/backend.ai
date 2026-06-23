"""Pydantic models for the unified kernel/session ``status_data`` payload.

Tracks https://github.com/lablup/backend.ai/issues/679 (BA-253). The legacy
``status_data`` dict has four branches (``kernel``, ``session``, ``scheduler``,
``error``); the ``error`` branch was emitted in two incompatible shapes (single
dict vs. ``{name: 'MultiAgentError', collection: [...]}``) which forced
consumers to shape-sniff at runtime. This module defines a typed envelope that
exposes a single canonical ``errors`` list and tolerantly parses both legacy
shapes during the deprecation window.

This PR only introduces the model. Producers and consumers are migrated in a
follow-up sub-issue (#11337).
"""

from __future__ import annotations

from typing import Any

from pydantic import Field, model_validator

from ai.backend.common.api_handlers import BaseResponseModel

__all__ = (
    "ErrorDetailInfo",
    "KernelStatusBranch",
    "KernelStatusData",
    "SchedulerStatusBranch",
    "SchedulingPredicateInfo",
    "SessionStatusBranch",
)


class KernelStatusBranch(BaseResponseModel):
    """Kernel-level status fields written on container termination."""

    exit_code: int | None = Field(
        default=None,
        description="Process exit code reported by the kernel container.",
    )


class SessionStatusBranch(BaseResponseModel):
    """Session-level status fields."""

    status: str | None = Field(
        default=None,
        description="Free-form session status string set by the manager.",
    )


class SchedulingPredicateInfo(BaseResponseModel):
    """Single scheduling predicate evaluation result."""

    name: str = Field(description="Predicate identifier (e.g., 'reserved_time').")
    msg: str | None = Field(
        default=None,
        description="Failure message; null when the predicate passed.",
    )


class SchedulerStatusBranch(BaseResponseModel):
    """Scheduler retry / predicate state at the time of the last attempt."""

    msg: str | None = Field(default=None, description="Last scheduling message.")
    retries: int | None = Field(default=None, description="Number of retries attempted.")
    last_try: str | None = Field(
        default=None,
        description="ISO-8601 timestamp of the last scheduling attempt.",
    )
    passed_predicates: list[SchedulingPredicateInfo] = Field(default_factory=list)
    failed_predicates: list[SchedulingPredicateInfo] = Field(default_factory=list)


class ErrorDetailInfo(BaseResponseModel):
    """One error detail entry. Mirrors ``manager.exceptions.ErrorDetail``."""

    src: str = Field(description="Origin of the error (e.g., 'agent', 'other').")
    name: str = Field(description="Exception class name.")
    repr: str = Field(description="``repr()`` of the exception.")
    agent_id: str | None = Field(
        default=None,
        description="Agent that raised the error (populated in debug mode).",
    )
    traceback: str | None = Field(
        default=None,
        description="Traceback (populated in debug mode).",
    )


class KernelStatusData(BaseResponseModel):
    """Unified ``status_data`` envelope for kernels and sessions.

    Tolerantly parses legacy shapes by normalizing the single-``error`` and
    ``MultiAgentError`` ``collection`` forms into a flat ``errors`` list before
    Pydantic field validation. Producers populate only the relevant branches.
    """

    kernel: KernelStatusBranch | None = Field(default=None)
    session: SessionStatusBranch | None = Field(default=None)
    scheduler: SchedulerStatusBranch | None = Field(default=None)
    errors: list[ErrorDetailInfo] = Field(
        default_factory=list,
        description="Flat list of error details. Canonical going forward.",
    )

    @model_validator(mode="before")
    @classmethod
    def _normalize_legacy_error(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        if data.get("errors"):
            return data
        legacy = data.get("error")
        if not isinstance(legacy, dict):
            return data
        if legacy.get("name") == "MultiAgentError" and isinstance(legacy.get("collection"), list):
            normalized = list(legacy["collection"])
        else:
            normalized = [{k: v for k, v in legacy.items() if k != "collection"}]
        return {**data, "errors": normalized}
