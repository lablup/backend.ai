"""Write specs for the resource policy a user is held to."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

from bai_scenario.seeds.seeder import Naming, SeedRow

from ai.backend.manager.data.resource.types import UserResourcePolicyData
from ai.backend.manager.models.resource_policy.creators import UserResourcePolicyCreator


@dataclass(frozen=True)
class SeedUserPolicy(SeedRow[UserResourcePolicyData]):
    """What a user is allowed, as a row of its own rather than a name borrowed from
    somewhere else."""

    name_hint: str = "user-policy"
    max_vfolder_count: int = 10
    max_quota_scope_size: int = -1
    max_session_count_per_model_session: int = 10
    max_customized_image_count: int = 3
    max_concurrent_logins: int | None = None

    @override
    def kind(self) -> str:
        return "사용자 정책"

    @override
    def detail(self) -> str:
        allows = [f"사용자 한 명당 폴더 {self.max_vfolder_count}개까지"]
        if self.max_concurrent_logins is not None:
            allows.append(f"동시 로그인 {self.max_concurrent_logins}개까지")
        return ", ".join(allows)

    @override
    def name(self, naming: Naming) -> str:
        return naming(self.name_hint)

    @override
    def seed(self, name: str) -> UserResourcePolicyCreator:
        return UserResourcePolicyCreator(
            name=name,
            max_vfolder_count=self.max_vfolder_count,
            max_quota_scope_size=self.max_quota_scope_size,
            max_session_count_per_model_session=self.max_session_count_per_model_session,
            max_customized_image_count=self.max_customized_image_count,
            max_concurrent_logins=self.max_concurrent_logins,
        )
