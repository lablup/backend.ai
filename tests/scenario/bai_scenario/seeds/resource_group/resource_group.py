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
from bai_scenario.seeds.seeder import Naming, SeedLink, SeedRow


@dataclass(frozen=True)
class SeedResourceGroup(SeedRow[ResourceGroupData]):
    """The scope agents and sessions are created under."""

    name_hint: str = "resource-group"
    scheduler: str = "fifo"

    @override
    def kind(self) -> str:
        return "리소스 그룹"

    @override
    def detail(self) -> str:
        return f"{self.scheduler} 스케줄러를 쓴다"

    @override
    def name(self, naming: Naming) -> str:
        return naming(self.name_hint)

    @override
    def seed(self, name: str) -> ResourceGroupCreator:
        return ResourceGroupCreator(name=name, driver="static", scheduler=self.scheduler)


@dataclass(frozen=True)
class LinkToDomain(SeedLink[DomainData, ResourceGroupData]):
    """Every session of that domain may schedule on the group."""

    @override
    def kind(self) -> str:
        return "의 세션이 쓸 수 있는"

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
class LinkToProject(SeedLink[ProjectData, ResourceGroupData]):
    """Every session of that project may schedule on the group."""

    @override
    def kind(self) -> str:
        return "의 세션이 쓸 수 있는"

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
class LinkToKeypair(SeedLink[UserData, ResourceGroupData]):
    """Only sessions asked for with that key may schedule on the group."""

    access_key: str

    @override
    def kind(self) -> str:
        return "의 키로 요청한 세션만 쓸 수 있는"

    @override
    def scope_id(self, scope: UserData) -> UserID:
        return UserID(scope.id)

    @override
    def target_id(self, target: ResourceGroupData) -> ResourceGroupID:
        return ResourceGroupID(target.id)

    @override
    def seed(self) -> ResourceGroupForKeypairRelationCreator:
        return ResourceGroupForKeypairRelationCreator(access_key=AccessKey(self.access_key))
