"""UpdaterSpec implementations for app config allow-list repository."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, override

from ai.backend.common.data.app_config.types import AppConfigPermission
from ai.backend.manager.models.app_config_allow_list.row import AppConfigAllowListRow
from ai.backend.manager.repositories.base.updater import UpdaterSpec
from ai.backend.manager.types import OptionalState


@dataclass
class AppConfigAllowListUpdaterSpec(UpdaterSpec[AppConfigAllowListRow]):
    """UpdaterSpec for app config allow-list entries.

    ``rank`` and ``permission`` are updatable — re-ordering the merge and re-policying who
    may write are the post-create adjustments an entry supports. The identity pair
    (``config_name``, ``scope_type``) is immutable: changing it means purging the entry
    (which cascades to its fragments) and creating a new one.
    """

    rank: OptionalState[int] = field(default_factory=OptionalState[int].nop)
    permission: OptionalState[AppConfigPermission] = field(
        default_factory=OptionalState[AppConfigPermission].nop
    )

    @property
    @override
    def row_class(self) -> type[AppConfigAllowListRow]:
        return AppConfigAllowListRow

    @override
    def build_values(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.rank.update_dict(to_update, "rank")
        self.permission.update_dict(to_update, "permission")
        return to_update
