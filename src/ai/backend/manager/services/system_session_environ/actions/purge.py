from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import PurgeEntityOpsAction
from ai.backend.manager.data.system_session_environ.types import SystemSessionEnvironData
from ai.backend.manager.models.system_session_environ.purgers import SystemSessionEnvironPurger
from ai.backend.manager.models.system_session_environ.row import SystemSessionEnvironRow

__all__ = ("PurgeSystemSessionEnvironAction",)


@dataclass(frozen=True)
class PurgeSystemSessionEnvironAction(
    PurgeEntityOpsAction[SystemSessionEnvironRow, SystemSessionEnvironData]
):
    """Remove a system session environ row with its virtual entity and every edge naming it."""

    purger: SystemSessionEnvironPurger

    @override
    @classmethod
    def action_name(cls) -> str:
        return "purge_system_session_environ"

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.purger.entity_id()

    @override
    def to_purger(self) -> SystemSessionEnvironPurger:
        return self.purger
