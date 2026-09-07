from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any, override

from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.data.entity.idle_checker import IdleCheckerID
from ai.backend.common.data.idle_checker.types import IdleCheckerSpec
from ai.backend.common.types import SessionTypes
from ai.backend.manager.data.idle_checker.types import IdleCheckerData
from ai.backend.manager.models.idle_checker.row import IdleCheckerRow
from ai.backend.manager.models.specs.types import IntegrityErrorCheck
from ai.backend.manager.models.specs.updater import DataUpdater
from ai.backend.manager.types import OptionalState, TriState


@dataclass
class IdleCheckerUpdater(DataUpdater[IdleCheckerRow, IdleCheckerData]):
    """Retune one stored idle checker definition.

    ``checker_type`` is not a field: the column is computed from ``spec`` by the
    database.
    """

    checker_id: IdleCheckerID
    name: OptionalState[str] = field(default_factory=OptionalState[str].nop)
    description: TriState[str] = field(default_factory=TriState[str].nop)
    target_session_types: OptionalState[list[SessionTypes]] = field(
        default_factory=OptionalState[list[SessionTypes]].nop
    )
    initial_grace_period_seconds: OptionalState[int] = field(default_factory=OptionalState[int].nop)
    spec: OptionalState[IdleCheckerSpec] = field(default_factory=OptionalState[IdleCheckerSpec].nop)

    @property
    @override
    def row_class(self) -> type[IdleCheckerRow]:
        return IdleCheckerRow

    @override
    def target_id_column(self) -> InstrumentedAttribute[Any]:
        return IdleCheckerRow.id

    @override
    def target_id_value(self) -> IdleCheckerID:
        return self.checker_id

    @property
    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_values(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.name.update_dict(to_update, "name")
        self.description.update_dict(to_update, "description")
        self.target_session_types.update_dict(to_update, "target_session_types")
        self.initial_grace_period_seconds.update_dict(to_update, "initial_grace_period_seconds")
        self.spec.update_dict(to_update, "spec")
        return to_update

    @override
    def to_data(self, row: IdleCheckerRow) -> IdleCheckerData:
        return row.to_data()
