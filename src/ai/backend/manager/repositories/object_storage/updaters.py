"""UpdaterSpec implementations for object storage repository."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, override

from ai.backend.manager.models.object_storage import ObjectStorageRow
from ai.backend.manager.repositories.base.updater import UpdaterSpec
from ai.backend.manager.types import OptionalState


@dataclass
class ObjectStorageUpdaterSpec(UpdaterSpec[ObjectStorageRow]):
    """UpdaterSpec for object storage updates."""

    name: OptionalState[str] = field(default_factory=OptionalState.nop)
    host: OptionalState[str] = field(default_factory=OptionalState.nop)
    access_key: OptionalState[str] = field(default_factory=OptionalState.nop)
    secret_key: OptionalState[str] = field(default_factory=OptionalState.nop)
    endpoint: OptionalState[str] = field(default_factory=OptionalState.nop)
    region: OptionalState[str] = field(default_factory=OptionalState.nop)

    @property
    @override
    def row_class(self) -> type[ObjectStorageRow]:
        return ObjectStorageRow

    @override
    def build_values(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.name.update_dict(to_update, "name")
        self.host.update_dict(to_update, "host")
        self.access_key.update_dict(to_update, "access_key")
        self.secret_key.update_dict(to_update, "secret_key")
        self.endpoint.update_dict(to_update, "endpoint")
        self.region.update_dict(to_update, "region")
        return to_update
