"""DataUpdater implementations for the user resource policy repository."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any, override

from ai.backend.manager.data.resource.types import UserResourcePolicyData
from ai.backend.manager.models.resource_policy.row import UserResourcePolicyRow
from ai.backend.manager.models.specs.types import IntegrityErrorCheck
from ai.backend.manager.models.specs.updater import DataUpdater
from ai.backend.manager.types import OptionalState, TriState


@dataclass
class UserResourcePolicyUpdater(DataUpdater[UserResourcePolicyRow, UserResourcePolicyData]):
    name: str
    max_vfolder_count: OptionalState[int] = field(default_factory=OptionalState[int].nop)
    max_quota_scope_size: OptionalState[int] = field(default_factory=OptionalState[int].nop)
    max_session_count_per_model_session: OptionalState[int] = field(
        default_factory=OptionalState[int].nop
    )
    max_customized_image_count: OptionalState[int] = field(default_factory=OptionalState[int].nop)
    max_concurrent_logins: TriState[int] = field(default_factory=TriState[int].nop)

    @property
    @override
    def row_class(self) -> type[UserResourcePolicyRow]:
        return UserResourcePolicyRow

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
        self.max_session_count_per_model_session.update_dict(
            to_update, "max_session_count_per_model_session"
        )
        self.max_customized_image_count.update_dict(to_update, "max_customized_image_count")
        self.max_concurrent_logins.update_dict(to_update, "max_concurrent_logins")
        return to_update

    @override
    def to_data(self, row: UserResourcePolicyRow) -> UserResourcePolicyData:
        return row.to_dataclass()
