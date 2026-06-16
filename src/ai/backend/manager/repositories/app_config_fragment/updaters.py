"""UpdaterSpec for AppConfigFragment rows."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, override

from ai.backend.manager.models.app_config_fragment.row import AppConfigFragmentRow
from ai.backend.manager.repositories.base.updater import UpdaterSpec
from ai.backend.manager.types import OptionalState


@dataclass
class AppConfigFragmentUpdaterSpec(UpdaterSpec[AppConfigFragmentRow]):
    """UpdaterSpec for `app_config_fragments`.

    `config` is replaced wholesale; `rank` (merge priority) is optionally
    updatable. The ``(scope_type, scope_id, name)`` natural key is fixed —
    changing any of those is a new row, not an update.
    """

    config: Mapping[str, Any]
    rank: OptionalState[int] = field(default_factory=OptionalState[int].nop)

    @property
    @override
    def row_class(self) -> type[AppConfigFragmentRow]:
        return AppConfigFragmentRow

    @override
    def build_values(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {"config": dict(self.config)}
        self.rank.update_dict(to_update, "rank")
        return to_update
