from __future__ import annotations

from dataclasses import dataclass, field
from datetime import timedelta
from typing import Any, override

from ai.backend.common.data.retention.types import RetentionCategory
from ai.backend.manager.models.retention.row import RetentionPolicyRow
from ai.backend.manager.repositories.base.updater import UpdaterSpec
from ai.backend.manager.types import OptionalState


@dataclass
class RetentionPolicyUpdaterSpec(UpdaterSpec[RetentionPolicyRow]):
    category: OptionalState[RetentionCategory] = field(
        default_factory=OptionalState[RetentionCategory].nop
    )
    retention_period: OptionalState[timedelta] = field(default_factory=OptionalState[timedelta].nop)
    enabled: OptionalState[bool] = field(default_factory=OptionalState[bool].nop)

    @property
    @override
    def row_class(self) -> type[RetentionPolicyRow]:
        return RetentionPolicyRow

    @override
    def build_values(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.category.update_dict(to_update, "category")
        self.retention_period.update_dict(to_update, "retention_period")
        self.enabled.update_dict(to_update, "enabled")
        return to_update
