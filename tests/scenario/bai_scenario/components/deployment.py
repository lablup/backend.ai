"""What a deployment scenario table says besides the call.

A deployment is created in a project and reached afterwards through the deployment
itself, so a table needs both: the project a caller may create in, and the row a caller
reads, edits or retires once it is there. The revision, replica, token, policy and rule
rows a deployment owns are not laid here — they are authorized through the deployment
and have tables of their own.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, override
from uuid import UUID

from bai_scenario.components.domain import WAS_HERE, SomeoneOf, WrittenByThisRun
from bai_scenario.seeds.deployment.deployment import SeedDeployment
from bai_scenario.seeds.domain.domain import SeedDomain
from bai_scenario.seeds.project.project import SeedProject
from bai_scenario.seeds.rbac.role import SeedPermission, SeedRole
from bai_scenario.seeds.resource_group.resource_group import SeedResourceGroup
from bai_scenario.seeds.resource_policy.project import SeedProjectPolicy
from bai_scenario.seeds.seeder import Laid, Seeder, SeedNest

from ai.backend.common.data.endpoint.types import ScalingState
from ai.backend.common.data.entity.deployment import DeploymentEntityType
from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.model_deployment.types import (
    DeploymentStrategy,
    ModelDeploymentStatus,
)
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.deployment.response import DeploymentNode
from ai.backend.common.dto.manager.v2.deployment.types import (
    DeploymentPolicyInfo,
    RollingUpdateConfigInfo,
)
from ai.backend.common.schema.deployment import IntOrPercent
from ai.backend.manager.api.adapter_options.deployment.options import deployment_options_to_info
from ai.backend.manager.data.deployment.types import DeploymentInfo
from ai.backend.manager.data.domain.types import DomainData
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.data.project.types import ProjectData
from ai.backend.manager.data.resource_group.types import ResourceGroupData
from ai.backend.manager.data.user.types import UserData
from ai.backend.manager.errors.base.entity import EntityNotFoundError
from ai.backend.testutils.scenario_steps import (
    Answered,
    Condition,
    Given,
    Held,
    Refused,
    Same,
    SameAs,
    Skipped,
    Then,
    Verdict,
)


def _names(granted: Sequence[Permission]) -> str:
    return ", ".join(one.name or str(int(one)) for one in granted)


@dataclass(frozen=True)
class APlaceAndACaller:
    """배포가 놓일 자리와, 그 자리에서 부를 사람."""

    domain: DomainData
    project: ProjectData
    resource_group: ResourceGroupData
    caller: UserData


@dataclass(frozen=True)
class ADeploymentAndACaller:
    """이미 있는 배포 하나와, 그것을 부를 사람."""

    place: APlaceAndACaller
    deployment: DeploymentInfo

    @property
    def caller(self) -> UserData:
        return self.place.caller


@dataclass(frozen=True)
class ManyDeploymentsAndACaller:
    """훑을 배포 여럿과, 훑을 사람. ``named``는 그중 골라낼 하나다."""

    place: APlaceAndACaller
    laid: tuple[DeploymentInfo, ...]
    named: DeploymentInfo

    @property
    def caller(self) -> UserData:
        return self.place.caller


@dataclass(frozen=True)
class LaidPlace:
    """자리를 이루는 행들의 손잡이. 배포를 심는 행이 이것을 딛는다."""

    domain: Laid[DomainData]
    project: Laid[ProjectData]
    resource_group: Laid[ResourceGroupData]
    caller: Laid[UserData]

    def made(self, seeding: Any) -> APlaceAndACaller:
        return APlaceAndACaller(
            domain=seeding.made(self.domain),
            project=seeding.made(self.project),
            resource_group=seeding.made(self.resource_group),
            caller=seeding.made(self.caller),
        )


@dataclass(frozen=True)
class SomeoneOfTheProject(SeedNest[Laid[UserData]]):
    """그 프로젝트 안에서 배포에 대해 정해진 권한만 가진 사용자.

    배포는 프로젝트 스코프에 생기므로 역할도 거기 앉고, 그 역할을 주는 일이 곧 그 사람을
    프로젝트 명부에 올리는 일이 된다. 권한을 하나도 대지 않으면 역할을 만들지 않는다.
    """

    domain: Laid[DomainData]
    project: Laid[ProjectData]
    granted: tuple[Permission, ...] = ()
    role: UserRole = UserRole.USER

    @override
    def kind(self) -> str:
        if not self.granted:
            return "배포 권한을 하나도 받지 않은 사용자 준비"
        return f"배포에 {_names(self.granted)} 권한을 받은 사용자 준비"

    @override
    def lay(self, seed: Seeder) -> Laid[UserData]:
        someone = seed.within(SomeoneOf(self.domain, role=self.role))
        if not self.granted:
            return someone
        role = seed.creating_from(
            SeedRole(lambda p: ProjectID(p.id), name_hint="deployment-user"), self.project
        )
        for one in self.granted:
            seed.adding(SeedPermission(entity_type=DeploymentEntityType(), permission=one), role)
        seed.granting(role, someone, role_id=lambda r: r.id, user_id=lambda u: UserID(u.id))
        return someone


@dataclass(frozen=True)
class SomeoneReadingTheirOwn(SeedNest[Laid[UserData]]):
    """자기 스코프에서 배포를 읽을 수 있는 사용자.

    범위는 사용자 자신이다. 배포는 만든 사람의 스코프에도 생기므로, 거기 앉은 역할이 자기가
    만든 것만 읽게 한다.
    """

    domain: Laid[DomainData]

    @override
    def kind(self) -> str:
        return "자기 스코프에서 배포를 읽을 수 있는 사용자 준비"

    @override
    def lay(self, seed: Seeder) -> Laid[UserData]:
        someone = seed.within(SomeoneOf(self.domain))
        role = seed.creating_from(
            SeedRole(lambda u: UserID(u.id), name_hint="deployment-owner"), someone
        )
        seed.adding(
            SeedPermission(entity_type=DeploymentEntityType(), permission=Permission.READ), role
        )
        seed.granting(role, someone, role_id=lambda r: r.id, user_id=lambda u: UserID(u.id))
        return someone


async def lay_a_place(
    seeding: Any,
    *,
    granted: Sequence[Permission] = (),
    role: UserRole = UserRole.USER,
) -> LaidPlace:
    """배포가 놓일 자리를 세우고, 그 안에 사용자 한 명을 둔다."""
    domain = await seeding.creating(SeedDomain(name_hint="home", description=WAS_HERE))
    policy = await seeding.once(SeedProjectPolicy())
    project = await seeding.creating_from_two(SeedProject(name_hint="team"), domain, policy)
    group = await seeding.creating(SeedResourceGroup())
    caller = await seeding.within(
        SomeoneOfTheProject(domain, project, granted=tuple(granted), role=role)
    )
    return LaidPlace(domain=domain, project=project, resource_group=group, caller=caller)


async def lay_a_deployment(
    seeding: Any,
    place: LaidPlace,
    *,
    name_hint: str = "deployment",
    replica_count: int = 1,
    tag: str | None = None,
    open_to_public: bool = False,
) -> Laid[DeploymentInfo]:
    """그 자리에 배포 하나를 심는다. 소유는 그 자리의 사용자에게 있다."""
    laid: Laid[DeploymentInfo] = await seeding.creating_from_three(
        SeedDeployment(
            name_hint=name_hint,
            replica_count=replica_count,
            tag=tag,
            open_to_public=open_to_public,
        ),
        place.project,
        place.resource_group,
        place.caller,
    )
    return laid


@dataclass(frozen=True)
class APlaceForDeployments(Given[Any, APlaceAndACaller]):
    """배포를 받아줄 프로젝트와 리소스 그룹, 그리고 그 안의 사용자 한 명."""

    granted: tuple[Permission, ...] = ()
    role: UserRole = UserRole.USER

    @override
    def describe(self) -> str:
        if not self.granted:
            return "배포를 놓을 수 있는 프로젝트와, 아무 배포 권한도 받지 않은 사용자 한 명"
        return (
            f"배포를 놓을 수 있는 프로젝트와, 배포에 {_names(self.granted)} "
            "권한을 받은 사용자 한 명"
        )

    @override
    async def lay(self, seeding: Any) -> APlaceAndACaller:
        place = await lay_a_place(seeding, granted=self.granted, role=self.role)
        return place.made(seeding)


@dataclass(frozen=True)
class AProjectGrantedElsewhere(Given[Any, APlaceAndACaller]):
    """만들려는 프로젝트와, 권한이 다른 프로젝트에 걸린 사용자.

    권한이 스코프를 넘지 않는지 보는 자리다. 요청이 가리키는 프로젝트와 역할이 앉은
    프로젝트가 다르다.
    """

    granted: tuple[Permission, ...] = ()

    @override
    def describe(self) -> str:
        return (
            f"배포를 놓을 프로젝트와, 다른 프로젝트에서 배포에 {_names(self.granted)} "
            "권한을 받은 사용자 한 명"
        )

    @override
    async def lay(self, seeding: Any) -> APlaceAndACaller:
        domain = await seeding.creating(SeedDomain(name_hint="home", description=WAS_HERE))
        policy = await seeding.once(SeedProjectPolicy())
        wanted = await seeding.creating_from_two(SeedProject(name_hint="team"), domain, policy)
        other = await seeding.creating_from_two(SeedProject(name_hint="other"), domain, policy)
        group = await seeding.creating(SeedResourceGroup())
        caller = await seeding.within(
            SomeoneOfTheProject(domain, other, granted=tuple(self.granted))
        )
        return APlaceAndACaller(
            domain=seeding.made(domain),
            project=seeding.made(wanted),
            resource_group=seeding.made(group),
            caller=seeding.made(caller),
        )


@dataclass(frozen=True)
class ADeploymentInThatPlace(Given[Any, ADeploymentAndACaller]):
    """이미 있는 배포 하나와, 그 프로젝트 안의 사용자 한 명."""

    granted: tuple[Permission, ...] = ()
    role: UserRole = UserRole.USER
    replica_count: int = 1
    tag: str | None = None
    open_to_public: bool = False

    @override
    def describe(self) -> str:
        if not self.granted:
            return "이미 있는 배포 하나와, 아무 배포 권한도 받지 않은 사용자 한 명"
        return f"이미 있는 배포 하나와, 배포에 {_names(self.granted)} 권한을 받은 사용자 한 명"

    @override
    async def lay(self, seeding: Any) -> ADeploymentAndACaller:
        place = await lay_a_place(seeding, granted=self.granted, role=self.role)
        laid = await lay_a_deployment(
            seeding,
            place,
            replica_count=self.replica_count,
            tag=self.tag,
            open_to_public=self.open_to_public,
        )
        return ADeploymentAndACaller(place=place.made(seeding), deployment=seeding.made(laid))


@dataclass(frozen=True)
class ManyDeploymentsInThatPlace(Given[Any, ManyDeploymentsAndACaller]):
    """배포 여럿과, 그 프로젝트 안의 사용자 한 명."""

    granted: tuple[Permission, ...] = ()
    role: UserRole = UserRole.USER
    besides: int = 2

    @override
    def describe(self) -> str:
        return f"같은 프로젝트의 배포 {self.besides + 1}개와, 그 프로젝트의 사용자 한 명"

    @override
    async def lay(self, seeding: Any) -> ManyDeploymentsAndACaller:
        place = await lay_a_place(seeding, granted=self.granted, role=self.role)
        wanted = await lay_a_deployment(seeding, place, name_hint="wanted")
        others = [
            await lay_a_deployment(seeding, place, name_hint="other") for _ in range(self.besides)
        ]
        return ManyDeploymentsAndACaller(
            place=place.made(seeding),
            laid=tuple(seeding.made(one) for one in [wanted, *others]),
            named=seeding.made(wanted),
        )


@dataclass(frozen=True)
class DeploymentsInTwoProjects(Given[Any, ManyDeploymentsAndACaller]):
    """두 프로젝트에 나뉜 배포들과, 한쪽 프로젝트에만 권한을 받은 사용자.

    답으로 오는 ``laid``는 권한을 받은 프로젝트의 것뿐이다. 다른 프로젝트의 배포는 심기만
    하고 답하지 않으므로, 훑은 결과에 섞여 나오면 그 자리에서 어긋난다.
    """

    granted: tuple[Permission, ...] = ()

    @override
    def describe(self) -> str:
        return (
            f"두 프로젝트에 나뉜 배포들과, 한쪽 프로젝트에서만 배포에 {_names(self.granted)} "
            "권한을 받은 사용자 한 명"
        )

    @override
    async def lay(self, seeding: Any) -> ManyDeploymentsAndACaller:
        place = await lay_a_place(seeding, granted=self.granted)
        policy = await seeding.once(SeedProjectPolicy())
        other = await seeding.creating_from_two(
            SeedProject(name_hint="other"), place.domain, policy
        )
        elsewhere = LaidPlace(
            domain=place.domain,
            project=other,
            resource_group=place.resource_group,
            caller=place.caller,
        )
        wanted = await lay_a_deployment(seeding, place, name_hint="wanted")
        beside = await lay_a_deployment(seeding, place, name_hint="beside")
        await lay_a_deployment(seeding, elsewhere, name_hint="elsewhere")
        return ManyDeploymentsAndACaller(
            place=place.made(seeding),
            laid=(seeding.made(wanted), seeding.made(beside)),
            named=seeding.made(wanted),
        )


@dataclass(frozen=True)
class MineBesideAnothers(Given[Any, ManyDeploymentsAndACaller]):
    """같은 프로젝트에 두 사람이 각자 만든 배포와, 그중 한 사람.

    답으로 오는 ``laid``는 부르는 사람의 것뿐이다. 다른 사람의 배포는 심기만 하고 답하지
    않으므로, 훑은 결과에 섞여 나오면 그 자리에서 어긋난다.
    """

    reads_own: bool = False

    @override
    def describe(self) -> str:
        if self.reads_own:
            return "두 사람이 각자 만든 배포와, 자기 스코프에서 배포 읽기 권한을 받은 그중 한 명"
        return "두 사람이 각자 만든 배포와, 아무 배포 권한도 받지 않은 그중 한 명"

    @override
    async def lay(self, seeding: Any) -> ManyDeploymentsAndACaller:
        domain = await seeding.creating(SeedDomain(name_hint="home", description=WAS_HERE))
        policy = await seeding.once(SeedProjectPolicy())
        project = await seeding.creating_from_two(SeedProject(name_hint="team"), domain, policy)
        group = await seeding.creating(SeedResourceGroup())
        if self.reads_own:
            caller = await seeding.within(SomeoneReadingTheirOwn(domain))
        else:
            caller = await seeding.within(SomeoneOf(domain))
        other = await seeding.within(SomeoneOf(domain))
        mine = LaidPlace(domain=domain, project=project, resource_group=group, caller=caller)
        theirs = LaidPlace(domain=domain, project=project, resource_group=group, caller=other)
        made = await lay_a_deployment(seeding, mine, name_hint="mine")
        await lay_a_deployment(seeding, theirs, name_hint="theirs")
        return ManyDeploymentsAndACaller(
            place=mine.made(seeding),
            laid=(seeding.made(made),),
            named=seeding.made(made),
        )


@dataclass(frozen=True)
class NamedAfterTheMaker(Condition[str]):
    """만든 사람에게서 지어진 이름. 값은 사람마다 달라 레포트에 넣지 않는다."""

    maker: UUID

    @override
    def says(self) -> str:
        return "만든 사람에게서 지어진 이름"

    @override
    def holds(self, got: str) -> bool:
        return got == f"deployment-{self.maker.hex[:8]}"


@dataclass(frozen=True)
class TheNewDeploymentNode(Then[APlaceAndACaller, DeploymentNode]):
    """방금 만든 배포가 통째로 온다. 요청이 정한 것만 여기로 받는다."""

    started: datetime
    named: str | None
    replicas: int
    surge: IntOrPercent
    unavailable: IntOrPercent
    tags: list[str] = field(default_factory=list)
    open_to_public: bool = False

    @override
    def says(self) -> str:
        return "만든 배포 전체가 온다"

    def _name_seen(self, got: str, laid: APlaceAndACaller) -> Verdict:
        if self.named is None:
            return Held("metadata.name", got, NamedAfterTheMaker(laid.caller.id))
        return Same("metadata.name", got, self.named)

    @override
    def look(self, laid: APlaceAndACaller, answered: Answered[DeploymentNode]) -> list[Verdict]:
        node = answered.response
        if node is None:
            return [Refused(EntityNotFoundError, answered.raised)]
        written = WrittenByThisRun(self.started)
        inherited = deployment_options_to_info(laid.resource_group.default_deployment_options)
        return [
            Skipped("id", "데이터베이스가 만든다"),
            Held(
                "metadata.project_id",
                node.metadata.project_id,
                SameAs(str(laid.project.id), "심은 프로젝트"),
            ),
            Same("metadata.domain_name", node.metadata.domain_name, laid.domain.name),
            self._name_seen(node.metadata.name, laid),
            Same("metadata.status", node.metadata.status, ModelDeploymentStatus.PENDING),
            Same("metadata.tags", node.metadata.tags, self.tags),
            Same(
                "metadata.resource_group_name",
                node.metadata.resource_group_name,
                laid.resource_group.name,
            ),
            Held("metadata.created_at", node.metadata.created_at, written),
            Held("metadata.updated_at", node.metadata.updated_at, written),
            Same("network_access.endpoint_url", node.network_access.endpoint_url, None),
            Same(
                "network_access.preferred_domain_name",
                node.network_access.preferred_domain_name,
                None,
            ),
            Same(
                "network_access.open_to_public",
                node.network_access.open_to_public,
                self.open_to_public,
            ),
            Same(
                "replica_state.desired_replica_count",
                node.replica_state.desired_replica_count,
                self.replicas,
            ),
            Same("replica_state.replica_ids", node.replica_state.replica_ids, []),
            Same(
                "default_deployment_strategy.type",
                node.default_deployment_strategy.type,
                DeploymentStrategy.ROLLING,
            ),
            Held("created_user_id", node.created_user_id, SameAs(laid.caller.id, "만든 사람")),
            Held("options", node.options, SameAs(inherited, "리소스 그룹의 기본값")),
            Same("scaling_state", node.scaling_state, ScalingState.STABLE),
            Same("current_revision_id", node.current_revision_id, None),
            Same("deploying_revision_id", node.deploying_revision_id, None),
            Same(
                "policy",
                node.policy,
                DeploymentPolicyInfo(
                    strategy=DeploymentStrategy.ROLLING,
                    rolling_update=RollingUpdateConfigInfo(
                        max_surge=self.surge,
                        max_unavailable=self.unavailable,
                    ),
                    blue_green=None,
                ),
            ),
        ]


@dataclass(frozen=True)
class TheDeploymentNode(Then[ADeploymentAndACaller, DeploymentNode]):
    """심은 배포가 통째로 온다. 값은 심은 것에서 읽는다.

    바꾸는 요청이 이것을 쓸 때는 바뀌어야 하는 자리만 인자로 받는다. 나머지가 조용히 함께
    움직이면 그 자리에서 어긋난다.
    """

    started: datetime
    named: str | None = None
    replicas: int | None = None
    tags: list[str] = field(default_factory=list)
    open_to_public: bool | None = None

    @override
    def says(self) -> str:
        return "심은 배포 전체가 온다"

    @override
    def look(
        self, laid: ADeploymentAndACaller, answered: Answered[DeploymentNode]
    ) -> list[Verdict]:
        node = answered.response
        if node is None:
            return [Refused(EntityNotFoundError, answered.raised)]
        seeded = laid.deployment
        place = laid.place
        written = WrittenByThisRun(self.started)
        wanted_replicas = (
            self.replicas if self.replicas is not None else seeded.replica.replica_count
        )
        wanted_public = (
            self.open_to_public
            if self.open_to_public is not None
            else seeded.network.open_to_public
        )
        return [
            Held("id", node.id, SameAs(seeded.id, "심은 배포")),
            Held(
                "metadata.project_id",
                node.metadata.project_id,
                SameAs(str(place.project.id), "심은 프로젝트"),
            ),
            Same("metadata.domain_name", node.metadata.domain_name, place.domain.name),
            Same(
                "metadata.name",
                node.metadata.name,
                self.named if self.named is not None else seeded.metadata.name,
            ),
            Same("metadata.status", node.metadata.status, ModelDeploymentStatus.PENDING),
            Same("metadata.tags", node.metadata.tags, self.tags),
            Same(
                "metadata.resource_group_name",
                node.metadata.resource_group_name,
                place.resource_group.name,
            ),
            Held("metadata.created_at", node.metadata.created_at, written),
            Held("metadata.updated_at", node.metadata.updated_at, written),
            Same("network_access.endpoint_url", node.network_access.endpoint_url, None),
            Same(
                "network_access.preferred_domain_name",
                node.network_access.preferred_domain_name,
                None,
            ),
            Same(
                "network_access.open_to_public", node.network_access.open_to_public, wanted_public
            ),
            Same(
                "replica_state.desired_replica_count",
                node.replica_state.desired_replica_count,
                wanted_replicas,
            ),
            Same("replica_state.replica_ids", node.replica_state.replica_ids, []),
            Same(
                "default_deployment_strategy.type",
                node.default_deployment_strategy.type,
                DeploymentStrategy.ROLLING,
            ),
            Held(
                "created_user_id",
                node.created_user_id,
                SameAs(place.caller.id, "심은 배포를 가진 사람"),
            ),
            Held(
                "options",
                node.options,
                SameAs(deployment_options_to_info(seeded.options), "심은 배포의 옵션"),
            ),
            Same("scaling_state", node.scaling_state, ScalingState.STABLE),
            Same("current_revision_id", node.current_revision_id, None),
            Same("deploying_revision_id", node.deploying_revision_id, None),
            Same("policy", node.policy, None),
        ]
