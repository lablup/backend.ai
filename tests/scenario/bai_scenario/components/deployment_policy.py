"""What a deployment policy scenario table says besides the call.

A policy is a row the deployment carries, one at most, and is reached through the
deployment's own read permission. A table lays the deployment first, the policy under
it, and a caller in the deployment's project.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, override
from uuid import UUID

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.deployment.response import DeploymentPolicyNode
from ai.backend.common.dto.manager.v2.deployment.types import RollingUpdateStrategySpecInfo
from ai.backend.common.schema.deployment import RollingUpdateSpec
from ai.backend.manager.data.deployment.types import DeploymentInfo, DeploymentPolicyData
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.data.user.types import UserData
from ai.backend.testutils.scenario_steps import Given, Held, Same, SameAs, Verdict
from bai_scenario.components.deployment import (
    APlaceAndACaller,
    LaidPlace,
    lay_a_deployment,
    lay_a_place,
)
from bai_scenario.components.domain import SomeoneOf, WrittenByThisRun
from bai_scenario.seeds.deployment.policy import SeedPolicyOf
from bai_scenario.seeds.project.project import SeedProject
from bai_scenario.seeds.resource_policy.project import SeedProjectPolicy

type Loaded = list[DeploymentPolicyNode | Exception | None]


@dataclass(frozen=True)
class ADeploymentAndItsPolicy:
    """정책이 딸린 배포 하나와, 그것을 부를 사람."""

    place: APlaceAndACaller
    deployment: DeploymentInfo
    policy: DeploymentPolicyData

    @property
    def caller(self) -> UserData:
        return self.place.caller


@dataclass(frozen=True)
class AReaderAndTwoDeployments:
    """정책이 딸린 배포 둘과, 그중 하나만 읽을 수 있는 사람.

    ``policy``는 읽을 수 있는 배포의 정책이다. 읽을 수 없는 배포의 정책은 심기만 하고
    답하지 않는다.
    """

    place: APlaceAndACaller
    readable: DeploymentInfo
    policy: DeploymentPolicyData
    unreadable: DeploymentInfo

    @property
    def caller(self) -> UserData:
        return self.place.caller


@dataclass(frozen=True)
class ADeploymentCarryingAPolicy(Given[Any, ADeploymentAndItsPolicy]):
    """정책이 딸린 배포 하나와, 그 프로젝트 안의 사용자 한 명."""

    granted: tuple[Permission, ...] = ()
    role: UserRole = UserRole.USER

    @override
    def describe(self) -> str:
        if not self.granted:
            return "정책이 딸린 배포 하나와, 아무 배포 권한도 받지 않은 사용자 한 명"
        granted = ", ".join(one.name or str(int(one)) for one in self.granted)
        return f"정책이 딸린 배포 하나와, 배포에 {granted} 권한을 받은 사용자 한 명"

    @override
    async def lay(self, seeding: Any) -> ADeploymentAndItsPolicy:
        place = await lay_a_place(seeding, granted=self.granted, role=self.role)
        deployment = await lay_a_deployment(seeding, place)
        policy = await seeding.adding(SeedPolicyOf(), deployment)
        return ADeploymentAndItsPolicy(
            place=place.made(seeding),
            deployment=seeding.made(deployment),
            policy=seeding.made(policy),
        )


@dataclass(frozen=True)
class PoliciesInTwoProjects(Given[Any, AReaderAndTwoDeployments]):
    """두 프로젝트에 정책이 딸린 배포가 하나씩 있고, 한쪽 프로젝트에만 권한을 받은 사용자."""

    granted: tuple[Permission, ...] = ()

    @override
    def describe(self) -> str:
        granted = ", ".join(one.name or str(int(one)) for one in self.granted)
        return (
            "두 프로젝트에 정책이 딸린 배포가 하나씩 있고, 한쪽 프로젝트에서만 배포에 "
            f"{granted} 권한을 받은 사용자 한 명"
        )

    @override
    async def lay(self, seeding: Any) -> AReaderAndTwoDeployments:
        place = await lay_a_place(seeding, granted=self.granted)
        project_policy = await seeding.once(SeedProjectPolicy())
        other = await seeding.creating_from_two(
            SeedProject(name_hint="other"), place.domain, project_policy
        )
        beside = LaidPlace(
            domain=place.domain,
            project=other,
            resource_group=place.resource_group,
            caller=place.caller,
        )
        readable = await lay_a_deployment(seeding, place, name_hint="readable")
        unreadable = await lay_a_deployment(seeding, beside, name_hint="unreadable")
        policy = await seeding.adding(SeedPolicyOf(), readable)
        await seeding.adding(SeedPolicyOf(), unreadable)
        return AReaderAndTwoDeployments(
            place=place.made(seeding),
            readable=seeding.made(readable),
            policy=seeding.made(policy),
            unreadable=seeding.made(unreadable),
        )


@dataclass(frozen=True)
class AnothersPolicyAndASuperadmin(Given[Any, ADeploymentAndItsPolicy]):
    """다른 사람이 만든, 정책이 딸린 배포 하나와, 아무 권한도 받지 않은 슈퍼관리자."""

    @override
    def describe(self) -> str:
        return (
            "다른 사람이 만든, 정책이 딸린 배포 하나와, 아무 배포 권한도 받지 않은 슈퍼관리자 한 명"
        )

    @override
    async def lay(self, seeding: Any) -> ADeploymentAndItsPolicy:
        place = await lay_a_place(seeding, role=UserRole.SUPERADMIN)
        other = await seeding.within(SomeoneOf(place.domain))
        theirs = LaidPlace(
            domain=place.domain,
            project=place.project,
            resource_group=place.resource_group,
            caller=other,
        )
        deployment = await lay_a_deployment(seeding, theirs, name_hint="theirs")
        policy = await seeding.adding(SeedPolicyOf(), deployment)
        return ADeploymentAndItsPolicy(
            place=place.made(seeding),
            deployment=seeding.made(deployment),
            policy=seeding.made(policy),
        )


@dataclass(frozen=True)
class DeploymentPolicyNodeLook:
    """정책 노드 하나를 통째로 본다. 기대는 심은 정책에서 온다."""

    started: datetime

    def verdicts(
        self,
        node: DeploymentPolicyNode,
        policy: DeploymentPolicyData,
        deployment: DeploymentInfo,
        at: str = "",
    ) -> list[Verdict]:
        """``at``은 답이 목록일 때 원소 자리를 앞에 붙인다."""
        written = WrittenByThisRun(self.started)
        seeded_spec = policy.strategy_spec
        if isinstance(seeded_spec, RollingUpdateSpec):
            strategy_spec: Verdict = Same(
                f"{at}strategy_spec",
                node.strategy_spec,
                RollingUpdateStrategySpecInfo(
                    strategy=policy.strategy,
                    max_surge=seeded_spec.max_surge,
                    max_unavailable=seeded_spec.max_unavailable,
                ),
            )
        else:
            strategy_spec = Same(
                f"{at}strategy_spec", type(seeded_spec).__name__, RollingUpdateSpec.__name__
            )
        return [
            Held(f"{at}id", node.id, SameAs[UUID](policy.id, "심은 정책")),
            Held(f"{at}field_id", node.field_id, SameAs[UUID](policy.id, "심은 정책")),
            Held(
                f"{at}deployment_id", node.deployment_id, SameAs[UUID](deployment.id, "심은 배포")
            ),
            strategy_spec,
            Held(f"{at}created_at", node.created_at, written),
            Held(f"{at}updated_at", node.updated_at, written),
        ]
