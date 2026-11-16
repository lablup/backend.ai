"""배포 리비전 프리셋 만들기."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override
from uuid import UUID

import pytest

from ai.backend.common.data.entity.image import ImageID
from ai.backend.common.data.entity.runtime_variant import RuntimeVariantID
from ai.backend.common.data.model_deployment.types import DeploymentStrategy
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.deployment.request import DeploymentStrategyInput
from ai.backend.common.dto.manager.v2.deployment_revision_preset.request import (
    CreateDeploymentRevisionPresetInput,
)
from ai.backend.common.dto.manager.v2.deployment_revision_preset.response import (
    CreateDeploymentRevisionPresetPayload,
)
from ai.backend.manager.api.adapters.deployment_revision_preset.adapter import (
    DeploymentRevisionPresetAdapter,
)
from ai.backend.manager.errors.auth import InsufficientPrivilege
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Answered,
    Condition,
    Given,
    Held,
    Same,
    SameAs,
    Says,
    Scenario,
    Skipped,
    Then,
    Verdict,
    When,
)
from bai_scenario.components.answers import MissingResponse, TheCallIsRefused
from bai_scenario.components.deployment_revision_preset import (
    AVariantAndACaller,
    AVariantAndSomeoneToCreate,
    TheImageIdThePresetKept,
)
from bai_scenario.components.domain import WrittenByThisRun
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type Answer = CreateDeploymentRevisionPresetPayload
type CreateStep = Scenario[
    TestSeedingSession, AVariantAndACaller, DeploymentRevisionPresetAdapter, Answer
]


@dataclass(frozen=True)
class TheRankTheDatabaseComputed(Condition[int]):
    """프리셋 순위는 요청이 정하지 않는다. 값 자체는 실행마다 달라 조건으로 본다."""

    @override
    def says(self) -> str:
        return Says("순위가 매겨진 값", english="a ranked value")

    @override
    def holds(self, got: int) -> bool:
        return got >= 0


@dataclass(frozen=True)
class CreatingAPreset(When[AVariantAndACaller, DeploymentRevisionPresetAdapter, Answer]):
    """프리셋 하나를 만든다."""

    @override
    def operation(self) -> str:
        return "create"

    @override
    def describe(self, laid: AVariantAndACaller) -> str:
        return Says(
            f"{laid.caller.username} 이 변형으로 프리셋 하나를 만듭니다",
            english=f"{laid.caller.username} makes one preset of the runtime variant",
        )

    @override
    async def call(
        self, adapter: DeploymentRevisionPresetAdapter, laid: AVariantAndACaller
    ) -> Answer:
        with ActingAs(laid.caller):
            return await adapter.create(
                CreateDeploymentRevisionPresetInput(
                    runtime_variant_id=RuntimeVariantID(laid.variant.id),
                    name="created-preset",
                    description="a preset made by this run",
                    image_id=ImageID(UUID(int=7)),
                    cluster_mode="single-node",
                    cluster_size=1,
                    replica_count=1,
                    deployment_strategy=DeploymentStrategyInput(type=DeploymentStrategy.ROLLING),
                )
            )


@dataclass(frozen=True)
class TheCreatedPresetComesBack(Then[AVariantAndACaller, Answer]):
    """만든 프리셋이 통째로 온다."""

    started: datetime

    @override
    def says(self) -> str:
        return Says(
            "만든 프리셋이 전체가 응답으로 옵니다", english="the whole preset made comes back"
        )

    @override
    def look(self, laid: AVariantAndACaller, answered: Answered[Answer]) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [MissingResponse(answered.raised)]
        node = payload.preset
        written = WrittenByThisRun(self.started)
        return [
            Skipped("preset.id", "the database generates it"),
            Skipped("preset.entity_id", "the database generates it"),
            Held[UUID](
                "preset.runtime_variant_id",
                node.runtime_variant_id,
                SameAs(
                    laid.variant.id,
                    Says("프리셋이 놓인 변형의 id", english="the id of the variant laid before"),
                ),
            ),
            Same("preset.name", node.name, "created-preset"),
            Same("preset.description", node.description, "a preset made by this run"),
            Held("preset.rank", node.rank, TheRankTheDatabaseComputed()),
            Same("preset.cluster.cluster_mode", node.cluster.cluster_mode, "single-node"),
            Same("preset.cluster.cluster_size", node.cluster.cluster_size, 1),
            Same("preset.resource.resource_opts", node.resource.resource_opts, []),
            Held(
                "preset.execution.image_id",
                node.execution.image_id,
                TheImageIdThePresetKept(image_id=ImageID(UUID(int=7))),
            ),
            Same("preset.execution.startup_command", node.execution.startup_command, None),
            Same("preset.execution.bootstrap_script", node.execution.bootstrap_script, None),
            Same("preset.execution.environ", node.execution.environ, []),
            Same(
                "preset.deployment_defaults.open_to_public",
                node.deployment_defaults.open_to_public,
                None,
            ),
            Same(
                "preset.deployment_defaults.replica_count",
                node.deployment_defaults.replica_count,
                1,
            ),
            Same(
                "preset.deployment_defaults.revision_history_limit",
                node.deployment_defaults.revision_history_limit,
                None,
            ),
            Same(
                "preset.deployment_defaults.deployment_strategy",
                node.deployment_defaults.deployment_strategy,
                DeploymentStrategy.ROLLING,
            ),
            Same(
                "preset.deployment_defaults.deployment_strategy_spec",
                node.deployment_defaults.deployment_strategy_spec,
                {},
            ),
            Same("preset.model_definition", node.model_definition, None),
            Same("preset.preset_values", node.preset_values, []),
            Held("preset.created_at", node.created_at, written),
            Held("preset.updated_at", node.updated_at, written),
        ]


@dataclass(frozen=True)
class TheSuperadminMakesAPreset(
    Scenario[TestSeedingSession, AVariantAndACaller, DeploymentRevisionPresetAdapter, Answer]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "the-superadmin-makes-a-preset"

    @override
    def describe(self) -> str:
        return Says(
            "전역 권한으로만 만들 수 있는 프리셋을 superadmin 이 만들면, 만든 프리셋이 옵니다. "
            "이 행의 요청 사용자는 전역 권한이 필요한 호출이라 superadmin 입니다",
            english=(
                "when the superadmin makes a preset, an operation gated by the global role, "
                "the preset made comes back. The requesting user of this row is the superadmin "
                "because the call is gated by the global role"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AVariantAndACaller]:
        return AVariantAndSomeoneToCreate(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[AVariantAndACaller, DeploymentRevisionPresetAdapter, Answer]:
        return CreatingAPreset()

    @override
    def then(self) -> Then[AVariantAndACaller, Answer]:
        return TheCreatedPresetComesBack(started=self.started)


@dataclass(frozen=True)
class APresetReaderMakesNoPreset(
    Scenario[TestSeedingSession, AVariantAndACaller, DeploymentRevisionPresetAdapter, Answer]
):
    @override
    def summary(self) -> str:
        return "a-preset-reader-makes-no-preset"

    @override
    def describe(self) -> str:
        return Says(
            "프리셋 조회 권한만 받은 사용자가 프리셋을 만들려 하면, 전역 권한이 없다는 이유로 "
            "거부됩니다",
            english=(
                "when a user granted only preset read tries to make a preset, the create is "
                "rejected because the user lacks the global role"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AVariantAndACaller]:
        return AVariantAndSomeoneToCreate(role=UserRole.USER)

    @override
    def when(self) -> When[AVariantAndACaller, DeploymentRevisionPresetAdapter, Answer]:
        return CreatingAPreset()

    @override
    def then(self) -> Then[AVariantAndACaller, Answer]:
        return TheCallIsRefused(InsufficientPrivilege)


STARTED = datetime.now(UTC)

SCENARIOS: list[CreateStep] = [
    TheSuperadminMakesAPreset(started=STARTED),
    APresetReaderMakesNoPreset(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_creating(
    scenario: CreateStep,
    adapter: DeploymentRevisionPresetAdapter,
    engine: ExtendedAsyncSAEngine,
) -> None:
    await run_scenario(scenario, adapter, engine)
