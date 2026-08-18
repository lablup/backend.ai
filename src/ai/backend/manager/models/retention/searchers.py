"""Searcher implementations for the retention policy repository."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.manager.data.retention.types import RetentionPolicyData
from ai.backend.manager.models.retention.row import RetentionPolicyRow
from ai.backend.manager.models.specs.searcher import Searcher


@dataclass
class RetentionPolicySearcher(Searcher[RetentionPolicyRow, RetentionPolicyData]):
    @override
    def build_select(self) -> sa.sql.Select[Any]:
        return sa.select(RetentionPolicyRow)

    @override
    def to_data(self, row: RetentionPolicyRow) -> RetentionPolicyData:
        return row.to_data()
