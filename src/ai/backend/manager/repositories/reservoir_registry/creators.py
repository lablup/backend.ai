"""CreatorSpec implementations for Reservoir registry domain."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from typing_extensions import override

from ai.backend.manager.repositories.base import CreatorSpec

if TYPE_CHECKING:
    from ai.backend.manager.models.reservoir_registry import ReservoirRegistryRow


@dataclass
class ReservoirRegistryCreatorSpec(CreatorSpec[ReservoirRegistryRow]):
    """CreatorSpec for Reservoir registry creation."""

    endpoint: str
    access_key: str
    secret_key: str
    api_version: str

    @override
    def build_row(self) -> ReservoirRegistryRow:
        from ai.backend.manager.models.reservoir_registry import ReservoirRegistryRow

        return ReservoirRegistryRow(
            endpoint=self.endpoint,
            access_key=self.access_key,
            secret_key=self.secret_key,
            api_version=self.api_version,
        )
