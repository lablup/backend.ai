from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.idle_checker import IdleCheckerID
from ai.backend.common.data.idle_checker.types import IdleCheckerSpec
from ai.backend.common.types import SessionTypes
from ai.backend.manager.data.idle_checker.types import IdleCheckerData
from ai.backend.manager.models.idle_checker.row import IdleCheckerRow
from ai.backend.manager.models.specs.creator import GlobalEntityCreator
from ai.backend.manager.models.specs.types import IntegrityErrorCheck


@dataclass
class IdleCheckerCreator(GlobalEntityCreator[IdleCheckerRow, IdleCheckerData]):
    """Creator for an idle checker definition in the global catalog."""

    name: str
    description: str | None
    target_session_types: list[SessionTypes]
    initial_grace_period_seconds: int
    spec: IdleCheckerSpec

    @override
    def entity_id(self, row: IdleCheckerRow) -> IdleCheckerID:
        return IdleCheckerID(row.id)

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_row(self) -> IdleCheckerRow:
        return IdleCheckerRow(
            name=self.name,
            description=self.description,
            target_session_types=self.target_session_types,
            initial_grace_period_seconds=self.initial_grace_period_seconds,
            spec=self.spec,
        )

    @override
    def to_data(self, row: IdleCheckerRow) -> IdleCheckerData:
        return row.to_data()
