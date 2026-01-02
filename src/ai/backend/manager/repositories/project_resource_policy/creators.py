from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional, override

from ai.backend.manager.repositories.base.creator import CreatorSpec

if TYPE_CHECKING:
    from ai.backend.manager.models.resource_policy import ProjectResourcePolicyRow


@dataclass
class ProjectResourcePolicyCreatorSpec(CreatorSpec["ProjectResourcePolicyRow"]):
    """CreatorSpec for project resource policy."""

    name: str
    max_vfolder_count: Optional[int]
    max_quota_scope_size: Optional[int]
    max_network_count: Optional[int]

    @override
    def build_row(self) -> ProjectResourcePolicyRow:
        from ai.backend.manager.models.resource_policy import ProjectResourcePolicyRow

        return ProjectResourcePolicyRow(
            name=self.name,
            max_vfolder_count=self.max_vfolder_count,
            max_quota_scope_size=self.max_quota_scope_size,
            max_network_count=self.max_network_count,
        )
