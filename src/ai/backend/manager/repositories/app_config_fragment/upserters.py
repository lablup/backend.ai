"""UpserterSpec implementations for app config fragment repository."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.common.data.app_config.types import AppConfigScopeType
from ai.backend.common.identifier.app_config import AppConfigScopeID
from ai.backend.manager.errors.app_config import AppConfigFragmentWriteNotAllowed
from ai.backend.manager.errors.repository import ForeignKeyViolationError
from ai.backend.manager.models.app_config_fragment.row import AppConfigFragmentRow
from ai.backend.manager.repositories.base import IntegrityErrorCheck
from ai.backend.manager.repositories.base.upserter import UpserterSpec


@dataclass
class AppConfigFragmentUpserterSpec(UpserterSpec[AppConfigFragmentRow]):
    """UpserterSpec for one app config fragment: insert it, or replace its ``config`` on conflict.

    The conflict target is the fragment's ``(config_name, scope_type, scope_id)`` — for
    ``public`` the partial unique index guarded by ``scope_id IS NULL`` (the db_source picks
    the target). The FK to ``app_config_allow_list`` is the write gate, as for a create.
    """

    config_name: str
    scope_type: AppConfigScopeType
    scope_id: AppConfigScopeID | None
    config: dict[str, Any]

    @property
    @override
    def row_class(self) -> type[AppConfigFragmentRow]:
        return AppConfigFragmentRow

    @override
    def build_insert_values(self) -> dict[str, Any]:
        return {
            "config_name": self.config_name,
            "scope_type": self.scope_type,
            "scope_id": self.scope_id,
            "config": self.config,
        }

    @override
    def build_update_values(self) -> dict[str, Any]:
        # Only ``config`` is replaced; bump ``updated_at`` explicitly since the raw upsert
        # statement bypasses the ORM ``onupdate`` hook.
        return {"config": self.config, "updated_at": sa.func.now()}

    @property
    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        # The FK to app_config_allow_list is the gate: an upsert of a config with no
        # allow-list row for (config_name, scope_type) surfaces as write-not-allowed.
        return (
            IntegrityErrorCheck(
                violation_type=ForeignKeyViolationError,
                constraint_name="fk_app_config_fragments_config_name_scope_type",
                error=AppConfigFragmentWriteNotAllowed(
                    f"Writing app config {self.config_name!r} at scope "
                    f"{self.scope_type.value!r} is not allowed."
                ),
            ),
        )
