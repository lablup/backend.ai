"""UpdaterSpec implementations for app_config repository."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, override

from ai.backend.manager.models.app_config import AppConfigRow
from ai.backend.manager.repositories.base.updater import UpdaterSpec
from ai.backend.manager.types import OptionalState


@dataclass
class AppConfigUpdaterSpec(UpdaterSpec[AppConfigRow]):
    """UpdaterSpec for app config updates.

    Note: App config uses upsert pattern with composite key (scope_type + scope_id),
    so this spec is used with custom db_source logic.
    """

    extra_config: OptionalState[dict[str, Any]] = field(
        default_factory=OptionalState[dict[str, Any]].nop
    )

    @property
    @override
    def row_class(self) -> type[AppConfigRow]:
        return AppConfigRow

    @override
    def build_values(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.extra_config.update_dict(to_update, "extra_config")
        return to_update
