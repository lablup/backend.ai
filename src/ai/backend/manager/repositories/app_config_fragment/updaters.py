"""UpdaterSpec implementations for app config fragment repository."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, override

from ai.backend.manager.models.app_config_fragment.row import AppConfigFragmentRow
from ai.backend.manager.repositories.base.updater import UpdaterSpec
from ai.backend.manager.types import OptionalState


@dataclass
class AppConfigFragmentUpdaterSpec(UpdaterSpec[AppConfigFragmentRow]):
    """UpdaterSpec for app config fragment updates.

    ``config`` is replaced wholesale; ``rank`` may be set explicitly for admin re-ordering.
    """

    config: OptionalState[dict[str, Any]] = field(default_factory=OptionalState[dict[str, Any]].nop)
    rank: OptionalState[int] = field(default_factory=OptionalState[int].nop)

    @property
    @override
    def row_class(self) -> type[AppConfigFragmentRow]:
        return AppConfigFragmentRow

    @override
    def build_values(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.config.update_dict(to_update, "config")
        self.rank.update_dict(to_update, "rank")
        return to_update
