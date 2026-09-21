"""Listing invitations, from whichever side the reader stands on."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.entity_share import EntityShareEntityType
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.ops.base import ScopedSearchOpsAction
from ai.backend.manager.data.entity_share.types import EntityShareData
from ai.backend.manager.models.entity_share.row import EntityShareRow

__all__ = ("SearchEntitySharesAction",)


@dataclass(frozen=True)
class SearchEntitySharesAction(ScopedSearchOpsAction[EntityShareRow, EntityShareData]):
    """Page through the invitations the named sides reach, combined with OR.

    Every side is authorized before the read runs, so a caller reaching for one they
    cannot see is refused rather than served the rest.
    """

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityShareEntityType()

    @override
    @classmethod
    def action_name(cls) -> str:
        return "search_entity_shares"
