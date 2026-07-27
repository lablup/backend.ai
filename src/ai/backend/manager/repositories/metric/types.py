from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from ai.backend.common.types import SessionId


@dataclass(frozen=True)
class SessionUtilizationMetricQuery:
    preset_id: UUID
    session_ids: Sequence[SessionId]
    evaluation_time: datetime


@dataclass(frozen=True)
class SessionUtilizationMetricResult:
    by_session: Mapping[SessionId, Decimal]
