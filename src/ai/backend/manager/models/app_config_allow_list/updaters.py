"""DataUpdater implementations for app config allow-list repository."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any, override
from uuid import UUID

from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.data.entity.app_config_allow_list import AppConfigAllowListID
from ai.backend.manager.data.app_config.types import AppConfigAllowListData
from ai.backend.manager.models.app_config_allow_list.row import AppConfigAllowListRow
from ai.backend.manager.models.specs.types import IntegrityErrorCheck
from ai.backend.manager.models.specs.updater import DataUpdater
from ai.backend.manager.types import OptionalState


@dataclass
class AppConfigAllowListUpdater(DataUpdater[AppConfigAllowListRow, AppConfigAllowListData]):
    """Updater for app config allow-list entries.

    Only ``rank`` is updatable — re-ordering the merge is the one post-create
    adjustment an entry supports. The identity pair (``config_name``, ``scope_type``)
    is immutable: changing it means purging the entry (which cascades to its
    fragments) and creating a new one.
    """

    allow_list_id: AppConfigAllowListID
    rank: OptionalState[int] = field(default_factory=OptionalState[int].nop)

    @property
    @override
    def row_class(self) -> type[AppConfigAllowListRow]:
        return AppConfigAllowListRow

    @override
    def target_id_column(self) -> InstrumentedAttribute[Any]:
        return AppConfigAllowListRow.id

    @override
    def target_id_value(self) -> UUID:
        return self.allow_list_id

    @property
    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_values(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.rank.update_dict(to_update, "rank")
        return to_update

    @override
    def to_data(self, row: AppConfigAllowListRow) -> AppConfigAllowListData:
        return row.to_data()
