"""Update specs for the artifacts table."""

from __future__ import annotations

from collections.abc import Collection, Sequence
from dataclasses import dataclass, field
from typing import Any, override
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.data.entity.artifact import ArtifactID
from ai.backend.manager.data.artifact.types import ArtifactAvailability, ArtifactData
from ai.backend.manager.models.artifact.conditions import ArtifactConditions
from ai.backend.manager.models.artifact.row import ArtifactRow
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.specs.types import IntegrityErrorCheck
from ai.backend.manager.models.specs.updater import (
    DataBatchUpdater,
    DataUpdater,
    GuardedDataUpdater,
)
from ai.backend.manager.types import TriState


@dataclass
class ArtifactUpdater(GuardedDataUpdater[ArtifactRow, ArtifactData]):
    """Edit one artifact's readonly flag and description.

    Guarded on availability: a deleted artifact is left alone and the caller is told
    nothing was written.
    """

    artifact_id: ArtifactID
    readonly: TriState[bool] = field(default_factory=TriState[bool].nop)
    description: TriState[str] = field(default_factory=TriState[str].nop)

    @property
    @override
    def row_class(self) -> type[ArtifactRow]:
        return ArtifactRow

    @override
    def target_id_column(self) -> InstrumentedAttribute[Any]:
        return ArtifactRow.id

    @override
    def target_id_value(self) -> UUID:
        return self.artifact_id

    @property
    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def guard_conditions(self) -> list[QueryCondition]:
        return [lambda: ArtifactRow.availability != ArtifactAvailability.DELETED]

    @override
    def build_values(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.readonly.update_dict(to_update, "readonly")
        self.description.update_dict(to_update, "description")
        return to_update

    @override
    def to_data(self, row: ArtifactRow) -> ArtifactData:
        return row.to_dataclass()


@dataclass
class ArtifactScanUpdater(DataUpdater[ArtifactRow, ArtifactData]):
    """Write back what a scan found about an artifact already registered.

    Separate from :class:`ArtifactUpdater` because the columns differ: a scan carries
    the registry's own description and extra, and stamps the row as touched.
    """

    artifact_id: ArtifactID
    extra: Any | None
    description: TriState[str] = field(default_factory=TriState[str].nop)

    @property
    @override
    def row_class(self) -> type[ArtifactRow]:
        return ArtifactRow

    @override
    def target_id_column(self) -> InstrumentedAttribute[Any]:
        return ArtifactRow.id

    @override
    def target_id_value(self) -> UUID:
        return self.artifact_id

    @property
    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_values(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {"extra": self.extra, "updated_at": sa.func.now()}
        self.description.update_dict(to_update, "description")
        return to_update

    @override
    def to_data(self, row: ArtifactRow) -> ArtifactData:
        return row.to_dataclass()


@dataclass
class ArtifactTouchUpdater(DataBatchUpdater[ArtifactRow, ArtifactData]):
    """Stamp the artifacts a scan wrote revisions under as touched."""

    artifact_ids: Collection[UUID]

    @property
    @override
    def row_class(self) -> type[ArtifactRow]:
        return ArtifactRow

    @override
    def conditions(self) -> list[QueryCondition]:
        return [ArtifactConditions.by_ids(self.artifact_ids)]

    @override
    def build_values(self) -> dict[str, Any]:
        return {"updated_at": sa.func.now()}

    @property
    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def to_data(self, row: ArtifactRow) -> ArtifactData:
        return row.to_dataclass()
