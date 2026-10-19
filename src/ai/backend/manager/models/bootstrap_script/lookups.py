"""Lookup specs for bootstrap scripts."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, override
from uuid import UUID

import sqlalchemy as sa

from ai.backend.common.data.entity.bootstrap_script import BootstrapScriptID
from ai.backend.common.data.entity.user import UserEntityType, UserID
from ai.backend.manager.models.bootstrap_script.row import BootstrapScriptRow
from ai.backend.manager.models.specs.lookup import FieldOwnerLookup


class BootstrapScriptOwnerLookup(FieldOwnerLookup[BootstrapScriptID, UserID]):
    """The user a bootstrap script is set on. A script set on another kind of entity
    resolves to no owner."""

    @override
    def build_query(self, field_ids: Sequence[BootstrapScriptID]) -> sa.sql.Select[Any]:
        return sa.select(BootstrapScriptRow.id, BootstrapScriptRow.entity_id).where(
            BootstrapScriptRow.id.in_(field_ids),
            BootstrapScriptRow.entity_type == UserEntityType(),
        )

    @override
    def to_entity_id(self, value: UUID) -> UserID:
        return UserID(value)
