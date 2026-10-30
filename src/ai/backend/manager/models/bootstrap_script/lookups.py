"""Lookup specs for bootstrap scripts."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, override
from uuid import UUID

import sqlalchemy as sa

from ai.backend.common.data.entity.bootstrap_script import BootstrapScriptID
from ai.backend.common.data.entity.types import EntityType, RuntimeEntityID
from ai.backend.manager.models.bootstrap_script.row import BootstrapScriptRow
from ai.backend.manager.models.specs.lookup import RuntimeFieldOwnerLookup


class BootstrapScriptOwnerLookup(RuntimeFieldOwnerLookup[BootstrapScriptID]):
    """The entity each named bootstrap script is set on, read from the type and id on
    the row."""

    @override
    def build_query(self, field_ids: Sequence[BootstrapScriptID]) -> sa.sql.Select[Any]:
        return sa.select(
            BootstrapScriptRow.id, BootstrapScriptRow.entity_id, BootstrapScriptRow.entity_type
        ).where(BootstrapScriptRow.id.in_(field_ids))

    @override
    def owner_of(self, entity_type: EntityType, entity_id: UUID) -> RuntimeEntityID:
        return RuntimeEntityID(entity_type, entity_id)
