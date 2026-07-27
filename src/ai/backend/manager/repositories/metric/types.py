from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime

from ai.backend.common.data.idle_checker.types import UtilizationKernelPolicy
from ai.backend.common.types import SessionId


@dataclass(frozen=True)
class SessionUtilizationMetricQuery:
    metric_name: str
    kernel_policy: UtilizationKernelPolicy
    time_window_seconds: int | None
    session_ids: Sequence[SessionId]
    evaluation_time: datetime
