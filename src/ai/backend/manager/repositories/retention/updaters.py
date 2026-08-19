"""UpdaterSpec implementations for the retention repository."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, override

from ai.backend.manager.models.retention.row import RetentionPolicyRow
from ai.backend.manager.repositories.base.updater import UpdaterSpec


@dataclass
class LastSweptAtUpdaterSpec(UpdaterSpec[RetentionPolicyRow]):
    """Stamps a policy's ``last_swept_at`` after its category is swept."""

    last_swept_at: datetime

    @property
    @override
    def row_class(self) -> type[RetentionPolicyRow]:
        return RetentionPolicyRow

    @override
    def build_values(self) -> dict[str, Any]:
        return {"last_swept_at": self.last_swept_at}
