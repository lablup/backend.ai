from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.common.data.app_config.types import AppConfigScopeType
from ai.backend.common.data.entity.app_config_allow_list import AppConfigAllowListID
from ai.backend.manager.data.app_config.types import AppConfigAllowListData
from ai.backend.manager.models.app_config_allow_list.row import AppConfigAllowListRow
from ai.backend.manager.models.specs.created_in import CreatedInGlobal
from ai.backend.manager.models.specs.types import IntegrityErrorCheck
from ai.backend.manager.models.specs.upserter import EntityUpserter

__all__ = ("AppConfigAllowListUpserter",)


@dataclass
class AppConfigAllowListUpserter(
    CreatedInGlobal[AppConfigAllowListRow],
    EntityUpserter[AppConfigAllowListRow, AppConfigAllowListData],
):
    """Upserter for one allow-list entry. Conflict key: ``(config_name, scope_type)``.
    ``rank`` falls back to the scope type's default when not given."""

    config_name: str
    scope_type: AppConfigScopeType
    rank: int | None = None

    @override
    def entity_id(self, row: AppConfigAllowListRow) -> AppConfigAllowListID:
        return AppConfigAllowListID(row.id)

    @override
    def row_class(self) -> type[AppConfigAllowListRow]:
        return AppConfigAllowListRow

    @override
    def index_elements(self) -> list[str]:
        return ["config_name", "scope_type"]

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_insert_values(self) -> dict[str, Any]:
        return {
            "config_name": self.config_name,
            "scope_type": self.scope_type,
            "rank": self._rank(),
        }

    @override
    def build_update_values(self) -> dict[str, Any]:
        """``updated_at`` is set here: ``ON CONFLICT DO UPDATE`` bypasses the ORM's
        ``onupdate``."""
        return {"rank": self._rank(), "updated_at": sa.func.now()}

    @override
    def to_data(self, row: AppConfigAllowListRow) -> AppConfigAllowListData:
        return row.to_data()

    def _rank(self) -> int:
        return self.rank if self.rank is not None else self.scope_type.default_rank()
