from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.manager.errors.repository import UniqueConstraintViolationError
from ai.backend.manager.errors.resource import RuntimeVariantConflict
from ai.backend.manager.models.runtime_variant.row import RuntimeVariantRow
from ai.backend.manager.repositories.base.creator import CreatorSpec
from ai.backend.manager.repositories.base.types import IntegrityErrorCheck


@dataclass
class RuntimeVariantCreatorSpec(CreatorSpec[RuntimeVariantRow]):
    name: str
    description: str | None

    @property
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
        row = RuntimeVariantRow()
        row.name = self.name
        row.description = self.description
        return row
