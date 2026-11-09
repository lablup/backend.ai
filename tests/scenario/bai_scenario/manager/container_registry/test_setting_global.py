"""컨테이너 레지스트리를 public 스코프에 넣거나 빼기."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override
from uuid import UUID

import pytest

from ai.backend.common.data.entity.container_registry import ContainerRegistryID
from ai.backend.common.data.user.types import UserRole
from ai.backend.manager.api.adapters.container_registry.adapter import ContainerRegistryAdapter
from ai.backend.manager.data.container_registry.types import ContainerRegistryData
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
from bai_scenario.components.container_registry import ARegistryAndACaller, ARegistryAndSomeone
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type SettingStep = Scenario[
    TestSeedingSession, ARegistryAndACaller, ContainerRegistryAdapter, ContainerRegistryData
]


@dataclass(frozen=True)
class SettingGlobal(When[ARegistryAndACaller, ContainerRegistryAdapter, ContainerRegistryData]):
    """미리 만들어 둔 레지스트리를 public 스코프에서 빼낸다."""

    is_global: bool = False

    @override
    def operation(self) -> str:
        return "apply_global"

    @override
    def describe(self, laid: ARegistryAndACaller) -> str:
        return Says(
            f"{laid.caller.username}이 {laid.registry.registry_name}의 전역 여부를 바꿉니다",
            english=f"{laid.caller.username} changes whether {laid.registry.registry_name} is global",
        )

    @override
    async def call(
        self, adapter: ContainerRegistryAdapter, laid: ARegistryAndACaller
    ) -> ContainerRegistryData:
        with ActingAs(laid.caller):
            return await adapter.apply_global(ContainerRegistryID(laid.registry.id), self.is_global)


@dataclass(frozen=True)
class TheRegistryTakesTheNewVisibility(Then[ARegistryAndACaller, ContainerRegistryData]):
    """레지스트리가 새 전역 여부를 싣고 통째로 반환된다."""

    is_global: bool

    @override
    def says(self) -> str:
        return Says(
            "미리 저장한 레지스트리 전체가 새 전역 여부로 반환됩니다",
            english="the whole seeded registry comes back with the new visibility",
        )

    @override
    def look(
        self, laid: ARegistryAndACaller, answered: Answered[ContainerRegistryData]
    ) -> list[Verdict]:
        data = answered.response
        if data is None:
            return [MissingResponse(answered.raised)]
        seeded = Says(
            "미리 저장한 컨테이너 레지스트리의 id",
            english="the id of the container registry seeded in advance",
        )
        return [
            Held[UUID]("id", data.id, SameAs[UUID](laid.registry.id, seeded)),
            Same("url", data.url, laid.registry.url),
            Same("registry_name", data.registry_name, laid.registry.registry_name),
            Same("type", data.type, laid.registry.type),
            Same("project", data.project, laid.registry.project),
            Same("username", data.username, laid.registry.username),
            Same("password", data.password, laid.registry.password),
            Same("ssl_verify", data.ssl_verify, laid.registry.ssl_verify),
            Same("is_global", data.is_global, self.is_global),
            Same("extra", data.extra, laid.registry.extra),
        ]


@dataclass(frozen=True)
class TheSuperadminTakesTheRegistryOutOfPublic(
    Scenario[
        TestSeedingSession, ARegistryAndACaller, ContainerRegistryAdapter, ContainerRegistryData
    ]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-takes-a-registry-out-of-public"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 레지스트리의 전역 여부를 거짓으로 바꾸면, 같은 레지스트리가 전역이 "
            "아닌 채로 통째로 반환됩니다",
            english=(
                "when the superadmin sets a registry not global, the same registry comes back "
                "whole with global false"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ARegistryAndACaller]:
        return ARegistryAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ARegistryAndACaller, ContainerRegistryAdapter, ContainerRegistryData]:
        return SettingGlobal(is_global=False)

    @override
    def then(self) -> Then[ARegistryAndACaller, ContainerRegistryData]:
        return TheRegistryTakesTheNewVisibility(is_global=False)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotChangeVisibility(
    Scenario[
        TestSeedingSession, ARegistryAndACaller, ContainerRegistryAdapter, ContainerRegistryData
    ]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-change-a-registry-visibility"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 받지 않은 사용자가 레지스트리의 전역 여부를 바꾸려 하면 권한 부족으로 "
            "거부됩니다. 이 호출은 레지스트리와 public 스코프 양쪽의 권한을 함께 봅니다",
            english=(
                "when a user granted nothing tries to change a registry's visibility, it is "
                "rejected for lack of permission. This call checks permission on the registry "
                "and on the public scope together"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ARegistryAndACaller]:
        return ARegistryAndSomeone()

    @override
    def when(self) -> When[ARegistryAndACaller, ContainerRegistryAdapter, ContainerRegistryData]:
        return SettingGlobal(is_global=False)

    @override
    def then(self) -> Then[ARegistryAndACaller, ContainerRegistryData]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class AUserGrantedOnBothScopesChangesVisibility(
    Scenario[
        TestSeedingSession, ARegistryAndACaller, ContainerRegistryAdapter, ContainerRegistryData
    ]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-on-both-scopes-takes-a-registry-out-of-public"

    @override
    def describe(self) -> str:
        return Says(
            "레지스트리와 public 두 범위에 수정 권한을 받은 사용자가 레지스트리의 전역 여부를 "
            "거짓으로 바꾸면, 같은 레지스트리가 전역이 아닌 채로 통째로 반환됩니다",
            english=(
                "when a user granted update permission on the registry and on public sets the "
                "registry not global, the same registry comes back whole with global false"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ARegistryAndACaller]:
        return ARegistryAndSomeone(keeps_registry=True, keeps_public=True)

    @override
    def when(self) -> When[ARegistryAndACaller, ContainerRegistryAdapter, ContainerRegistryData]:
        return SettingGlobal(is_global=False)

    @override
    def then(self) -> Then[ARegistryAndACaller, ContainerRegistryData]:
        return TheRegistryTakesTheNewVisibility(is_global=False)


@dataclass(frozen=True)
class AUserGrantedOnTheRegistryButNotPublicMayNotChangeVisibility(
    Scenario[
        TestSeedingSession, ARegistryAndACaller, ContainerRegistryAdapter, ContainerRegistryData
    ]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-on-the-registry-but-not-public-may-not-change-a-registry-visibility"

    @override
    def describe(self) -> str:
        return Says(
            "레지스트리에 수정 권한을 받고 public 에는 받지 않은 사용자가 레지스트리의 전역 여부를 "
            "바꾸려 하면 권한 부족으로 거부됩니다. 이 호출은 두 스코프 가운데 하나만 허락해도 "
            "통과하지 않습니다",
            english=(
                "when a user granted update permission on the registry but not on public tries to "
                "change a registry's visibility, it is rejected for lack of permission. This call "
                "does not pass with only one of the two scopes permitting it"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ARegistryAndACaller]:
        return ARegistryAndSomeone(keeps_registry=True)

    @override
    def when(self) -> When[ARegistryAndACaller, ContainerRegistryAdapter, ContainerRegistryData]:
        return SettingGlobal(is_global=False)

    @override
    def then(self) -> Then[ARegistryAndACaller, ContainerRegistryData]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class AUserGrantedOnPublicButNotTheRegistryMayNotChangeVisibility(
    Scenario[
        TestSeedingSession, ARegistryAndACaller, ContainerRegistryAdapter, ContainerRegistryData
    ]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-on-public-but-not-the-registry-may-not-change-a-registry-visibility"

    @override
    def describe(self) -> str:
        return Says(
            "public 에 수정 권한을 받고 레지스트리에는 받지 않은 사용자가 레지스트리의 전역 여부를 "
            "바꾸려 하면 권한 부족으로 거부됩니다. 이 호출은 두 스코프 가운데 하나만 허락해도 "
            "통과하지 않습니다",
            english=(
                "when a user granted update permission on public but not on the registry tries to "
                "change a registry's visibility, it is rejected for lack of permission. This call "
                "does not pass with only one of the two scopes permitting it"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ARegistryAndACaller]:
        return ARegistryAndSomeone(keeps_public=True)

    @override
    def when(self) -> When[ARegistryAndACaller, ContainerRegistryAdapter, ContainerRegistryData]:
        return SettingGlobal(is_global=False)

    @override
    def then(self) -> Then[ARegistryAndACaller, ContainerRegistryData]:
        return TheCallIsRefused(NotEnoughPermission)


SCENARIOS: list[SettingStep] = [
    TheSuperadminTakesTheRegistryOutOfPublic(),
    AUserGrantedOnBothScopesChangesVisibility(),
    AUserGrantedOnTheRegistryButNotPublicMayNotChangeVisibility(),
    AUserGrantedOnPublicButNotTheRegistryMayNotChangeVisibility(),
    AUserGrantedNothingMayNotChangeVisibility(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_setting_global(
    scenario: SettingStep,
    adapter: ContainerRegistryAdapter,
    engine: ExtendedAsyncSAEngine,
) -> None:
    await run_scenario(scenario, adapter, engine)
