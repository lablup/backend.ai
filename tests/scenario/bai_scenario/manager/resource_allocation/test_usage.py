"""자원 사용량 조회 — 사용자, 키페어, 프로젝트, 도메인, 자원 그룹."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override
from uuid import UUID

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.resource_allocation.response import (
    DomainResourceAllocationPayload,
    KeypairResourceAllocationPayload,
    ProjectResourceAllocationPayload,
    ResourceGroupResourceAllocationPayload,
    UserConcurrencyPayload,
    UserResourceAllocationPayload,
)
from ai.backend.manager.api.adapters.resource_allocation.adapter import (
    ResourceAllocationAdapter,
)
from ai.backend.manager.errors.auth import InsufficientPrivilege
from ai.backend.manager.errors.base.entity import EntityNotFoundError
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Held,
    Same,
    SameAs,
    Says,
    Scenario,
    Then,
    Verdict,
    When,
)
from bai_scenario.components.answers import MissingResponse, TheCallIsRefused
from bai_scenario.components.resource_allocation_usage import (
    APlaceAndSomeone,
    AUsagePlace,
    resource_group_usage_verdicts,
    scope_usage_verdicts,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

UNKNOWN_NAME = "no-such-target"

type ReadingStep = Scenario[TestSeedingSession, AUsagePlace, ResourceAllocationAdapter, Any]


@dataclass(frozen=True)
class ReadingMyConcurrency(When[AUsagePlace, ResourceAllocationAdapter, UserConcurrencyPayload]):
    """호출자 자신의 동시 세션 수를 읽는다."""

    @override
    def operation(self) -> str:
        return "my_concurrency"

    @override
    def describe(self, laid: AUsagePlace) -> str:
        return Says(
            f"{laid.caller.username}이 자기 동시 세션 수를 조회합니다",
            english=f"{laid.caller.username} reads their own concurrent session counts",
        )

    @override
    async def call(
        self, adapter: ResourceAllocationAdapter, laid: AUsagePlace
    ) -> UserConcurrencyPayload:
        with ActingAs(laid.caller):
            return await adapter.my_concurrency()


@dataclass(frozen=True)
class ReadingMyUserUsage(
    When[AUsagePlace, ResourceAllocationAdapter, UserResourceAllocationPayload]
):
    """호출자 자신의 모든 키페어에 걸친 사용량을 읽는다."""

    @override
    def operation(self) -> str:
        return "my_user_usage"

    @override
    def describe(self, laid: AUsagePlace) -> str:
        return Says(
            f"{laid.caller.username}이 자기 사용량을 조회합니다",
            english=f"{laid.caller.username} reads their own resource usage",
        )

    @override
    async def call(
        self, adapter: ResourceAllocationAdapter, laid: AUsagePlace
    ) -> UserResourceAllocationPayload:
        with ActingAs(laid.caller):
            return await adapter.my_user_usage()


@dataclass(frozen=True)
class ReadingMyKeypairUsage(
    When[AUsagePlace, ResourceAllocationAdapter, KeypairResourceAllocationPayload]
):
    """호출자의 기본 키페어 사용량을 읽는다."""

    @override
    def operation(self) -> str:
        return "my_keypair_usage"

    @override
    def describe(self, laid: AUsagePlace) -> str:
        return Says(
            f"{laid.caller.username}이 자기 기본 키페어 사용량을 조회합니다",
            english=f"{laid.caller.username} reads the usage of their default keypair",
        )

    @override
    async def call(
        self, adapter: ResourceAllocationAdapter, laid: AUsagePlace
    ) -> KeypairResourceAllocationPayload:
        with ActingAs(laid.caller):
            return await adapter.my_keypair_usage()


@dataclass(frozen=True)
class ReadingProjectUsage(
    When[AUsagePlace, ResourceAllocationAdapter, ProjectResourceAllocationPayload]
):
    """미리 만들어 둔 프로젝트의 사용량을 읽는다."""

    @override
    def operation(self) -> str:
        return "project_usage"

    @override
    def describe(self, laid: AUsagePlace) -> str:
        return Says(
            f"{laid.caller.username}이 프로젝트 {laid.project.name}의 사용량을 조회합니다",
            english=f"{laid.caller.username} reads the usage of the project {laid.project.name}",
        )

    @override
    async def call(
        self, adapter: ResourceAllocationAdapter, laid: AUsagePlace
    ) -> ProjectResourceAllocationPayload:
        with ActingAs(laid.caller):
            return await adapter.project_usage(laid.project.id)


@dataclass(frozen=True)
class ReadingDomainUsage(
    When[AUsagePlace, ResourceAllocationAdapter, DomainResourceAllocationPayload]
):
    """미리 만들어 둔 도메인의 사용량을 읽는다. ``unknown``이면 어느 행에도 없는 이름을 쓴다."""

    unknown: bool = False

    @override
    def operation(self) -> str:
        return "admin_domain_usage"

    @override
    def describe(self, laid: AUsagePlace) -> str:
        name_ko = UNKNOWN_NAME if self.unknown else laid.domain.name
        name_en = "a name that does not exist" if self.unknown else laid.domain.name
        return Says(
            f"{laid.caller.username}이 도메인 {name_ko}의 사용량을 조회합니다",
            english=f"{laid.caller.username} reads the usage of the domain {name_en}",
        )

    @override
    async def call(
        self, adapter: ResourceAllocationAdapter, laid: AUsagePlace
    ) -> DomainResourceAllocationPayload:
        with ActingAs(laid.caller):
            return await adapter.admin_domain_usage(
                UNKNOWN_NAME if self.unknown else laid.domain.name
            )


@dataclass(frozen=True)
class ReadingResourceGroupUsage(
    When[AUsagePlace, ResourceAllocationAdapter, ResourceGroupResourceAllocationPayload]
):
    """미리 만들어 둔 자원 그룹의 사용량을 읽는다."""

    @override
    def operation(self) -> str:
        return "resource_group_usage"

    @override
    def describe(self, laid: AUsagePlace) -> str:
        return Says(
            f"{laid.caller.username}이 자원 그룹 {laid.group.name}의 사용량을 조회합니다",
            english=f"{laid.caller.username} reads the usage of the resource group {laid.group.name}",
        )

    @override
    async def call(
        self, adapter: ResourceAllocationAdapter, laid: AUsagePlace
    ) -> ResourceGroupResourceAllocationPayload:
        with ActingAs(laid.caller):
            return await adapter.resource_group_usage(laid.group.name)


@dataclass(frozen=True)
class TheConcurrency(Then[AUsagePlace, UserConcurrencyPayload]):
    """그 사용자의 세션 수가 온다. 아무 세션도 없으므로 모두 0 이다."""

    @override
    def says(self) -> str:
        return Says(
            "그 사용자의 세션 수가 오고, 아무 세션도 없으므로 모두 0 입니다",
            english="that user's session counts come back, all zero because no session exists",
        )

    @override
    def look(self, laid: AUsagePlace, answered: Answered[UserConcurrencyPayload]) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [MissingResponse(answered.raised)]
        return [
            Held[UUID](
                "user_id",
                payload.user_id,
                SameAs(
                    laid.caller.id,
                    Says("호출한 사용자의 id", english="the id of the calling user"),
                ),
            ),
            Same("session_count", payload.session_count, 0),
            Same("private_session_count", payload.private_session_count, 0),
        ]


@dataclass(frozen=True)
class AUserReadingTheirOwnUserReadsTheirConcurrency(
    Scenario[TestSeedingSession, AUsagePlace, ResourceAllocationAdapter, UserConcurrencyPayload]
):
    @override
    def summary(self) -> str:
        return "a-user-reading-their-own-user-reads-their-concurrency"

    @override
    def describe(self) -> str:
        return Says(
            "자기 사용자 범위에서 사용자를 읽을 수 있는 사용자가 자기 동시 세션 수를 읽으면, "
            "세션이 없으므로 모두 0 이 반환됩니다",
            english=(
                "when a user who can read users in their own user scope reads their own "
                "concurrent session counts, all zero comes back because no session exists"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AUsagePlace]:
        return APlaceAndSomeone(self_read=True, slot_type=False)

    @override
    def when(self) -> When[AUsagePlace, ResourceAllocationAdapter, UserConcurrencyPayload]:
        return ReadingMyConcurrency()

    @override
    def then(self) -> Then[AUsagePlace, UserConcurrencyPayload]:
        return TheConcurrency()


@dataclass(frozen=True)
class AUserGrantedNothingMayNotReadTheirConcurrency(
    Scenario[TestSeedingSession, AUsagePlace, ResourceAllocationAdapter, UserConcurrencyPayload]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-read-their-own-concurrency"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 받지 않은 사용자가 자기 동시 세션 수를 읽으려 하면 권한 부족으로 "
            "거부됩니다",
            english=(
                "a user granted nothing reading their own concurrent session counts is rejected "
                "for not enough permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AUsagePlace]:
        return APlaceAndSomeone(slot_type=False)

    @override
    def when(self) -> When[AUsagePlace, ResourceAllocationAdapter, UserConcurrencyPayload]:
        return ReadingMyConcurrency()

    @override
    def then(self) -> Then[AUsagePlace, UserConcurrencyPayload]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class AUserReadingTheirOwnUserReadsTheirUserUsage(
    Scenario[
        TestSeedingSession, AUsagePlace, ResourceAllocationAdapter, UserResourceAllocationPayload
    ]
):
    @override
    def summary(self) -> str:
        return "a-user-reading-their-own-user-reads-their-user-usage"

    @override
    def describe(self) -> str:
        return Says(
            "자기 사용자 범위에서 사용자를 읽을 수 있는 사용자가 자기 사용량을 읽으면, 등록된 슬롯 "
            "종류의 한도가 무한대로 오고 사용량은 0 입니다",
            english=(
                "when a user who can read users in their own user scope reads their own usage, "
                "the registered slot type's limit comes back unlimited and the usage is zero"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AUsagePlace]:
        return APlaceAndSomeone(self_read=True)

    @override
    def when(self) -> When[AUsagePlace, ResourceAllocationAdapter, UserResourceAllocationPayload]:
        return ReadingMyUserUsage()

    @override
    def then(self) -> Then[AUsagePlace, UserResourceAllocationPayload]:
        return TheUserUsage()


@dataclass(frozen=True)
class TheUserUsage(Then[AUsagePlace, UserResourceAllocationPayload]):
    """사용량 응답에서 사용자 범위를 벗겨 검사한다."""

    @override
    def says(self) -> str:
        return Says(
            "사용자 범위의 한도는 무한대이고 사용량은 0 입니다",
            english="the user scope's limit is unlimited and the usage is zero",
        )

    @override
    def look(
        self, laid: AUsagePlace, answered: Answered[UserResourceAllocationPayload]
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [MissingResponse(answered.raised)]
        return scope_usage_verdicts("user.", payload.user, laid.slot_name)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotReadTheirUserUsage(
    Scenario[
        TestSeedingSession, AUsagePlace, ResourceAllocationAdapter, UserResourceAllocationPayload
    ]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-read-their-own-user-usage"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 받지 않은 사용자가 자기 사용량을 읽으려 하면 권한 부족으로 거부됩니다",
            english=(
                "a user granted nothing reading their own usage is rejected for not enough "
                "permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AUsagePlace]:
        return APlaceAndSomeone()

    @override
    def when(self) -> When[AUsagePlace, ResourceAllocationAdapter, UserResourceAllocationPayload]:
        return ReadingMyUserUsage()

    @override
    def then(self) -> Then[AUsagePlace, UserResourceAllocationPayload]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class TheKeypairUsage(Then[AUsagePlace, KeypairResourceAllocationPayload]):
    """키페어 범위의 사용량 전체가 온다."""

    @override
    def says(self) -> str:
        return Says(
            "키페어 범위의 한도는 무한대이고 사용량은 0 입니다",
            english="the keypair scope's limit is unlimited and the usage is zero",
        )

    @override
    def look(
        self, laid: AUsagePlace, answered: Answered[KeypairResourceAllocationPayload]
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [MissingResponse(answered.raised)]
        return scope_usage_verdicts("keypair.", payload.keypair, laid.slot_name)


@dataclass(frozen=True)
class AUserReadingTheirOwnUserReadsTheirKeypairUsage(
    Scenario[
        TestSeedingSession, AUsagePlace, ResourceAllocationAdapter, KeypairResourceAllocationPayload
    ]
):
    @override
    def summary(self) -> str:
        return "a-user-reading-their-own-user-reads-their-keypair-usage"

    @override
    def describe(self) -> str:
        return Says(
            "자기 사용자 범위에서 사용자를 읽을 수 있는 사용자가 자기 기본 키페어 사용량을 읽으면, "
            "등록된 슬롯 종류의 한도가 무한대로 오고 사용량은 0 입니다",
            english=(
                "when a user who can read users in their own user scope reads their default "
                "keypair's usage, the registered slot type's limit comes back unlimited and the "
                "usage is zero"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AUsagePlace]:
        return APlaceAndSomeone(self_read=True)

    @override
    def when(
        self,
    ) -> When[AUsagePlace, ResourceAllocationAdapter, KeypairResourceAllocationPayload]:
        return ReadingMyKeypairUsage()

    @override
    def then(self) -> Then[AUsagePlace, KeypairResourceAllocationPayload]:
        return TheKeypairUsage()


@dataclass(frozen=True)
class AUserGrantedNothingMayNotReadTheirKeypairUsage(
    Scenario[
        TestSeedingSession, AUsagePlace, ResourceAllocationAdapter, KeypairResourceAllocationPayload
    ]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-read-their-own-keypair-usage"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 받지 않은 사용자가 자기 키페어 사용량을 읽으려 하면 권한 부족으로 "
            "거부됩니다",
            english=(
                "a user granted nothing reading their own keypair usage is rejected for not "
                "enough permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AUsagePlace]:
        return APlaceAndSomeone()

    @override
    def when(
        self,
    ) -> When[AUsagePlace, ResourceAllocationAdapter, KeypairResourceAllocationPayload]:
        return ReadingMyKeypairUsage()

    @override
    def then(self) -> Then[AUsagePlace, KeypairResourceAllocationPayload]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class TheProjectUsage(Then[AUsagePlace, ProjectResourceAllocationPayload]):
    """프로젝트 범위의 사용량 전체가 온다."""

    @override
    def says(self) -> str:
        return Says(
            "프로젝트 범위의 한도는 무한대이고 사용량은 0 입니다",
            english="the project scope's limit is unlimited and the usage is zero",
        )

    @override
    def look(
        self, laid: AUsagePlace, answered: Answered[ProjectResourceAllocationPayload]
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [MissingResponse(answered.raised)]
        return scope_usage_verdicts("project.", payload.project, laid.slot_name)


@dataclass(frozen=True)
class AUserReadingTheProjectReadsItsUsage(
    Scenario[
        TestSeedingSession, AUsagePlace, ResourceAllocationAdapter, ProjectResourceAllocationPayload
    ]
):
    @override
    def summary(self) -> str:
        return "a-user-reading-the-project-reads-its-usage"

    @override
    def describe(self) -> str:
        return Says(
            "프로젝트 범위에서 프로젝트를 읽을 수 있는 사용자가 그 프로젝트의 사용량을 읽으면, "
            "등록된 슬롯 종류의 한도가 무한대로 오고 사용량은 0 입니다",
            english=(
                "when a user who can read the project in its scope reads that project's usage, "
                "the registered slot type's limit comes back unlimited and the usage is zero"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AUsagePlace]:
        return APlaceAndSomeone(project_read=True)

    @override
    def when(
        self,
    ) -> When[AUsagePlace, ResourceAllocationAdapter, ProjectResourceAllocationPayload]:
        return ReadingProjectUsage()

    @override
    def then(self) -> Then[AUsagePlace, ProjectResourceAllocationPayload]:
        return TheProjectUsage()


@dataclass(frozen=True)
class AUserGrantedNothingMayNotReadTheProjectUsage(
    Scenario[
        TestSeedingSession, AUsagePlace, ResourceAllocationAdapter, ProjectResourceAllocationPayload
    ]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-read-a-projects-usage"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 받지 않은 사용자가 프로젝트 사용량을 읽으려 하면 권한 부족으로 거부됩니다",
            english=(
                "a user granted nothing reading a project's usage is rejected for not enough "
                "permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AUsagePlace]:
        return APlaceAndSomeone()

    @override
    def when(
        self,
    ) -> When[AUsagePlace, ResourceAllocationAdapter, ProjectResourceAllocationPayload]:
        return ReadingProjectUsage()

    @override
    def then(self) -> Then[AUsagePlace, ProjectResourceAllocationPayload]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class TheDomainUsage(Then[AUsagePlace, DomainResourceAllocationPayload]):
    """도메인 범위의 사용량 전체가 온다."""

    @override
    def says(self) -> str:
        return Says(
            "도메인 범위의 한도는 무한대이고 사용량은 0 입니다",
            english="the domain scope's limit is unlimited and the usage is zero",
        )

    @override
    def look(
        self, laid: AUsagePlace, answered: Answered[DomainResourceAllocationPayload]
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [MissingResponse(answered.raised)]
        return scope_usage_verdicts("domain.", payload.domain, laid.slot_name)


@dataclass(frozen=True)
class AUserReadingTheDomainReadsItsUsage(
    Scenario[
        TestSeedingSession, AUsagePlace, ResourceAllocationAdapter, DomainResourceAllocationPayload
    ]
):
    @override
    def summary(self) -> str:
        return "a-user-reading-the-domain-reads-its-usage"

    @override
    def describe(self) -> str:
        return Says(
            "도메인 범위에서 도메인을 읽을 수 있는 사용자가 그 도메인의 사용량을 읽으면, 등록된 "
            "슬롯 종류의 한도가 무한대로 오고 사용량은 0 입니다",
            english=(
                "when a user who can read the domain in its scope reads that domain's usage, the "
                "registered slot type's limit comes back unlimited and the usage is zero"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AUsagePlace]:
        return APlaceAndSomeone(domain_read=True)

    @override
    def when(self) -> When[AUsagePlace, ResourceAllocationAdapter, DomainResourceAllocationPayload]:
        return ReadingDomainUsage()

    @override
    def then(self) -> Then[AUsagePlace, DomainResourceAllocationPayload]:
        return TheDomainUsage()


@dataclass(frozen=True)
class ANameNothingAnswersToIsNotFound(
    Scenario[
        TestSeedingSession, AUsagePlace, ResourceAllocationAdapter, DomainResourceAllocationPayload
    ]
):
    @override
    def summary(self) -> str:
        return "reading-the-usage-of-a-domain-nothing-answers-to-is-not-found"

    @override
    def describe(self) -> str:
        return Says(
            "없는 이름으로 도메인 사용량을 읽으면 대상이 없다는 것으로 거부됩니다",
            english=(
                "reading the usage of a domain name nothing answers to is rejected as no such "
                "target"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AUsagePlace]:
        return APlaceAndSomeone(slot_type=False)

    @override
    def when(self) -> When[AUsagePlace, ResourceAllocationAdapter, DomainResourceAllocationPayload]:
        return ReadingDomainUsage(unknown=True)

    @override
    def then(self) -> Then[AUsagePlace, DomainResourceAllocationPayload]:
        return TheCallIsRefused(EntityNotFoundError)


@dataclass(frozen=True)
class TheSuperadminReadsTheResourceGroupUsage(
    Scenario[
        TestSeedingSession,
        AUsagePlace,
        ResourceAllocationAdapter,
        ResourceGroupResourceAllocationPayload,
    ]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-reads-a-resource-groups-usage"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 자원 그룹의 사용량을 읽으면, 에이전트가 없으므로 용량·사용량·여유가 "
            "모두 비어 있습니다. 이 호출은 superadmin 역할이 막습니다",
            english=(
                "when the superadmin reads a resource group's usage, capacity, usage and free "
                "are all empty because no agent exists. the superadmin role gates this call"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AUsagePlace]:
        return APlaceAndSomeone(role=UserRole.SUPERADMIN, slot_type=False)

    @override
    def when(
        self,
    ) -> When[AUsagePlace, ResourceAllocationAdapter, ResourceGroupResourceAllocationPayload]:
        return ReadingResourceGroupUsage()

    @override
    def then(self) -> Then[AUsagePlace, ResourceGroupResourceAllocationPayload]:
        return TheResourceGroupUsageNode()


@dataclass(frozen=True)
class TheResourceGroupUsageNode(Then[AUsagePlace, ResourceGroupResourceAllocationPayload]):
    """자원 그룹 사용량 응답에서 범위를 벗겨 검사한다."""

    @override
    def says(self) -> str:
        return Says(
            "자원 그룹의 용량, 사용량, 여유가 모두 비어 있습니다",
            english="the resource group's capacity, usage and free amount are all empty",
        )

    @override
    def look(
        self, laid: AUsagePlace, answered: Answered[ResourceGroupResourceAllocationPayload]
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [MissingResponse(answered.raised)]
        return resource_group_usage_verdicts(
            "resource_group.", payload.resource_group, laid.slot_name
        )


@dataclass(frozen=True)
class AUserMayNotReadTheResourceGroupUsage(
    Scenario[
        TestSeedingSession,
        AUsagePlace,
        ResourceAllocationAdapter,
        ResourceGroupResourceAllocationPayload,
    ]
):
    @override
    def summary(self) -> str:
        return "a-user-may-not-read-a-resource-groups-usage"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 아닌 사용자가 자원 그룹 사용량을 읽으려 하면 역할이 없다는 것으로 "
            "거부됩니다",
            english=(
                "a user who is not the superadmin reading a resource group's usage is rejected "
                "for lacking the role"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AUsagePlace]:
        return APlaceAndSomeone(slot_type=False)

    @override
    def when(
        self,
    ) -> When[AUsagePlace, ResourceAllocationAdapter, ResourceGroupResourceAllocationPayload]:
        return ReadingResourceGroupUsage()

    @override
    def then(self) -> Then[AUsagePlace, ResourceGroupResourceAllocationPayload]:
        return TheCallIsRefused(InsufficientPrivilege)


SCENARIOS: list[ReadingStep] = [
    AUserReadingTheirOwnUserReadsTheirConcurrency(),
    AUserGrantedNothingMayNotReadTheirConcurrency(),
    AUserReadingTheirOwnUserReadsTheirUserUsage(),
    AUserGrantedNothingMayNotReadTheirUserUsage(),
    AUserReadingTheirOwnUserReadsTheirKeypairUsage(),
    AUserGrantedNothingMayNotReadTheirKeypairUsage(),
    AUserReadingTheProjectReadsItsUsage(),
    AUserGrantedNothingMayNotReadTheProjectUsage(),
    AUserReadingTheDomainReadsItsUsage(),
    ANameNothingAnswersToIsNotFound(),
    TheSuperadminReadsTheResourceGroupUsage(),
    AUserMayNotReadTheResourceGroupUsage(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_usage(
    scenario: ReadingStep, adapter: ResourceAllocationAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
