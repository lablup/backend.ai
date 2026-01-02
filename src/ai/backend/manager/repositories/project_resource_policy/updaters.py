from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from typing_extensions import override

from ai.backend.manager.models.resource_policy import ProjectResourcePolicyRow
from ai.backend.manager.repositories.base.updater import UpdaterSpec
from ai.backend.manager.types import OptionalState


@dataclass
class ProjectResourcePolicyUpdaterSpec(UpdaterSpec[ProjectResourcePolicyRow]):
    """UpdaterSpec for project resource policy updates."""

    max_vfolder_count: OptionalState[int] = field(default_factory=OptionalState.nop)
    max_quota_scope_size: OptionalState[int] = field(default_factory=OptionalState.nop)
    max_vfolder_size: OptionalState[int] = field(default_factory=OptionalState.nop)
    max_network_count: OptionalState[int] = field(default_factory=OptionalState.nop)

    @property
    @override
    def row_class(self) -> type[ProjectResourcePolicyRow]:
        return ProjectResourcePolicyRow

    @override
    def build_values(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.max_vfolder_count.update_dict(to_update, "max_vfolder_count")
        self.max_quota_scope_size.update_dict(to_update, "max_quota_scope_size")
        self.max_vfolder_size.update_dict(to_update, "max_vfolder_size")
        self.max_network_count.update_dict(to_update, "max_network_count")
        return to_update
