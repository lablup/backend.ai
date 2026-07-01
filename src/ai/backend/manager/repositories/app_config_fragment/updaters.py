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

    Only ``config`` is updatable (replaced wholesale). ``rank`` is assigned at create and is
    never updatable — re-ordering is not exposed through the update path.
    """

    config: OptionalState[dict[str, Any]] = field(default_factory=OptionalState[dict[str, Any]].nop)

    @property
    @override
    def row_class(self) -> type[AppConfigFragmentRow]:
        return AppConfigFragmentRow

    @override
    def build_values(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.config.update_dict(to_update, "config")
        return to_update
