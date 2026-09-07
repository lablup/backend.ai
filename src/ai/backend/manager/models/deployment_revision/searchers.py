"""Searcher spec for the deployment_revisions table."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.manager.data.deployment.types import ModelRevisionData
from ai.backend.manager.models.deployment_revision.row import DeploymentRevisionRow
from ai.backend.manager.models.specs.searcher import Searcher


@dataclass
class ModelRevisionSearcher(Searcher[DeploymentRevisionRow, ModelRevisionData]):
    @override
    def build_select(self) -> sa.sql.Select[Any]:
        return sa.select(DeploymentRevisionRow)

    @override
    def to_data(self, row: DeploymentRevisionRow) -> ModelRevisionData:
        return row.to_data()
