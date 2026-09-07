"""FieldQuerier implementations for deployment revisions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.data.entity.deployment_revision import DeploymentRevisionID
from ai.backend.manager.data.deployment.types import ModelRevisionData
from ai.backend.manager.models.deployment_revision.row import DeploymentRevisionRow
from ai.backend.manager.models.specs.querier import FieldQuerier


@dataclass
class ModelRevisionQuerier(FieldQuerier[DeploymentRevisionRow, ModelRevisionData]):
    revision_id: DeploymentRevisionID

    @override
    def row_class(self) -> type[DeploymentRevisionRow]:
        return DeploymentRevisionRow

    @override
    def target_id_column(self) -> InstrumentedAttribute[Any]:
        return DeploymentRevisionRow.id

    @override
    def target_id_value(self) -> DeploymentRevisionID:
        return self.revision_id

    @override
    def to_data(self, row: DeploymentRevisionRow) -> ModelRevisionData:
        return row.to_data()
