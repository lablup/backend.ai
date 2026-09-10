"""Write specs for the resource policy a project is held to."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override
from uuid import UUID

from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.data.resource.types import ProjectResourcePolicyData
from ai.backend.manager.models.project.creators import ProjectCreator
from ai.backend.manager.models.resource_policy.creators import ProjectResourcePolicyCreator
from bai_scenario.seeds.seeder import Naming, SeedRow


@dataclass(frozen=True)
class SeedProjectPolicy(SeedRow[ProjectResourcePolicyData]):
    """프로젝트가 무엇을 허용받는지.

    이름은 시더가 아니라 매니저가 정한다. 사용자를 만들면 개인 프로젝트가 딸려 만들어지고,
    그 프로젝트가 이름으로 이 정책을 찾는다. 그 이름을 여기 다시 적지 않고 매니저에게 묻는다.
    """

    max_vfolder_count: int = 10
    max_quota_scope_size: int = -1
    max_network_count: int = 3

    @override
    def kind(self) -> str:
        return "프로젝트 정책"

    @override
    def detail(self) -> str:
        return "사용자를 만들 때 딸려 만들어지는 개인 프로젝트가 이 이름으로 찾는다"

    @override
    def name(self, naming: Naming) -> str:
        blank = UUID(int=0)
        wanted = ProjectCreator.personal(
            name="",
            domain_id=DomainID(blank),
            domain_name="",
            user_id=UserID(blank),
        ).resource_policy
        if wanted is None:
            raise ValueError("the personal project no longer names a resource policy")
        return wanted

    @override
    def seed(self, name: str) -> ProjectResourcePolicyCreator:
        return ProjectResourcePolicyCreator(
            name=name,
            max_vfolder_count=self.max_vfolder_count,
            max_quota_scope_size=self.max_quota_scope_size,
            max_network_count=self.max_network_count,
        )
