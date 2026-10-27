from __future__ import annotations

from collections.abc import Collection, Sequence
from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.common.data.entity.global_entity import GlobalEntityName
from ai.backend.common.data.entity.system_session_environ import SystemSessionEnvironID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.data.system_session_environ.types import (
    SystemSessionEnvironScopeType,
    SystemSessionEnvironValueSource,
)
from ai.backend.manager.data.permission.global_entity import global_entity_id
from ai.backend.manager.data.system_session_environ.types import SystemSessionEnvironData
from ai.backend.manager.models.specs.types import IntegrityErrorCheck
from ai.backend.manager.models.specs.upserter import EntityUpserter
from ai.backend.manager.models.system_session_environ.row import SystemSessionEnvironRow
from ai.backend.manager.models.system_session_environ.searchable_fields import (
    SystemSessionEnvironSearchableFields,
)

__all__ = ("SystemSessionEnvironUpserter",)


@dataclass
class SystemSessionEnvironUpserter(
    EntityUpserter[SystemSessionEnvironRow, SystemSessionEnvironData]
):
    """Upserter for a binding at its owner: the public entity, a domain or a project.

    Conflict key: ``(key, scope_type, scope_id)`` among the rows not soft-deleted. A
    ``public`` binding is created in the `global` and `public` scopes, a domain's or a
    project's in that owner.
    """

    owner: EntityIdentifier
    value_source: SystemSessionEnvironValueSource
    key: str

    @override
    def row_class(self) -> type[SystemSessionEnvironRow]:
        return SystemSessionEnvironRow

    @override
    def entity_id(self, row: SystemSessionEnvironRow) -> SystemSessionEnvironID:
        return SystemSessionEnvironID(row.id)

    @override
    def created_in(self, row: SystemSessionEnvironRow) -> Collection[EntityIdentifier]:
        match SystemSessionEnvironScopeType.of_owner(self.owner):
            case SystemSessionEnvironScopeType.PUBLIC:
                return (
                    global_entity_id(GlobalEntityName.GLOBAL),
                    global_entity_id(GlobalEntityName.PUBLIC),
                )
            case SystemSessionEnvironScopeType.DOMAIN | SystemSessionEnvironScopeType.PROJECT:
                return (self.owner,)

    @override
    def index_elements(self) -> list[str]:
        return ["key", "scope_type", "scope_id"]

    @override
    def index_where(self) -> sa.ColumnElement[bool]:
        return SystemSessionEnvironRow.deleted_at.is_(None)

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_insert_values(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "scope_type": SystemSessionEnvironScopeType.of_owner(self.owner),
            "scope_id": self.owner,
            "value_source": self.value_source,
        }

    @override
    def build_update_values(self) -> dict[str, Any]:
        return {
            "value_source": self.value_source,
            "updated_at": sa.func.now(),
        }

    @override
    def to_data(self, row: SystemSessionEnvironRow) -> SystemSessionEnvironData:
        return SystemSessionEnvironSearchableFields.own.to_data(row)
