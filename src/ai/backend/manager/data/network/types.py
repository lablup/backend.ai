from __future__ import annotations

import enum
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Final, override

from ai.backend.common.data.entity.network import NetworkID
from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.types import EntityData

__all__: Final[tuple[str, ...]] = (
    "NetworkData",
    "NetworkType",
)


class NetworkType(enum.StrEnum):
    VOLATILE = "volatile"
    PERSISTENT = "persistent"
    HOST = "host"


@dataclass(frozen=True)
class NetworkData(EntityData):
    id: NetworkID
    name: str
    ref_name: str
    driver: str
    project_id: ProjectID
    domain_name: str
    options: Mapping[str, Any]
    created_at: datetime
    updated_at: datetime | None

    @override
    def entity_id(self) -> NetworkID:
        return self.id
