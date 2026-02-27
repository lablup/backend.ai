"""CreatorSpec implementations for network repository."""

from __future__ import annotations

import uuid
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, override

from ai.backend.manager.models.network.row import NetworkRow
from ai.backend.manager.repositories.base import CreatorSpec


@dataclass
class NetworkCreatorSpec(CreatorSpec[NetworkRow]):
    """CreatorSpec for network creation."""

    name: str
    ref_name: str
    driver: str
    domain_name: str
    project_id: uuid.UUID
    options: Mapping[str, Any]

    @override
    def build_row(self) -> NetworkRow:
        return NetworkRow(
            self.name,
            self.ref_name,
            self.driver,
            self.domain_name,
            self.project_id,
            options=self.options,
        )
