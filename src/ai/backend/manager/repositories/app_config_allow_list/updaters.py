"""UpdaterSpec implementations for app config allow-list repository."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, override

from ai.backend.common.data.app_config.types import AppConfigAccessLevel
from ai.backend.manager.models.app_config_allow_list.row import AppConfigAllowListRow
from ai.backend.manager.repositories.base.updater import UpdaterSpec
from ai.backend.manager.types import OptionalState


@dataclass
class AppConfigAllowListUpdaterSpec(UpdaterSpec[AppConfigAllowListRow]):
    """UpdaterSpec for app config allow-list entries.

    ``rank`` and the access tiers (``read_access`` / ``write_access``) are updatable —
    re-ordering the merge and re-policying who may read/write are the post-create
    adjustments an entry supports. The identity pair (``config_name``, ``scope_type``)
    is immutable: changing it means purging the entry (which cascades to its
    fragments) and creating a new one.
    """

    rank: OptionalState[int] = field(default_factory=OptionalState[int].nop)
    read_access: OptionalState[AppConfigAccessLevel] = field(
        default_factory=OptionalState[AppConfigAccessLevel].nop
    )
    write_access: OptionalState[AppConfigAccessLevel] = field(
        default_factory=OptionalState[AppConfigAccessLevel].nop
    )

    @property
    @override
    def row_class(self) -> type[AppConfigAllowListRow]:
        return AppConfigAllowListRow

    @override
    def build_values(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.rank.update_dict(to_update, "rank")
        self.read_access.update_dict(to_update, "read_access")
        self.write_access.update_dict(to_update, "write_access")
        return to_update
