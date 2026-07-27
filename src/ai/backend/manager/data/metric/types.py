from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal

from ai.backend.common.types import SessionId


@dataclass(frozen=True)
class SessionUtilizationMetricResult:
    by_session: Mapping[SessionId, Decimal]
