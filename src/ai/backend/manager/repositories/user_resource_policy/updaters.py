from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from typing_extensions import override

from ai.backend.manager.models.resource_policy import UserResourcePolicyRow
from ai.backend.manager.repositories.base.updater import UpdaterSpec
from ai.backend.manager.types import OptionalState


@dataclass
class UserResourcePolicyUpdaterSpec(UpdaterSpec[UserResourcePolicyRow]):
    """UpdaterSpec for user resource policy updates."""

    max_vfolder_count: OptionalState[int] = field(default_factory=OptionalState.nop)
    max_quota_scope_size: OptionalState[int] = field(default_factory=OptionalState.nop)
    max_session_count_per_model_session: OptionalState[int] = field(
        default_factory=OptionalState.nop
    )
    max_customized_image_count: OptionalState[int] = field(default_factory=OptionalState.nop)

    @property
    @override
    def row_class(self) -> type[UserResourcePolicyRow]:
        return UserResourcePolicyRow

    @override
    def build_values(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.max_vfolder_count.update_dict(to_update, "max_vfolder_count")
        self.max_quota_scope_size.update_dict(to_update, "max_quota_scope_size")
        self.max_session_count_per_model_session.update_dict(
            to_update, "max_session_count_per_model_session"
        )
        self.max_customized_image_count.update_dict(to_update, "max_customized_image_count")
        return to_update
