"""DataQuerier implementations for the idle checker repository."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.identifier.idle_checker import IdleCheckerAssignmentID, IdleCheckerID
from ai.backend.manager.data.idle_checker.types import IdleCheckerAssignmentData, IdleCheckerData
from ai.backend.manager.models.idle_checker.row import IdleCheckerBindingRow, IdleCheckerRow
from ai.backend.manager.repositories.base.querier import DataQuerier


@dataclass
class IdleCheckerQuerier(DataQuerier[IdleCheckerRow, IdleCheckerData]):
    checker_id: IdleCheckerID

    @override
    def row_class(self) -> type[IdleCheckerRow]:
        return IdleCheckerRow

    @override
    def pk_value(self) -> IdleCheckerID:
        return self.checker_id

    @override
    def to_data(self, row: IdleCheckerRow) -> IdleCheckerData:
        return row.to_data()


@dataclass
class IdleCheckerAssignmentQuerier(DataQuerier[IdleCheckerBindingRow, IdleCheckerAssignmentData]):
    assignment_id: IdleCheckerAssignmentID

    @override
    def row_class(self) -> type[IdleCheckerBindingRow]:
        return IdleCheckerBindingRow

    @override
    def pk_value(self) -> IdleCheckerAssignmentID:
        return self.assignment_id

    @override
    def to_data(self, row: IdleCheckerBindingRow) -> IdleCheckerAssignmentData:
        return row.to_data()
