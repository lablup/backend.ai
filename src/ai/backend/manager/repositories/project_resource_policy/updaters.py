"""DataUpdater implementations for the project resource policy repository."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any, override

from ai.backend.manager.data.resource.types import ProjectResourcePolicyData
from ai.backend.manager.models.resource_policy.row import ProjectResourcePolicyRow
from ai.backend.manager.models.specs.types import IntegrityErrorCheck
from ai.backend.manager.models.specs.updater import DataUpdater
from ai.backend.manager.types import OptionalState


@dataclass
class ProjectResourcePolicyUpdater(
    DataUpdater[ProjectResourcePolicyRow, ProjectResourcePolicyData]
):
    name: str
    max_vfolder_count: OptionalState[int] = field(default_factory=OptionalState[int].nop)
    max_quota_scope_size: OptionalState[int] = field(default_factory=OptionalState[int].nop)
    max_vfolder_size: OptionalState[int] = field(default_factory=OptionalState[int].nop)
    max_network_count: OptionalState[int] = field(default_factory=OptionalState[int].nop)

    @property
    @override
    def row_class(self) -> type[ProjectResourcePolicyRow]:
        return ProjectResourcePolicyRow

    @override
    def pk_value(self) -> str:
        return self.name

    @property
    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_values(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.max_vfolder_count.update_dict(to_update, "max_vfolder_count")
        self.max_quota_scope_size.update_dict(to_update, "max_quota_scope_size")
        self.max_vfolder_size.update_dict(to_update, "max_vfolder_size")
        self.max_network_count.update_dict(to_update, "max_network_count")
        return to_update

    @override
    def to_data(self, row: ProjectResourcePolicyRow) -> ProjectResourcePolicyData:
        return row.to_dataclass()
