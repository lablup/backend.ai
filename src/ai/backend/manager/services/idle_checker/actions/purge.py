from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from typing import Self, override

from ai.backend.common.data.entity.idle_checker import IdleCheckerID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import PartialBulkPurgeGlobalEntityOpsAction
from ai.backend.manager.data.idle_checker.types import IdleCheckerData
from ai.backend.manager.models.idle_checker.purgers import IdleCheckerPurger
from ai.backend.manager.models.idle_checker.row import IdleCheckerRow


@dataclass(frozen=True)
class BulkPurgeIdleCheckersAction(
    PartialBulkPurgeGlobalEntityOpsAction[IdleCheckerRow, IdleCheckerData]
):
    """Remove the named idle checker definitions for good, answering for each one.

    The bindings and session rows referencing a removed definition follow it through
    ``ON DELETE CASCADE``.
    """

    ids: Sequence[IdleCheckerID]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "bulk_purge_idle_checkers"

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return tuple(self.ids)

    @override
    def to_purgers(self) -> Mapping[EntityIdentifier, IdleCheckerPurger]:
        return {checker_id: IdleCheckerPurger(checker_id=checker_id) for checker_id in self.ids}

    @override
    def narrowed_to(self, entity_ids: Sequence[EntityIdentifier]) -> Self:
        allowed = frozenset(entity_ids)
        return replace(self, ids=[checker_id for checker_id in self.ids if checker_id in allowed])
