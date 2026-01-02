from __future__ import annotations

import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from .schema.object_type import ObjectType


@dataclass
class CreateShareParams:
    name: str
    path: Path
    share_size_limit: Optional[int] = None
    create_path: bool = True
    validate_only: bool = False

    def query(self) -> dict[str, str]:
        return {
            "create-path": "true" if self.create_path else "false",
            "validate-only": "true" if self.validate_only else "false",
        }

    def body(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "name": self.name,
            "path": str(self.path),
        }
        if self.share_size_limit is not None:
            data["shareSizeLimit"] = self.share_size_limit
        return data


@dataclass
class GetShareParams:
    name: str

    def query(self) -> dict[str, str]:
        return {"spec": f"name=eq={self.name}"}


@dataclass
class ClusterMetricParams:
    site_id: uuid.UUID
    preceding_duration: str  # "7d", "24h", "60m"
    interval_duration: str  # "1d", "1h", "5m"

    # Available object_type values : CLUSTER, SHARE, STORAGE_VOLUME
    object_type: ObjectType = ObjectType.CLUSTER

    def query(self) -> dict[str, str]:
        return {
            "precedingDuration": self.preceding_duration,
            "intervalDuration": self.interval_duration,
        }
