"""배포 만들기 — 누가 만들 수 있고, 만들어진 것이 무엇을 들고 있는가.

이름이 공백뿐인 요청과 복제 수가 음수인 요청은 여기 없다. 요청 타입이 이미 막으므로 어댑터가
보장하는 것이 아니다.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, override

import pytest
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.deployment import (
    APlaceAndACaller,
    APlaceForDeployments,
    AProjectGrantedElsewhere,
    TheNewDeploymentNode,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario

from ai.backend.common.data.entity.resource_group import ResourceGroupName
from ai.backend.common.data.model_deployment.types import DeploymentStrategy
from ai.backend.common.dto.manager.v2.deployment.request import (
    CreateDeploymentInput,
    DeploymentStrategyInput,
    ModelDeploymentMetadataInput,
    ModelDeploymentNetworkAccessInput,
    RollingUpdateConfigInput,
)
from ai.backend.common.dto.manager.v2.deployment.response import DeploymentNode
from ai.backend.common.schema.deployment import IntOrPercent
from ai.backend.manager.api.adapters.deployment.adapter import DeploymentAdapter
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Configured,
    Given,
    Scenario,
    Then,
    When,
)

MADE = "serving"
ENFORCEMENT = "manager.rbac.enforcement_enabled"
SURGE = IntOrPercent(count=2)
UNAVAILABLE = IntOrPercent(count=0)

type CreatingStep = Scenario[SeedingSession, APlaceAndACaller, DeploymentAdapter, DeploymentNode]


@dataclass(frozen=True)
class Creating(When[APlaceAndACaller, DeploymentAdapter, DeploymentNode]):
    """배포 하나를 만든다. 이름을 대지 않으면 서버가 짓는다."""

    named: str | None = MADE
    replicas: int = 1

    @override
    def operation(self) -> str:
        return "create"

    @override
    def describe(self, laid: APlaceAndACaller) -> str:
        called = self.named if self.named is not None else "이름 없이"
        return f"{laid.caller.username}이 {laid.project.name}에 {called} 배포를 만듦"

    @override
    async def call(self, adapter: DeploymentAdapter, laid: APlaceAndACaller) -> DeploymentNode:
        with ActingAs(laid.caller):
            payload = await adapter.create(
                CreateDeploymentInput(
                    metadata=ModelDeploymentMetadataInput(
                        project_id=laid.project.id,
                        domain_name=laid.domain.name,
                        resource_group_name=ResourceGroupName(laid.resource_group.name),
                        name=self.named,
                    ),
                    network_access=ModelDeploymentNetworkAccessInput(),
                    default_deployment_strategy=DeploymentStrategyInput(
                        type=DeploymentStrategy.ROLLING,
                        rolling_update=RollingUpdateConfigInput(
                            max_surge=SURGE, max_unavailable=UNAVAILABLE
                        ),
                    ),
                    replica_count=self.replicas,
                ),
                laid.caller.id,
            )
        return payload.deployment


@dataclass(frozen=True)
class TheWholeNodeComesBack(
    Scenario[SeedingSession, APlaceAndACaller, DeploymentAdapter, DeploymentNode]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-user-granted-create-in-a-project-makes-a-deployment-there"

    @override
    def describe(self) -> str:
        return (
            "프로젝트에서 배포 생성 권한을 받은 사용자가 배포를 만들면, "
            "그 프로젝트에 속하고 부른 사람이 소유하는 배포가 리비전 없이 만들어진다"
        )

    @override
    def given(self) -> Given[SeedingSession, APlaceAndACaller]:
        return APlaceForDeployments(granted=(Permission.CREATE,))

    @override
    def when(self) -> When[APlaceAndACaller, DeploymentAdapter, DeploymentNode]:
        return Creating(replicas=2)

    @override
    def then(self) -> Then[APlaceAndACaller, DeploymentNode]:
        return TheNewDeploymentNode(
            started=self.started,
            named=MADE,
            replicas=2,
            surge=SURGE,
            unavailable=UNAVAILABLE,
        )


@dataclass(frozen=True)
class ANamelessOneIsNamedAfterItsMaker(
    Scenario[SeedingSession, APlaceAndACaller, DeploymentAdapter, DeploymentNode]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-deployment-made-without-a-name-is-named-after-its-maker"

    @override
    def describe(self) -> str:
        return "이름을 대지 않고 배포를 만들면, 만든 사람에게서 이름이 지어진다"

    @override
    def given(self) -> Given[SeedingSession, APlaceAndACaller]:
        return APlaceForDeployments(granted=(Permission.CREATE,))

    @override
    def when(self) -> When[APlaceAndACaller, DeploymentAdapter, DeploymentNode]:
        return Creating(named=None)

    @override
    def then(self) -> Then[APlaceAndACaller, DeploymentNode]:
        return TheNewDeploymentNode(
            started=self.started,
            named=None,
            replicas=1,
            surge=SURGE,
            unavailable=UNAVAILABLE,
        )


@dataclass(frozen=True)
class AUserGrantedNothingMayNotCreate(
    Scenario[SeedingSession, APlaceAndACaller, DeploymentAdapter, DeploymentNode]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-create-a-deployment"

    @override
    def describe(self) -> str:
        return "아무 배포 권한도 받지 않은 사용자가 배포를 만들면, 권한 부족으로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, APlaceAndACaller]:
        return APlaceForDeployments()

    @override
    def when(self) -> When[APlaceAndACaller, DeploymentAdapter, DeploymentNode]:
        return Creating()

    @override
    def then(self) -> Then[APlaceAndACaller, DeploymentNode]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class AGrantInAnotherProjectDoesNotReachHere(
    Scenario[SeedingSession, APlaceAndACaller, DeploymentAdapter, DeploymentNode]
):
    @override
    def summary(self) -> str:
        return "a-create-grant-in-another-project-does-not-reach-this-one"

    @override
    def describe(self) -> str:
        return (
            "생성 권한을 받은 프로젝트가 아닌 다른 프로젝트에 배포를 만들면, 권한 부족으로 거부된다"
        )

    @override
    def given(self) -> Given[SeedingSession, APlaceAndACaller]:
        return AProjectGrantedElsewhere(granted=(Permission.CREATE,))

    @override
    def when(self) -> When[APlaceAndACaller, DeploymentAdapter, DeploymentNode]:
        return Creating()

    @override
    def then(self) -> Then[APlaceAndACaller, DeploymentNode]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class EnforcementOffLetsAnyoneCreate(
    Scenario[SeedingSession, APlaceAndACaller, DeploymentAdapter, DeploymentNode], Configured
):
    started: datetime

    @override
    def summary(self) -> str:
        return "turning-enforcement-off-lets-a-user-create-a-deployment"

    @override
    def describe(self) -> str:
        return (
            "엔티티 권한 집행을 끄면 아무 권한도 받지 않은 사용자도 배포를 만든다. "
            "이 문은 역할이 아니라 권한 그래프가 지키기 때문이다"
        )

    @override
    def config(self) -> Mapping[str, Any]:
        return {ENFORCEMENT: False}

    @override
    def given(self) -> Given[SeedingSession, APlaceAndACaller]:
        return APlaceForDeployments()

    @override
    def when(self) -> When[APlaceAndACaller, DeploymentAdapter, DeploymentNode]:
        return Creating()

    @override
    def then(self) -> Then[APlaceAndACaller, DeploymentNode]:
        return TheNewDeploymentNode(
            started=self.started,
            named=MADE,
            replicas=1,
            surge=SURGE,
            unavailable=UNAVAILABLE,
        )


SCENARIOS: list[CreatingStep] = [
    TheWholeNodeComesBack(started=datetime.now(UTC)),
    ANamelessOneIsNamedAfterItsMaker(started=datetime.now(UTC)),
    AUserGrantedNothingMayNotCreate(),
    AGrantInAnotherProjectDoesNotReachHere(),
    EnforcementOffLetsAnyoneCreate(started=datetime.now(UTC)),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_creating(
    scenario: CreatingStep, adapter: DeploymentAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
