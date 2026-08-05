from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Self

from ai.backend.common.data.idle_checker.types import (
    CheckerType,
    IdleCheckerSpec,
    UtilizationThresholdEntry,
)
from ai.backend.common.data.permission.types import ScopeType
from ai.backend.common.identifier.idle_checker import IdleCheckerAssignmentID, IdleCheckerID
from ai.backend.common.identifier.prometheus_query_preset import PrometheusQueryPresetID
from ai.backend.common.types import SessionId, SessionTypes


@dataclass(frozen=True)
class IdleCheckSession:
    """Session fields needed to evaluate idle checkers."""

    session_id: SessionId
    created_at: datetime
    starts_at: datetime | None
    expire_at: datetime | None


@dataclass(frozen=True)
class SessionUtilizationQuery:
    """Hashable batching key: one Prometheus query per (preset, labels) combination."""

    preset_id: PrometheusQueryPresetID
    filter_labels: tuple[tuple[str, str], ...]
    group_labels: tuple[str, ...]

    @classmethod
    def from_threshold(cls, threshold: UtilizationThresholdEntry) -> Self:
        return cls(
            preset_id=threshold.preset_id,
            filter_labels=tuple(
                sorted((label.key, label.value) for label in threshold.filter_labels)
            ),
            group_labels=tuple(sorted(set(threshold.group_labels))),
        )


@dataclass(frozen=True)
class IdleCheckerAssignmentData:
    id: IdleCheckerAssignmentID
    scope_type: ScopeType
    scope_id: uuid.UUID
    idle_checker_id: IdleCheckerID
    enabled: bool
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class IdleCheckerData:
    id: IdleCheckerID
    name: str
    description: str | None
    checker_type: CheckerType
    target_session_types: list[SessionTypes]
    initial_grace_period_seconds: int
    spec: IdleCheckerSpec
    created_at: datetime
    updated_at: datetime
