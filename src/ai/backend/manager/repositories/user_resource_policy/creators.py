from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional, override

from ai.backend.manager.repositories.base.creator import CreatorSpec

if TYPE_CHECKING:
    from ai.backend.manager.models.resource_policy import UserResourcePolicyRow


@dataclass
class UserResourcePolicyCreatorSpec(CreatorSpec["UserResourcePolicyRow"]):
    """CreatorSpec for user resource policy."""

    name: str
    max_vfolder_count: Optional[int]
    max_quota_scope_size: Optional[int]
    max_session_count_per_model_session: Optional[int]
    max_customized_image_count: Optional[int]

    @override
    def build_row(self) -> UserResourcePolicyRow:
        from ai.backend.manager.models.resource_policy import UserResourcePolicyRow

        return UserResourcePolicyRow(
            name=self.name,
            max_vfolder_count=self.max_vfolder_count,
            max_quota_scope_size=self.max_quota_scope_size,
            max_session_count_per_model_session=self.max_session_count_per_model_session,
            max_customized_image_count=self.max_customized_image_count,
        )
