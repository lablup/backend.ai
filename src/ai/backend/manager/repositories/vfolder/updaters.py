"""UpdaterSpec implementations for vfolder repository."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, override

from ai.backend.common.exception import BackendAIError
from ai.backend.manager.data.vfolder.types import VFolderOperationStatus
from ai.backend.manager.models.vfolder import VFolderPermission, VFolderRow
from ai.backend.manager.repositories.base.types import QueryCondition
from ai.backend.manager.repositories.base.updater import UpdaterSpec
from ai.backend.manager.types import OptionalState


@dataclass
class VFolderAttributeUpdaterSpec(UpdaterSpec[VFolderRow]):
    """UpdaterSpec for vfolder attribute updates."""

    name: OptionalState[str] = field(default_factory=OptionalState.nop)
    cloneable: OptionalState[bool] = field(default_factory=OptionalState.nop)
    mount_permission: OptionalState[VFolderPermission] = field(default_factory=OptionalState.nop)

    @property
    @override
    def row_class(self) -> type[VFolderRow]:
        return VFolderRow

    @override
    def build_values(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.name.update_dict(to_update, "name")
        self.cloneable.update_dict(to_update, "cloneable")
        self.mount_permission.update_dict(to_update, "permission")
        return to_update

    @override
    def guard_condition(self) -> QueryCondition | None:
        return None

    @override
    def not_found_error(self) -> BackendAIError | None:
        return None

    @override
    def on_guard_failure(self) -> BackendAIError | None:
        return None


class VFolderTrashUpdaterSpec(UpdaterSpec[VFolderRow]):
    """Set vfolder status to DELETE_PENDING (soft-delete / move to trash)."""

    @property
    @override
    def row_class(self) -> type[VFolderRow]:
        return VFolderRow

    @override
    def build_values(self) -> dict[str, Any]:
        return {"status": VFolderOperationStatus.DELETE_PENDING}

    @override
    def guard_condition(self) -> QueryCondition | None:
        return None

    @override
    def not_found_error(self) -> BackendAIError | None:
        return None

    @override
    def on_guard_failure(self) -> BackendAIError | None:
        return None
