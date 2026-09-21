"""배포 정책 여럿을 배포 id로 한 번에 읽기 — 자리마다 무엇이 오는가.

정책은 배포가 소유하는 행이라 그 배포의 읽기 권한으로 열린다. 자리마다 그 배포 읽기와 같은
기준으로 따로 판정하고, 호출 전체가 거부되지는 않는다.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, override
from uuid import uuid4

import pytest

from ai.backend.common.data.entity.deployment import DeploymentID
from ai.backend.common.dto.manager.v2.deployment.response import DeploymentPolicyNode
from ai.backend.manager.api.adapters.deployment.adapter import DeploymentAdapter
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Refused,
    Same,
    Scenario,
    Then,
    Verdict,
    When,
)
from bai_scenario.components.answers import MissingResponse
from bai_scenario.components.deployment import (
    ADeploymentAndACaller,
    ADeploymentInThatPlace,
    APlaceAndACaller,
    APlaceForDeployments,
)
from bai_scenario.components.deployment_policy import (
    ADeploymentAndItsPolicy,
    ADeploymentCarryingAPolicy,
    AnothersPolicyAndASuperadmin,
    AReaderAndTwoDeployments,
    DeploymentPolicyNodeLook,
    Loaded,
    PoliciesInTwoProjects,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario

type LoadStep = Scenario[SeedingSession, Any, DeploymentAdapter, Loaded]


@dataclass(frozen=True)
class LoadingThePolicyByDeploymentId(When[ADeploymentAndItsPolicy, DeploymentAdapter, Loaded]):
    """배포 id 하나만 준다."""

    @override
    def operation(self) -> str:
        return "batch_load_policies_by_endpoint_ids"

    @override
    def describe(self, laid: ADeploymentAndItsPolicy) -> str:
        return f"{laid.caller.username}이 {laid.deployment.metadata.name}의 id로 정책을 일괄 읽음"

    @override
    async def call(self, adapter: DeploymentAdapter, laid: ADeploymentAndItsPolicy) -> Loaded:
        with ActingAs(laid.caller):
            return await adapter.batch_load_policies_by_endpoint_ids([
                DeploymentID(laid.deployment.id)
            ])


@dataclass(frozen=True)
class LoadingReadableUnreadableAndMissing(
    When[AReaderAndTwoDeployments, DeploymentAdapter, Loaded]
):
    """읽을 수 있는 배포, 읽을 수 없는 배포, 없는 id 순으로 한 번에 읽는다."""

    @override
    def operation(self) -> str:
        return "batch_load_policies_by_endpoint_ids"

    @override
    def describe(self, laid: AReaderAndTwoDeployments) -> str:
        return (
            f"{laid.caller.username}이 {laid.readable.metadata.name}, "
            f"{laid.unreadable.metadata.name}, 없는 id 순으로 정책을 일괄 읽음"
        )

    @override
    async def call(self, adapter: DeploymentAdapter, laid: AReaderAndTwoDeployments) -> Loaded:
        with ActingAs(laid.caller):
            return await adapter.batch_load_policies_by_endpoint_ids([
                DeploymentID(laid.readable.id),
                DeploymentID(laid.unreadable.id),
                DeploymentID(uuid4()),
            ])


@dataclass(frozen=True)
class LoadingTheDeploymentIdAlone(When[ADeploymentAndACaller, DeploymentAdapter, Loaded]):
    """정책이 딸리지 않은 배포의 id 하나만 준다."""

    @override
    def operation(self) -> str:
        return "batch_load_policies_by_endpoint_ids"

    @override
    def describe(self, laid: ADeploymentAndACaller) -> str:
        return f"{laid.caller.username}이 {laid.deployment.metadata.name}의 id로 정책을 일괄 읽음"

    @override
    async def call(self, adapter: DeploymentAdapter, laid: ADeploymentAndACaller) -> Loaded:
        with ActingAs(laid.caller):
            return await adapter.batch_load_policies_by_endpoint_ids([
                DeploymentID(laid.deployment.id)
            ])


@dataclass(frozen=True)
class LoadingThePolicyAndMissing(When[ADeploymentAndItsPolicy, DeploymentAdapter, Loaded]):
    """있는 배포와 없는 id를 한 번에 읽는다."""

    @override
    def operation(self) -> str:
        return "batch_load_policies_by_endpoint_ids"

    @override
    def describe(self, laid: ADeploymentAndItsPolicy) -> str:
        return (
            f"{laid.caller.username}이 {laid.deployment.metadata.name}의 id와 없는 id로 "
            "정책을 일괄 읽음"
        )

    @override
    async def call(self, adapter: DeploymentAdapter, laid: ADeploymentAndItsPolicy) -> Loaded:
        with ActingAs(laid.caller):
            return await adapter.batch_load_policies_by_endpoint_ids([
                DeploymentID(laid.deployment.id),
                DeploymentID(uuid4()),
            ])


@dataclass(frozen=True)
class LoadingNothing(When[APlaceAndACaller, DeploymentAdapter, Loaded]):
    """빈 id 목록으로 읽는다."""

    @override
    def operation(self) -> str:
        return "batch_load_policies_by_endpoint_ids"

    @override
    def describe(self, laid: APlaceAndACaller) -> str:
        return f"{laid.caller.username}이 빈 목록으로 정책을 일괄 읽음"

    @override
    async def call(self, adapter: DeploymentAdapter, laid: APlaceAndACaller) -> Loaded:
        with ActingAs(laid.caller):
            return await adapter.batch_load_policies_by_endpoint_ids([])


@dataclass(frozen=True)
class ThePolicyAlone(Then[ADeploymentAndItsPolicy, Loaded]):
    """심은 정책 하나가 통째로 온다."""

    started: datetime

    @override
    def says(self) -> str:
        return "심은 정책 하나가 통째로 온다"

    @override
    def look(self, laid: ADeploymentAndItsPolicy, answered: Answered[Loaded]) -> list[Verdict]:
        loaded = answered.response
        if loaded is None:
            return [MissingResponse(answered.raised)]
        seen: list[Verdict] = [Same("length", len(loaded), 1)]
        first = loaded[0] if loaded else None
        if isinstance(first, DeploymentPolicyNode):
            seen.extend(
                DeploymentPolicyNodeLook(self.started).verdicts(
                    first, laid.policy, laid.deployment, at="[0]."
                )
            )
        else:
            seen.append(Same("[0]", type(first).__name__, DeploymentPolicyNode.__name__))
        return seen


@dataclass(frozen=True)
class ARefusalAlone(Then[ADeploymentAndItsPolicy, Loaded]):
    """호출은 성공하고, 그 자리는 권한 부족으로 거부된다."""

    @override
    def says(self) -> str:
        return "그 자리는 권한 부족으로 거부된다"

    @override
    def look(self, laid: ADeploymentAndItsPolicy, answered: Answered[Loaded]) -> list[Verdict]:
        loaded = answered.response
        if loaded is None:
            return [MissingResponse(answered.raised)]
        first = loaded[0] if loaded else None
        return [
            Same("length", len(loaded), 1),
            Refused(NotEnoughPermission, first if isinstance(first, Exception) else None),
        ]


@dataclass(frozen=True)
class AnEmptySlotAlone(Then[ADeploymentAndACaller, Loaded]):
    """호출은 성공하고, 그 자리는 빈 값으로 온다."""

    @override
    def says(self) -> str:
        return "그 자리는 빈 값으로 온다"

    @override
    def look(self, laid: ADeploymentAndACaller, answered: Answered[Loaded]) -> list[Verdict]:
        loaded = answered.response
        if loaded is None:
            return [MissingResponse(answered.raised)]
        return [Same("loaded", loaded, [None])]


@dataclass(frozen=True)
class EachElementInOrder(Then[AReaderAndTwoDeployments, Loaded]):
    """입력 순서대로 자리마다 정책 또는 거부가 온다."""

    started: datetime

    @override
    def says(self) -> str:
        return "입력 순서대로 자리마다 정책 또는 거부가 온다"

    @override
    def look(self, laid: AReaderAndTwoDeployments, answered: Answered[Loaded]) -> list[Verdict]:
        loaded = answered.response
        if loaded is None:
            return [MissingResponse(answered.raised)]
        seen: list[Verdict] = [Same("length", len(loaded), 3)]
        if len(loaded) != 3:
            return seen
        first, second, third = loaded
        if isinstance(first, DeploymentPolicyNode):
            seen.extend(
                DeploymentPolicyNodeLook(self.started).verdicts(
                    first, laid.policy, laid.readable, at="[0]."
                )
            )
        else:
            seen.append(Same("[0]", type(first).__name__, DeploymentPolicyNode.__name__))
        seen.append(Refused(NotEnoughPermission, second if isinstance(second, Exception) else None))
        seen.append(Refused(NotEnoughPermission, third if isinstance(third, Exception) else None))
        return seen


@dataclass(frozen=True)
class ThePolicyThenNothing(Then[ADeploymentAndItsPolicy, Loaded]):
    """있는 배포의 정책은 노드로, 없는 id 자리는 빈 값으로 온다."""

    started: datetime

    @override
    def says(self) -> str:
        return "있는 배포의 정책은 노드로, 없는 id 자리는 빈 값으로 온다"

    @override
    def look(self, laid: ADeploymentAndItsPolicy, answered: Answered[Loaded]) -> list[Verdict]:
        loaded = answered.response
        if loaded is None:
            return [MissingResponse(answered.raised)]
        seen: list[Verdict] = [Same("length", len(loaded), 2)]
        if len(loaded) != 2:
            return seen
        first, second = loaded
        if isinstance(first, DeploymentPolicyNode):
            seen.extend(
                DeploymentPolicyNodeLook(self.started).verdicts(
                    first, laid.policy, laid.deployment, at="[0]."
                )
            )
        else:
            seen.append(Same("[0]", type(first).__name__, DeploymentPolicyNode.__name__))
        seen.append(Same("[1]", second, None))
        return seen


@dataclass(frozen=True)
class AnEmptyList(Then[APlaceAndACaller, Loaded]):
    """빈 목록이 온다."""

    @override
    def says(self) -> str:
        return "빈 목록이 온다"

    @override
    def look(self, laid: APlaceAndACaller, answered: Answered[Loaded]) -> list[Verdict]:
        loaded = answered.response
        if loaded is None:
            return [MissingResponse(answered.raised)]
        return [Same("loaded", loaded, [])]


@dataclass(frozen=True)
class AUserGrantedReadLoadsThePolicyOfTheirDeployment(
    Scenario[SeedingSession, ADeploymentAndItsPolicy, DeploymentAdapter, Loaded]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-user-granted-read-loads-the-policy-of-their-deployment"

    @override
    def describe(self) -> str:
        return (
            "배포 읽기 권한을 받은 사용자가 정책이 딸린 자기 배포의 id로 정책을 일괄 읽으면, "
            "그 정책이 온다"
        )

    @override
    def given(self) -> Given[SeedingSession, ADeploymentAndItsPolicy]:
        return ADeploymentCarryingAPolicy(granted=(Permission.READ,))

    @override
    def when(self) -> When[ADeploymentAndItsPolicy, DeploymentAdapter, Loaded]:
        return LoadingThePolicyByDeploymentId()

    @override
    def then(self) -> Then[ADeploymentAndItsPolicy, Loaded]:
        return ThePolicyAlone(started=self.started)


@dataclass(frozen=True)
class AUserGrantedNothingGetsARefusalInPlaceOfThePolicy(
    Scenario[SeedingSession, ADeploymentAndItsPolicy, DeploymentAdapter, Loaded]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-gets-a-refusal-in-place-of-the-policy"

    @override
    def describe(self) -> str:
        return (
            "아무 배포 권한도 받지 않은 사용자가 정책이 딸린 자기 배포의 id로 정책을 일괄 읽으면, "
            "호출은 성공하되 그 자리는 권한 부족으로 거부된다"
        )

    @override
    def given(self) -> Given[SeedingSession, ADeploymentAndItsPolicy]:
        return ADeploymentCarryingAPolicy()

    @override
    def when(self) -> When[ADeploymentAndItsPolicy, DeploymentAdapter, Loaded]:
        return LoadingThePolicyByDeploymentId()

    @override
    def then(self) -> Then[ADeploymentAndItsPolicy, Loaded]:
        return ARefusalAlone()


@dataclass(frozen=True)
class ADeploymentCarryingNoPolicyAnswersAnEmptySlot(
    Scenario[SeedingSession, ADeploymentAndACaller, DeploymentAdapter, Loaded]
):
    @override
    def summary(self) -> str:
        return "a-deployment-carrying-no-policy-answers-an-empty-slot"

    @override
    def describe(self) -> str:
        return (
            "배포 읽기 권한을 받은 사용자가 정책이 딸리지 않은 자기 배포의 id로 정책을 일괄 "
            "읽으면, 호출은 성공하되 그 자리는 빈 값으로 온다"
        )

    @override
    def given(self) -> Given[SeedingSession, ADeploymentAndACaller]:
        return ADeploymentInThatPlace(granted=(Permission.READ,))

    @override
    def when(self) -> When[ADeploymentAndACaller, DeploymentAdapter, Loaded]:
        return LoadingTheDeploymentIdAlone()

    @override
    def then(self) -> Then[ADeploymentAndACaller, Loaded]:
        return AnEmptySlotAlone()


@dataclass(frozen=True)
class ABatchLoadAnswersEachElementInOrder(
    Scenario[SeedingSession, AReaderAndTwoDeployments, DeploymentAdapter, Loaded]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-batch-load-answers-a-policy-or-a-refusal-for-each-deployment-in-order"

    @override
    def describe(self) -> str:
        return (
            "한 프로젝트에서만 배포 읽기 권한을 받은 사용자가 자기 프로젝트의 배포, 다른 "
            "프로젝트의 배포, 없는 id로 정책을 한 번에 읽으면, 입력 순서대로 그 정책, 거부, "
            "거부가 온다"
        )

    @override
    def given(self) -> Given[SeedingSession, AReaderAndTwoDeployments]:
        return PoliciesInTwoProjects(granted=(Permission.READ,))

    @override
    def when(self) -> When[AReaderAndTwoDeployments, DeploymentAdapter, Loaded]:
        return LoadingReadableUnreadableAndMissing()

    @override
    def then(self) -> Then[AReaderAndTwoDeployments, Loaded]:
        return EachElementInOrder(started=self.started)


@dataclass(frozen=True)
class TheSuperadminBatchLoadLeavesAMissingIdEmpty(
    Scenario[SeedingSession, ADeploymentAndItsPolicy, DeploymentAdapter, Loaded]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "the-superadmin-batch-load-leaves-a-missing-deployment-id-empty"

    @override
    def describe(self) -> str:
        return (
            "슈퍼관리자가 남의 배포와 없는 id로 정책을 한 번에 읽으면, "
            "그 정책은 노드로, 없는 id 자리는 빈 값으로 온다"
        )

    @override
    def given(self) -> Given[SeedingSession, ADeploymentAndItsPolicy]:
        return AnothersPolicyAndASuperadmin()

    @override
    def when(self) -> When[ADeploymentAndItsPolicy, DeploymentAdapter, Loaded]:
        return LoadingThePolicyAndMissing()

    @override
    def then(self) -> Then[ADeploymentAndItsPolicy, Loaded]:
        return ThePolicyThenNothing(started=self.started)


@dataclass(frozen=True)
class ABatchLoadOfNothingAnswersNothing(
    Scenario[SeedingSession, APlaceAndACaller, DeploymentAdapter, Loaded]
):
    @override
    def summary(self) -> str:
        return "a-batch-load-of-no-deployment-ids-answers-an-empty-list"

    @override
    def describe(self) -> str:
        return "아무 권한도 받지 않은 사용자가 빈 id 목록을 주면, 권한 검사 없이 빈 목록이 온다"

    @override
    def given(self) -> Given[SeedingSession, APlaceAndACaller]:
        return APlaceForDeployments()

    @override
    def when(self) -> When[APlaceAndACaller, DeploymentAdapter, Loaded]:
        return LoadingNothing()

    @override
    def then(self) -> Then[APlaceAndACaller, Loaded]:
        return AnEmptyList()


STARTED = datetime.now(UTC)

SCENARIOS: list[LoadStep] = [
    AUserGrantedReadLoadsThePolicyOfTheirDeployment(started=STARTED),
    AUserGrantedNothingGetsARefusalInPlaceOfThePolicy(),
    ADeploymentCarryingNoPolicyAnswersAnEmptySlot(),
    ABatchLoadAnswersEachElementInOrder(started=STARTED),
    TheSuperadminBatchLoadLeavesAMissingIdEmpty(started=STARTED),
    ABatchLoadOfNothingAnswersNothing(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_loading_policies(
    scenario: LoadStep, adapter: DeploymentAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
