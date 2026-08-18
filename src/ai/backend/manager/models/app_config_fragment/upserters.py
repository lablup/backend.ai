from __future__ import annotations

from collections.abc import Collection, Sequence
from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.common.data.app_config.types import AppConfigScopeType
from ai.backend.common.data.entity.app_config_fragment import AppConfigFragmentID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.data.app_config_fragment.types import AppConfigFragmentData
from ai.backend.manager.errors.app_config import AppConfigFragmentWriteNotAllowed
from ai.backend.manager.errors.repository import ForeignKeyViolationError
from ai.backend.manager.models.app_config_fragment.row import AppConfigFragmentRow
from ai.backend.manager.models.specs.types import IntegrityErrorCheck
from ai.backend.manager.models.specs.upserter import EntityUpserter, GlobalEntityUpserter


def _write_gate_check(config_name: str, scope_type: AppConfigScopeType) -> IntegrityErrorCheck:
    """The FK to ``app_config_allow_list``: writing a config no entry allows is refused."""
    return IntegrityErrorCheck(
        violation_type=ForeignKeyViolationError,
        constraint_name="fk_app_config_fragments_config_name_scope_type",
        error=AppConfigFragmentWriteNotAllowed(
            f"Writing app config {config_name!r} at scope {scope_type.value!r} is not allowed."
        ),
    )


def _replaced_config(config: dict[str, Any]) -> dict[str, Any]:
    """Only ``config`` is replaced; ``updated_at`` is bumped explicitly because the raw
    upsert statement bypasses the ORM ``onupdate`` hook."""
    return {"config": config, "updated_at": sa.func.now()}


@dataclass
class AppConfigFragmentUpserter(EntityUpserter[AppConfigFragmentRow, AppConfigFragmentData]):
    """Upserter for a fragment owned by a domain or a user.

    The owner is required, so the row always joins its owner's scope. A fragment that
    belongs to no one is ``public``, written through
    :class:`PublicAppConfigFragmentUpserter` instead.
    """

    config_name: str
    owner: EntityIdentifier
    config: dict[str, Any]

    @override
    def row_class(self) -> type[AppConfigFragmentRow]:
        return AppConfigFragmentRow

    @override
    def entity_id(self, row: AppConfigFragmentRow) -> EntityIdentifier:
        return AppConfigFragmentID(row.id)

    @override
    def member_of(self, row: AppConfigFragmentRow) -> Collection[EntityIdentifier]:
        return (self.owner,)

    @override
    def index_elements(self) -> list[str]:
        return ["config_name", "scope_type", "scope_id"]

    @override
    def build_insert_values(self) -> dict[str, Any]:
        return {
            "config_name": self.config_name,
            "scope_type": AppConfigScopeType.of_owner(self.owner),
            "scope_id": self.owner,
            "config": self.config,
        }

    @override
    def build_update_values(self) -> dict[str, Any]:
        return _replaced_config(self.config)

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return (_write_gate_check(self.config_name, AppConfigScopeType.of_owner(self.owner)),)

    @override
    def to_data(self, row: AppConfigFragmentRow) -> AppConfigFragmentData:
        return row.to_data()


@dataclass
class PublicAppConfigFragmentUpserter(
    GlobalEntityUpserter[AppConfigFragmentRow, AppConfigFragmentData]
):
    """Upserter for a ``public`` fragment, which belongs to no one.

    It takes no owner, so it can only ever write a public row; the conflict target keys
    on a NULL ``scope_id`` like any other, since the constraint is NULLS NOT DISTINCT.
    """

    config_name: str
    config: dict[str, Any]

    @override
    def row_class(self) -> type[AppConfigFragmentRow]:
        return AppConfigFragmentRow

    @override
    def entity_id(self, row: AppConfigFragmentRow) -> EntityIdentifier:
        return AppConfigFragmentID(row.id)

    @override
    def index_elements(self) -> list[str]:
        return ["config_name", "scope_type", "scope_id"]

    @override
    def build_insert_values(self) -> dict[str, Any]:
        return {
            "config_name": self.config_name,
            "scope_type": AppConfigScopeType.PUBLIC,
            "scope_id": None,
            "config": self.config,
        }

    @override
    def build_update_values(self) -> dict[str, Any]:
        return _replaced_config(self.config)

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return (_write_gate_check(self.config_name, AppConfigScopeType.PUBLIC),)

    @override
    def to_data(self, row: AppConfigFragmentRow) -> AppConfigFragmentData:
        return row.to_data()
