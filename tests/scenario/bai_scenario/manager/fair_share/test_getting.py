"""도메인, 프로젝트, 사용자의 fair share 하나 조회하기."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, override

import pytest

from ai.backend.common.data.permission.types import Permission
from ai.backend.common.dto.manager.v2.fair_share.request import (
    GetDomainFairShareInput,
    GetProjectFairShareInput,
    GetUserFairShareInput,
)
from ai.backend.common.dto.manager.v2.fair_share.response import (
    DomainFairShareNode,
    ProjectFairShareNode,
    UserFairShareNode,
)
from ai.backend.manager.api.adapters.fair_share.adapter import FairShareAdapter
from ai.backend.manager.data.fair_share.types import (
    DomainFairShareData,
    ProjectFairShareData,
    UserFairShareData,
)
from ai.backend.manager.errors.base.entity import EntityNotFoundError
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Says, Scenario, Then, When
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.fair_share import (
    ADomainWeightAndSomeone,
    AProjectWeightAndSomeone,
    AUserWeightAndSomeone,
    AWeightAndACaller,
    TheDomainRecord,
    TheProjectRecord,
    TheUserRecord,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type Laid = AWeightAndACaller[Any]
type GettingStep = Scenario[TestSeedingSession, Laid, FairShareAdapter, Any]


@dataclass(frozen=True)
class ReadingInTheGroup:
    """요청이 이름으로 가리키는 리소스 그룹. ``missing``이면 아무도 만들지 않은 이름이다."""

    missing: bool = False

    def name(self, laid: Laid) -> str:
        if self.missing:
            return f"{laid.group.name}-missing"
        return laid.group.name

    def says(self, laid: Laid, what_ko: str, what_en: str) -> str:
        if self.missing:
            return Says(
                (
                    f"{laid.caller.username} 이 없는 리소스 그룹 이름으로 {what_ko} {laid.about}의 "
                    "fair share 를 조회합니다"
                ),
                english=(
                    f"{laid.caller.username} reads the fair share of {what_en} {laid.about} under "
                    "a resource group name nobody created"
                ),
            )
        return Says(
            (
                f"{laid.caller.username} 이 {laid.group.name} 안 {what_ko} {laid.about}의 "
                "fair share 를 조회합니다"
            ),
            english=(
                f"{laid.caller.username} reads the fair share of {what_en} {laid.about} in "
                f"{laid.group.name}"
            ),
        )


@dataclass(frozen=True)
class ReadingTheDomain(
    When[AWeightAndACaller[DomainFairShareData], FairShareAdapter, DomainFairShareNode | None]
):
    """그 도메인의 fair share 하나를 조회한다."""

    group: ReadingInTheGroup = ReadingInTheGroup()

    @override
    def operation(self) -> str:
        return "get_domain"

    @override
    def describe(self, laid: AWeightAndACaller[DomainFairShareData]) -> str:
        return self.group.says(laid, "도메인", "domain")

    @override
    async def call(
        self, adapter: FairShareAdapter, laid: AWeightAndACaller[DomainFairShareData]
    ) -> DomainFairShareNode | None:
        with ActingAs(laid.caller):
            payload = await adapter.get_domain(
                GetDomainFairShareInput(
                    resource_group=self.group.name(laid), domain_name=laid.record.domain_name
                )
            )
        return payload.item


@dataclass(frozen=True)
class ReadingTheProject(
    When[AWeightAndACaller[ProjectFairShareData], FairShareAdapter, ProjectFairShareNode | None]
):
    """그 프로젝트의 fair share 하나를 조회한다."""

    group: ReadingInTheGroup = ReadingInTheGroup()

    @override
    def operation(self) -> str:
        return "get_project"

    @override
    def describe(self, laid: AWeightAndACaller[ProjectFairShareData]) -> str:
        return self.group.says(laid, "프로젝트", "project")

    @override
    async def call(
        self, adapter: FairShareAdapter, laid: AWeightAndACaller[ProjectFairShareData]
    ) -> ProjectFairShareNode | None:
        with ActingAs(laid.caller):
            payload = await adapter.get_project(
                GetProjectFairShareInput(
                    resource_group=self.group.name(laid), project_id=laid.record.project_id
                )
            )
        return payload.item


@dataclass(frozen=True)
class ReadingTheMember(
    When[AWeightAndACaller[UserFairShareData], FairShareAdapter, UserFairShareNode | None]
):
    """그 프로젝트 안 멤버의 fair share 하나를 조회한다."""

    group: ReadingInTheGroup = ReadingInTheGroup()

    @override
    def operation(self) -> str:
        return "get_user"

    @override
    def describe(self, laid: AWeightAndACaller[UserFairShareData]) -> str:
        return self.group.says(laid, "사용자", "user")

    @override
    async def call(
        self, adapter: FairShareAdapter, laid: AWeightAndACaller[UserFairShareData]
    ) -> UserFairShareNode | None:
        with ActingAs(laid.caller):
            payload = await adapter.get_user(
                GetUserFairShareInput(
                    resource_group=self.group.name(laid),
                    project_id=laid.record.project_id,
                    user_uuid=laid.record.user_uuid,
                )
            )
        return payload.item


@dataclass(frozen=True)
class Target:
    """조회할 fair share 의 종류와 그 종류의 준비, 호출, 검사."""

    key: str
    korean: str
    english: str
    given: Callable[[Permission], Given[Any, Any]]
    when: Callable[[ReadingInTheGroup], When[Any, FairShareAdapter, Any]]
    then: Callable[[datetime], Then[Any, Any]]


DOMAIN = Target(
    "domain", "도메인", "domain", ADomainWeightAndSomeone, ReadingTheDomain, TheDomainRecord
)
PROJECT = Target(
    "project", "프로젝트", "project", AProjectWeightAndSomeone, ReadingTheProject, TheProjectRecord
)
USER = Target("user", "사용자", "user", AUserWeightAndSomeone, ReadingTheMember, TheUserRecord)


@dataclass(frozen=True)
class AReaderReadsTheWeight(Scenario[TestSeedingSession, Laid, FairShareAdapter, Any]):
    target: Target
    started: datetime

    @override
    def summary(self) -> str:
        return f"a-user-granted-fair-share-read-on-the-group-reads-a-{self.target.key}-fair-share"

    @override
    def describe(self) -> str:
        return Says(
            (
                f"그 리소스 그룹 범위에서 fair share 읽기 역할을 받은 사용자가 {self.target.korean}의 "
                "fair share 를 조회하면 그 그룹에 기록한 값이 그대로 옵니다"
            ),
            english=(
                "when a user granted the fair share read role in the resource group scope reads "
                f"the fair share of a {self.target.english}, the values recorded in that group "
                "come back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, Laid]:
        return self.target.given(Permission.READ)

    @override
    def when(self) -> When[Laid, FairShareAdapter, Any]:
        return self.target.when(ReadingInTheGroup())

    @override
    def then(self) -> Then[Laid, Any]:
        return self.target.then(self.started)


@dataclass(frozen=True)
class AnUpdaterMayNotReadTheWeight(Scenario[TestSeedingSession, Laid, FairShareAdapter, Any]):
    target: Target

    @override
    def summary(self) -> str:
        return f"a-user-granted-only-fair-share-update-may-not-read-a-{self.target.key}-fair-share"

    @override
    def describe(self) -> str:
        return Says(
            (
                "그 리소스 그룹 범위에서 fair share 수정 역할만 받은 사용자가 "
                f"{self.target.korean}의 fair share 를 조회하면 권한 부족으로 거부됩니다"
            ),
            english=(
                "when a user granted only the fair share update role in the resource group scope "
                f"reads the fair share of a {self.target.english}, it is rejected for a lack of "
                "permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, Laid]:
        return self.target.given(Permission.UPDATE)

    @override
    def when(self) -> When[Laid, FairShareAdapter, Any]:
        return self.target.when(ReadingInTheGroup())

    @override
    def then(self) -> Then[Laid, Any]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class AnUnknownGroupFails(Scenario[TestSeedingSession, Laid, FairShareAdapter, Any]):
    target: Target

    @override
    def summary(self) -> str:
        return f"reading-a-{self.target.key}-fair-share-in-an-unknown-resource-group-fails"

    @override
    def describe(self) -> str:
        return Says(
            (
                "fair share 읽기 역할을 받은 사용자가 없는 리소스 그룹 이름으로 "
                f"{self.target.korean}의 fair share 를 조회하면 리소스 그룹을 찾지 못해 실패합니다"
            ),
            english=(
                "when a user granted the fair share read role reads the fair share of a "
                f"{self.target.english} under a resource group name nobody created, it fails "
                "because the resource group is not found"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, Laid]:
        return self.target.given(Permission.READ)

    @override
    def when(self) -> When[Laid, FairShareAdapter, Any]:
        return self.target.when(ReadingInTheGroup(missing=True))

    @override
    def then(self) -> Then[Laid, Any]:
        return TheCallIsRefused(EntityNotFoundError)


SCENARIOS: list[GettingStep] = [
    row
    for target in (DOMAIN, PROJECT, USER)
    for row in (
        AReaderReadsTheWeight(target, started=datetime.now(UTC)),
        AnUpdaterMayNotReadTheWeight(target),
        AnUnknownGroupFails(target),
    )
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_getting(
    scenario: GettingStep, adapter: FairShareAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
