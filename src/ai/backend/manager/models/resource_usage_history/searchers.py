"""Searcher implementations for the usage bucket tables."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.manager.data.resource_usage_history.types import (
    DomainUsageBucketData,
    ProjectUsageBucketData,
    UserUsageBucketData,
)
from ai.backend.manager.models.resource_usage_history.row import (
    DomainUsageBucketRow,
    ProjectUsageBucketRow,
    UserUsageBucketRow,
)
from ai.backend.manager.models.specs.searcher import Searcher


@dataclass
class DomainUsageBucketSearcher(Searcher[DomainUsageBucketRow, DomainUsageBucketData]):
    @override
    def build_select(self) -> sa.sql.Select[Any]:
        return sa.select(DomainUsageBucketRow)

    @override
    def to_data(self, row: DomainUsageBucketRow) -> DomainUsageBucketData:
        return row.to_data()


@dataclass
class ProjectUsageBucketSearcher(Searcher[ProjectUsageBucketRow, ProjectUsageBucketData]):
    @override
    def build_select(self) -> sa.sql.Select[Any]:
        return sa.select(ProjectUsageBucketRow)

    @override
    def to_data(self, row: ProjectUsageBucketRow) -> ProjectUsageBucketData:
        return row.to_data()


@dataclass
class UserUsageBucketSearcher(Searcher[UserUsageBucketRow, UserUsageBucketData]):
    @override
    def build_select(self) -> sa.sql.Select[Any]:
        return sa.select(UserUsageBucketRow)

    @override
    def to_data(self, row: UserUsageBucketRow) -> UserUsageBucketData:
        return row.to_data()
