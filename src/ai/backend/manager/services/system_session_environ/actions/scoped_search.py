from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.system_session_environ import SystemSessionEnvironEntityType
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.ops.base import ScopedSearchOpsAction
from ai.backend.manager.data.system_session_environ.types import SystemSessionEnvironData
from ai.backend.manager.models.system_session_environ.row import SystemSessionEnvironRow

__all__ = ("ScopedSearchSystemSessionEnvironsAction",)


@dataclass(frozen=True)
class ScopedSearchSystemSessionEnvironsAction(
    ScopedSearchOpsAction[SystemSessionEnvironRow, SystemSessionEnvironData]
):
    """Page through the system session environ rows the named scopes reach, combined with OR."""

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return SystemSessionEnvironEntityType()

    @override
    @classmethod
    def action_name(cls) -> str:
        return "scoped_search_system_session_environs"
