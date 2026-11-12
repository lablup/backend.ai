"""사용량 버킷 훑기 — 관리자 경로와 리소스 그룹 범위 경로.

버킷 행을 만드는 쓰기 경로가 seeder 입구 밖에 있어, 표는 빈 페이지와 거부만 확인한다.
버킷 값을 응답으로 옮기는 분기(무한 값 포함)는 덮지 않는다.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

import pytest

from ai.backend.common.dto.manager.v2.resource_usage.request import (
    AdminSearchDomainUsageBucketsInput,
    AdminSearchProjectUsageBucketsInput,
    AdminSearchUserUsageBucketsInput,
    DomainSearchDomainUsageBucketsInput,
    DomainSearchProjectUsageBucketsInput,
    DomainSearchUserUsageBucketsInput,
)
from ai.backend.manager.api.adapters.resource_usage.adapter import ResourceUsageAdapter
from ai.backend.manager.errors.auth import InsufficientPrivilege
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Says, Scenario, Then, When
from bai_scenario.components.answers import NothingIsFound, TheCallIsRefused
from bai_scenario.components.resource_usage import (
    AUsageScopeAndACaller,
    AUsageScopeAndSomeone,
    Side,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type SearchStep = Scenario[TestSeedingSession, AUsageScopeAndACaller, ResourceUsageAdapter, Any]

LABELS: dict[str, tuple[str, str]] = {
    "admin_search_domain": ("도메인", "domain"),
    "admin_search_project": ("프로젝트", "project"),
    "admin_search_user": ("사용자", "user"),
    "domain_search_domain": ("도메인", "domain"),
    "domain_search_project": ("프로젝트", "project"),
    "domain_search_user": ("사용자", "user"),
}


@dataclass(frozen=True)
class SearchingTheBuckets(When[AUsageScopeAndACaller, ResourceUsageAdapter, Any]):
    """``how`` 가 가리키는 호출로 버킷을 훑는다."""

    how: str

    @override
    def operation(self) -> str:
        return self.how

    @override
    def describe(self, laid: AUsageScopeAndACaller) -> str:
        where, where_en = LABELS[self.how]
        if self.how.startswith("admin_"):
            return Says(
                f"{laid.caller.username} 이 리소스 그룹 {laid.resource_group_name} 의 {where} "
                "사용량 버킷을 범위 없이 훑습니다",
                english=(
                    f"{laid.caller.username} pages through the {where_en} usage buckets of "
                    f"resource group {laid.resource_group_name} without a scope"
                ),
            )
        return Says(
            f"{laid.caller.username} 이 리소스 그룹 {laid.resource_group_name} 을 범위로 {where} "
            "사용량 버킷을 훑습니다",
            english=(
                f"{laid.caller.username} pages through the {where_en} usage buckets of "
                f"resource group {laid.resource_group_name} as the scope"
            ),
        )

    @override
    async def call(self, adapter: ResourceUsageAdapter, laid: AUsageScopeAndACaller) -> Any:
        with ActingAs(laid.caller):
            match self.how:
                case "admin_search_domain":
                    return await adapter.admin_search_domain(
                        AdminSearchDomainUsageBucketsInput(
                            domain_name=laid.domain_name,
                            resource_group=laid.resource_group_name,
                        )
                    )
                case "admin_search_project":
                    return await adapter.admin_search_project(
                        AdminSearchProjectUsageBucketsInput(
                            domain_name=laid.domain_name,
                            resource_group=laid.resource_group_name,
                            project_id=laid.project_id,
                        )
                    )
                case "admin_search_user":
                    return await adapter.admin_search_user(
                        AdminSearchUserUsageBucketsInput(
                            domain_name=laid.domain_name,
                            resource_group=laid.resource_group_name,
                            project_id=laid.project_id,
                            user_uuid=laid.user_id,
                        )
                    )
                case "domain_search_domain":
                    return await adapter.domain_search_domain(
                        DomainSearchDomainUsageBucketsInput(
                            domain_name=laid.domain_name,
                            resource_group=laid.resource_group_name,
                        )
                    )
                case "domain_search_project":
                    return await adapter.domain_search_project(
                        DomainSearchProjectUsageBucketsInput(
                            domain_name=laid.domain_name,
                            resource_group=laid.resource_group_name,
                            project_id=laid.project_id,
                        )
                    )
                case _:
                    return await adapter.domain_search_user(
                        DomainSearchUserUsageBucketsInput(
                            domain_name=laid.domain_name,
                            resource_group=laid.resource_group_name,
                            project_id=laid.project_id,
                            user_uuid=laid.user_id,
                        )
                    )


@dataclass(frozen=True)
class UsageRow(Scenario[TestSeedingSession, AUsageScopeAndACaller, ResourceUsageAdapter, Any]):
    named: str
    guarantees: str
    how: str
    refused: bool = False

    @override
    def summary(self) -> str:
        return self.named

    @override
    def describe(self) -> str:
        return self.guarantees

    @override
    def given(self) -> Given[TestSeedingSession, AUsageScopeAndACaller]:
        if self.refused:
            return AUsageScopeAndSomeone(who=Side.NOBODY)
        if self.how.startswith("admin_"):
            return AUsageScopeAndSomeone(who=Side.SUPERADMIN)
        return AUsageScopeAndSomeone(who=Side.READER)

    @override
    def when(self) -> When[AUsageScopeAndACaller, ResourceUsageAdapter, Any]:
        return SearchingTheBuckets(how=self.how)

    @override
    def then(self) -> Then[AUsageScopeAndACaller, Any]:
        if self.refused:
            expected = (
                InsufficientPrivilege if self.how.startswith("admin_") else NotEnoughPermission
            )
            return TheCallIsRefused(expected)
        return NothingIsFound()


def _row(how: str, *, refused: bool = False) -> UsageRow:
    where, where_en = LABELS[how]
    slug = how.replace("_", "-")
    if refused:
        who = "슈퍼관리자가 아닌" if how.startswith("admin_") else "아무 권한도 받지 않은"
        who_en = (
            "a user other than the superadmin"
            if how.startswith("admin_")
            else "a user granted nothing"
        )
        return UsageRow(
            named=f"{slug}-is-refused-to-a-caller-without-permission",
            guarantees=Says(
                f"{who} 사용자가 {where} 사용량 버킷을 훑으면 거부됩니다",
                english=f"when {who_en} pages through {where_en} usage buckets, the call is rejected",
            ),
            how=how,
            refused=True,
        )
    caller = (
        "슈퍼관리자가"
        if how.startswith("admin_")
        else "리소스 그룹에서 사용량을 읽을 수 있는 일반 사용자가"
    )
    caller_en = (
        "the superadmin"
        if how.startswith("admin_")
        else "a regular user granted permission to read usage in the resource group"
    )
    return UsageRow(
        named=f"{slug}-returns-an-empty-page",
        guarantees=Says(
            f"{caller} 버킷이 없는 자리에서 {where} 사용량 버킷을 훑으면 빈 페이지가 옵니다",
            english=(
                f"when {caller_en} pages through {where_en} usage buckets where none are laid, "
                "an empty page comes back"
            ),
        ),
        how=how,
    )


SCENARIOS: list[SearchStep] = [
    _row("admin_search_domain"),
    _row("admin_search_domain", refused=True),
    _row("admin_search_project"),
    _row("admin_search_project", refused=True),
    _row("admin_search_user"),
    _row("admin_search_user", refused=True),
    _row("domain_search_domain"),
    _row("domain_search_domain", refused=True),
    _row("domain_search_project"),
    _row("domain_search_project", refused=True),
    _row("domain_search_user"),
    _row("domain_search_user", refused=True),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_searching(
    scenario: SearchStep, adapter: ResourceUsageAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
