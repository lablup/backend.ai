from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, replace
from typing import Self, override

from ai.backend.common.data.entity.system_session_environ import SystemSessionEnvironID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import PartialBulkGetEntityOpsAction
from ai.backend.manager.data.system_session_environ.types import SystemSessionEnvironData
from ai.backend.manager.models.system_session_environ.queriers import (
    BulkSystemSessionEnvironQuerier,
)
from ai.backend.manager.models.system_session_environ.row import SystemSessionEnvironRow

__all__ = ("BulkGetSystemSessionEnvironsAction",)


@dataclass(frozen=True)
class BulkGetSystemSessionEnvironsAction(
    PartialBulkGetEntityOpsAction[SystemSessionEnvironRow, SystemSessionEnvironData]
):
    """Read the system session environ rows the caller named, one permission check per row."""

    ids: Sequence[SystemSessionEnvironID]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "bulk_get_system_session_environs"

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return tuple(self.ids)

    @override
    def to_querier(self) -> BulkSystemSessionEnvironQuerier:
        return BulkSystemSessionEnvironQuerier()

    @override
    def narrowed_to(self, entity_ids: Sequence[EntityIdentifier]) -> Self:
        allowed_ids = frozenset(entity_ids)
        return replace(
            self,
            ids=[environ_id for environ_id in self.ids if environ_id in allowed_ids],
        )
