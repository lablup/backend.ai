"""Export repositories container."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Self

from .db_source import ExportDBSource
from .registry import ExportReportRegistry
from .repository import ExportRepository

if TYPE_CHECKING:
    from ai.backend.manager.repositories.types import RepositoryArgs


@dataclass
class ExportRepositories:
    """Container for export-related repositories."""

    repository: ExportRepository

    @classmethod
    def create(cls, args: RepositoryArgs) -> Self:
        """Create ExportRepositories from repository args."""
        db_source = ExportDBSource(db=args.db)
        registry = ExportReportRegistry.create_default()

        return cls(
            repository=ExportRepository(
                db_source=db_source,
                registry=registry,
            ),
        )
