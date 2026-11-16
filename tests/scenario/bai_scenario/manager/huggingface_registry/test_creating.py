"""HuggingFace 레지스트리 하나 만들기."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.huggingface_registry.request import (
    CreateHuggingFaceRegistryInput,
)
from ai.backend.common.dto.manager.v2.huggingface_registry.response import (
    CreateHuggingFaceRegistryPayload,
    HuggingFaceRegistryNode,
)
from ai.backend.manager.api.adapters.huggingface_registry.adapter import (
    HuggingFaceRegistryAdapter,
)
from ai.backend.manager.errors.auth import InsufficientPrivilege
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Same,
    Says,
    Scenario,
    Skipped,
    Then,
    Verdict,
    When,
)
from bai_scenario.components.answers import MissingResponse, TheCallIsRefused
from bai_scenario.components.system import ACaller, SomeoneAlone
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

NAME = "made-huggingface"
URL = "https://made.huggingface.example.com"

type CreatingStep = Scenario[
    TestSeedingSession, ACaller, HuggingFaceRegistryAdapter, CreateHuggingFaceRegistryPayload
]


@dataclass(frozen=True)
class Creating(When[ACaller, HuggingFaceRegistryAdapter, CreateHuggingFaceRegistryPayload]):
    @override
    def operation(self) -> str:
        return "create"

    @override
    def describe(self, laid: ACaller) -> str:
        return Says(
            f"{laid.caller.username}이 HuggingFace 레지스트리를 만듭니다",
            english=f"{laid.caller.username} creates a HuggingFace registry",
        )

    @override
    async def call(
        self, adapter: HuggingFaceRegistryAdapter, laid: ACaller
    ) -> CreateHuggingFaceRegistryPayload:
        with ActingAs(laid.caller):
            return await adapter.create(
                CreateHuggingFaceRegistryInput(name=NAME, url=URL, token=None)
            )


@dataclass(frozen=True)
class TheNewRegistryNode(Then[ACaller, CreateHuggingFaceRegistryPayload]):
    @override
    def says(self) -> str:
        return Says(
            "만든 레지스트리 전체가 반환됩니다",
            english="the whole created registry comes back",
        )

    @override
    def look(
        self, laid: ACaller, answered: Answered[CreateHuggingFaceRegistryPayload]
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [MissingResponse(answered.raised)]
        node: HuggingFaceRegistryNode = payload.huggingface_registry
        return [
            Skipped("id", Says("데이터베이스가 생성합니다", english="the database generates it")),
            Skipped(
                "entity_id",
                Says("데이터베이스가 생성합니다", english="the database generates it"),
            ),
            Same("name", node.name, NAME),
            Same("url", node.url, URL),
            Same("token", node.token, None),
        ]


@dataclass(frozen=True)
class TheSuperadminCreates(
    Scenario[
        TestSeedingSession, ACaller, HuggingFaceRegistryAdapter, CreateHuggingFaceRegistryPayload
    ]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-creates-a-huggingface-registry"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 HuggingFace 레지스트리를 만들면 만든 레지스트리 전체가 반환됩니다. 이 "
            "호출은 전역 역할을 검사합니다",
            english=(
                "when the superadmin creates a HuggingFace registry, the whole created registry "
                "comes back. This call is gated by the global role"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ACaller]:
        return SomeoneAlone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ACaller, HuggingFaceRegistryAdapter, CreateHuggingFaceRegistryPayload]:
        return Creating()

    @override
    def then(self) -> Then[ACaller, CreateHuggingFaceRegistryPayload]:
        return TheNewRegistryNode()


@dataclass(frozen=True)
class APlainUserMayNotCreate(
    Scenario[
        TestSeedingSession, ACaller, HuggingFaceRegistryAdapter, CreateHuggingFaceRegistryPayload
    ]
):
    @override
    def summary(self) -> str:
        return "a-user-who-is-not-the-superadmin-may-not-create-a-huggingface-registry"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 아닌 사용자가 HuggingFace 레지스트리를 만들려 하면 권한 부족으로 "
            "거부됩니다. 이 호출은 전역 역할을 검사합니다",
            english=(
                "when a user who is not the superadmin tries to create a HuggingFace registry, "
                "it is rejected for lack of permission. This call is gated by the global role"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ACaller]:
        return SomeoneAlone()

    @override
    def when(self) -> When[ACaller, HuggingFaceRegistryAdapter, CreateHuggingFaceRegistryPayload]:
        return Creating()

    @override
    def then(self) -> Then[ACaller, CreateHuggingFaceRegistryPayload]:
        return TheCallIsRefused(InsufficientPrivilege)


SCENARIOS: list[CreatingStep] = [
    TheSuperadminCreates(),
    APlainUserMayNotCreate(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_creating(
    scenario: CreatingStep,
    adapter: HuggingFaceRegistryAdapter,
    engine: ExtendedAsyncSAEngine,
) -> None:
    await run_scenario(scenario, adapter, engine)
