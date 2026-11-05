"""GQL 경로의 사용량 버킷 훑기 — 범위 경로, 관리자 경로, 범위 없는 경로."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

import pytest

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

type GqlStep = Scenario[TestSeedingSession, AUsageScopeAndACaller, ResourceUsageAdapter, Any]

LABELS: dict[str, tuple[str, str]] = {
    "gql_search_domain_scoped": ("도메인", "domain"),
    "gql_search_project_scoped": ("프로젝트", "project"),
    "gql_search_user_scoped": ("사용자", "user"),
    "gql_admin_search_domain": ("도메인", "domain"),
    "gql_admin_search_project": ("프로젝트", "project"),
    "gql_admin_search_user": ("사용자", "user"),
    "gql_search_project_unscoped": ("프로젝트", "project"),
    "gql_search_user_unscoped": ("사용자", "user"),
}


@dataclass(frozen=True)
class GqlSearchingTheBuckets(When[AUsageScopeAndACaller, ResourceUsageAdapter, Any]):
    """``how`` 가 가리키는 GQL 경로 호출로 버킷을 훑는다."""

    how: str

    @override
    def operation(self) -> str:
        return self.how

    @override
    def describe(self, laid: AUsageScopeAndACaller) -> str:
        where, where_en = LABELS[self.how]
        return Says(
            f"{laid.caller.username} 이 리소스 그룹 {laid.resource_group_name} 의 {where} 사용량 "
            "버킷을 GQL 경로로 훑습니다",
            english=(
                f"{laid.caller.username} pages through the {where_en} usage buckets of resource "
                f"group {laid.resource_group_name} through the GQL path"
            ),
        )

    @override
    async def call(self, adapter: ResourceUsageAdapter, laid: AUsageScopeAndACaller) -> Any:
        with ActingAs(laid.caller):
            match self.how:
                case "gql_search_domain_scoped":
                    return await adapter.gql_search_domain_scoped(
                        laid.resource_group_name, laid.domain_name
                    )
                case "gql_search_project_scoped":
                    return await adapter.gql_search_project_scoped(
                        laid.resource_group_name, laid.domain_name, laid.project_id
                    )
                case "gql_search_user_scoped":
                    return await adapter.gql_search_user_scoped(
                        laid.resource_group_name,
                        laid.domain_name,
                        laid.project_id,
                        laid.user_id,
                    )
                case "gql_admin_search_domain":
                    return await adapter.gql_admin_search_domain()
                case "gql_admin_search_project":
                    return await adapter.gql_admin_search_project()
                case "gql_admin_search_user":
                    return await adapter.gql_admin_search_user()
                case "gql_search_project_unscoped":
                    return await adapter.gql_search_project_unscoped([])
                case _:
                    return await adapter.gql_search_user_unscoped([])


@dataclass(frozen=True)
class GqlRow(Scenario[TestSeedingSession, AUsageScopeAndACaller, ResourceUsageAdapter, Any]):
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
        return AUsageScopeAndSomeone(who=Side.NOBODY if self.refused else Side.SUPERADMIN)

    @override
    def when(self) -> When[AUsageScopeAndACaller, ResourceUsageAdapter, Any]:
        return GqlSearchingTheBuckets(how=self.how)

    @override
    def then(self) -> Then[AUsageScopeAndACaller, Any]:
        if self.refused:
            expected = (
                NotEnoughPermission if self.how.endswith("_scoped") else InsufficientPrivilege
            )
            return TheCallIsRefused(expected)
        return NothingIsFound()


def _row(how: str, *, refused: bool = False) -> GqlRow:
    where, where_en = LABELS[how]
    slug = how.replace("_", "-")
    if refused:
        in_scope = how.endswith("_scoped")
        who = "아무 권한도 받지 않은" if in_scope else "슈퍼관리자가 아닌"
        who_en = "a user granted nothing" if in_scope else "a user other than the superadmin"
        return GqlRow(
            named=f"{slug}-is-refused-to-a-caller-without-permission",
            guarantees=Says(
                f"{who} 사용자가 GQL 경로로 {where} 사용량 버킷을 훑으면 거부됩니다",
                english=(
                    f"when {who_en} pages through {where_en} usage buckets through the GQL "
                    "path, the call is rejected"
                ),
            ),
            how=how,
            refused=True,
        )
    return GqlRow(
        named=f"{slug}-returns-an-empty-page",
        guarantees=Says(
            f"슈퍼관리자가 버킷이 없는 자리에서 GQL 경로로 {where} 사용량 버킷을 훑으면 빈 "
            "페이지가 옵니다",
            english=(
                f"when the superadmin pages through {where_en} usage buckets through the GQL "
                "path where none are laid, an empty page comes back"
            ),
        ),
        how=how,
    )


SCENARIOS: list[GqlStep] = [
    _row("gql_search_domain_scoped"),
    _row("gql_search_domain_scoped", refused=True),
    _row("gql_search_project_scoped"),
    _row("gql_search_project_scoped", refused=True),
    _row("gql_search_user_scoped"),
    _row("gql_search_user_scoped", refused=True),
    _row("gql_admin_search_domain"),
    _row("gql_admin_search_domain", refused=True),
    _row("gql_admin_search_project"),
    _row("gql_admin_search_project", refused=True),
    _row("gql_admin_search_user"),
    _row("gql_admin_search_user", refused=True),
    _row("gql_search_project_unscoped"),
    _row("gql_search_project_unscoped", refused=True),
    _row("gql_search_user_unscoped"),
    _row("gql_search_user_unscoped", refused=True),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_gql_searching(
    scenario: GqlStep, adapter: ResourceUsageAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
