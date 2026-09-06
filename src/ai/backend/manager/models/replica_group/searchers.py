"""List-read specs for replica groups."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.manager.data.deployment.types import ReplicaGroupData
from ai.backend.manager.models.replica_group.row import ReplicaGroupRow
from ai.backend.manager.models.specs.searcher import Searcher
from ai.backend.manager.views.replica_group import (
    ReplicaGroupDeploySchedulingView,
    ReplicaGroupScalingSchedulingView,
)


@dataclass
class ReplicaGroupSearcher(Searcher[ReplicaGroupRow, ReplicaGroupData]):
    @override
    def build_select(self) -> sa.sql.Select[Any]:
        return sa.select(ReplicaGroupRow)

    @override
    def to_data(self, row: ReplicaGroupRow) -> ReplicaGroupData:
        return row.to_data()


@dataclass
class ReplicaGroupDeploySchedulingViewSearcher(
    Searcher[ReplicaGroupRow, ReplicaGroupDeploySchedulingView]
):
    @override
    def build_select(self) -> sa.sql.Select[Any]:
        return sa.select(ReplicaGroupRow)

    @override
    def to_data(self, row: ReplicaGroupRow) -> ReplicaGroupDeploySchedulingView:
        return row.to_deploy_scheduling_view()


@dataclass
class ReplicaGroupScalingSchedulingViewSearcher(
    Searcher[ReplicaGroupRow, ReplicaGroupScalingSchedulingView]
):
    @override
    def build_select(self) -> sa.sql.Select[Any]:
        return sa.select(ReplicaGroupRow)

    @override
    def to_data(self, row: ReplicaGroupRow) -> ReplicaGroupScalingSchedulingView:
        return row.to_scaling_scheduling_view()
