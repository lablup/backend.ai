from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.config import DefaultModelDefinition
from ai.backend.manager.data.runtime_variant.types import RuntimeVariantData
from ai.backend.manager.errors.repository import UniqueConstraintViolationError
from ai.backend.manager.errors.resource import RuntimeVariantConflict
from ai.backend.manager.models.runtime_variant.row import RuntimeVariantRow
from ai.backend.manager.models.specs.creator import GlobalEntityCreator
from ai.backend.manager.models.specs.types import IntegrityErrorCheck


@dataclass
class RuntimeVariantCreator(GlobalEntityCreator[RuntimeVariantRow, RuntimeVariantData]):
    """Creator for a runtime variant — a name in the global runtime catalog."""

    name: str
    description: str | None

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return (
            IntegrityErrorCheck(
                violation_type=UniqueConstraintViolationError,
                error=RuntimeVariantConflict(f"Duplicate runtime variant name: {self.name}"),
            ),
        )

    @override
    def build_row(self) -> RuntimeVariantRow:
        return RuntimeVariantRow(
            name=self.name,
            description=self.description,
            default_model_definition=DefaultModelDefinition(),
        )

    @override
    def to_data(self, row: RuntimeVariantRow) -> RuntimeVariantData:
        return row.to_data()
