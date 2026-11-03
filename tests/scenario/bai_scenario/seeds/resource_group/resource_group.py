"""Write specs for a resource group."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.resource_group import ResourceGroupID
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.types import AccessKey
from ai.backend.manager.data.domain.types import DomainData
from ai.backend.manager.data.project.types import ProjectData
from ai.backend.manager.data.resource_group.types import ResourceGroupData
from ai.backend.manager.data.user.types import UserData
from ai.backend.manager.models.resource_group.creators import (
    ResourceGroupCreator,
    ResourceGroupForDomainRelationCreator,
    ResourceGroupForKeypairRelationCreator,
    ResourceGroupForProjectRelationCreator,
)
from ai.backend.manager.models.resource_group.types import (
    NUM_RETRIES_TO_SKIP_CONFIG_KEY,
    ResourceGroupOpts,
)
from ai.backend.testutils.scenario_steps import Says
from bai_scenario.seeds.seeder import Naming, TestSeedLink, TestSeedRow, joined


@dataclass(frozen=True)
class TestSeedResourceGroup(TestSeedRow[ResourceGroupData]):
    """The scope agents and sessions are created under."""

    name_hint: str = "resource-group"
    scheduler: str = "fifo"
    description: str | None = None
    is_active: bool = True
    is_default: bool = False
    num_retries_to_skip: int | None = None

    @override
    def kind(self) -> str:
        return Says("자원 그룹", english="Resource group")

    @override
    def detail(self) -> str:
        parts = [
            Says(
                f"{self.scheduler} 스케줄러를 사용합니다",
                english=f"uses the {self.scheduler} scheduler",
            )
        ]
        if not self.is_active:
            parts.append(Says("비활성", english="inactive"))
        if self.is_default:
            parts.append(Says("기본 그룹", english="default group"))
        if self.num_retries_to_skip is not None:
            parts.append(
                Says(
                    f"대기 세션 건너뛰기 재시도 횟수 {self.num_retries_to_skip}",
                    english=f"skips a pending session after {self.num_retries_to_skip} retries",
                )
            )
        return joined(parts)

    @override
    def name(self, naming: Naming) -> str:
        return naming(self.name_hint)

    @override
    def seed(self, name: str) -> ResourceGroupCreator:
        return ResourceGroupCreator(
            name=name,
            driver="static",
            scheduler=self.scheduler,
            description=self.description,
            is_active=self.is_active,
            is_default=self.is_default,
            scheduler_opts=(
                None
                if self.num_retries_to_skip is None
                else ResourceGroupOpts(
                    config={NUM_RETRIES_TO_SKIP_CONFIG_KEY: self.num_retries_to_skip}
                )
            ),
        )


@dataclass(frozen=True)
class LinkToDomain(TestSeedLink[DomainData, ResourceGroupData]):
    """Every session of that domain may schedule on the group."""

    @override
    def kind(self) -> str:
        return Says("의 세션이 사용할 수 있는", english="whose sessions can use")

    @override
    def scope_id(self, scope: DomainData) -> DomainID:
        return scope.id

    @override
    def target_id(self, target: ResourceGroupData) -> ResourceGroupID:
        return ResourceGroupID(target.id)

    @override
    def seed(self) -> ResourceGroupForDomainRelationCreator:
        return ResourceGroupForDomainRelationCreator()


@dataclass(frozen=True)
class LinkToProject(TestSeedLink[ProjectData, ResourceGroupData]):
    """Every session of that project may schedule on the group."""

    @override
    def kind(self) -> str:
        return Says("의 세션이 사용할 수 있는", english="whose sessions can use")

    @override
    def scope_id(self, scope: ProjectData) -> ProjectID:
        return ProjectID(scope.id)

    @override
    def target_id(self, target: ResourceGroupData) -> ResourceGroupID:
        return ResourceGroupID(target.id)

    @override
    def seed(self) -> ResourceGroupForProjectRelationCreator:
        return ResourceGroupForProjectRelationCreator()


@dataclass(frozen=True)
class LinkToKeypair(TestSeedLink[UserData, ResourceGroupData]):
    """Only sessions asked for with that key may schedule on the group."""

    access_key: str

    @override
    def kind(self) -> str:
        return Says(
            "의 키로 요청한 세션만 사용할 수 있는",
            english="whose sessions requested with its key can use",
        )

    @override
    def scope_id(self, scope: UserData) -> UserID:
        return UserID(scope.id)

    @override
    def target_id(self, target: ResourceGroupData) -> ResourceGroupID:
        return ResourceGroupID(target.id)

    @override
    def seed(self) -> ResourceGroupForKeypairRelationCreator:
        return ResourceGroupForKeypairRelationCreator(access_key=AccessKey(self.access_key))
