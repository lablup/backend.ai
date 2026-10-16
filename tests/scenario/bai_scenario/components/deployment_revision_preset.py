"""What a deployment revision preset scenario table says besides the call.

Presets live in public: a plain user only reads them.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override
from uuid import UUID

from ai.backend.common.data.entity.deployment_preset import DeploymentPresetEntityType
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.common import PartialBulkPayload
from ai.backend.common.dto.manager.v2.deployment_revision_preset.response import (
    DeploymentRevisionPresetNode,
)
from ai.backend.manager.data.deployment_revision_preset.types import DeploymentRevisionPresetData
from ai.backend.manager.data.user.types import UserData
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Held,
    Refused,
    Same,
    SameAs,
    Then,
    Verdict,
)
from bai_scenario.components.domain import Mentions
from bai_scenario.components.system import lay_a_public_reader, role_named
from bai_scenario.seeds.deployment.revision_preset import TestSeedDeploymentRevisionPreset
from bai_scenario.seeds.runtime_variant.runtime_variant import TestSeedRuntimeVariant

LAID_DESCRIPTION = "미리 만들어 둔 프리셋"


@dataclass(frozen=True)
class PresetsAndACaller:
    """같은 변형의 프리셋 여럿과, 그것을 부를 사람."""

    presets: tuple[DeploymentRevisionPresetData, ...]
    caller: UserData


@dataclass(frozen=True)
class PresetsAndSomeone(Given[Any, PresetsAndACaller]):
    """변형 하나, 그 변형의 프리셋 여럿, 프리셋을 읽을 수 있는 사용자 한 명."""

    role: UserRole = UserRole.USER
    count: int = 2

    @override
    def describe(self) -> str:
        return (
            f"변형 하나와 그 변형의 배포 리비전 프리셋 {self.count}개, 그리고 "
            f"{role_named(self.role)} 한 명"
        )

    @override
    async def lay(self, seeding: Any) -> PresetsAndACaller:
        variant = await seeding.creating(TestSeedRuntimeVariant())
        presets = [
            await seeding.creating_from(TestSeedDeploymentRevisionPreset(), variant)
            for _ in range(self.count)
        ]
        caller = await lay_a_public_reader(seeding, DeploymentPresetEntityType(), self.role)
        return PresetsAndACaller(
            presets=tuple(seeding.made(preset) for preset in presets),
            caller=seeding.made(caller),
        )


@dataclass(frozen=True)
class EveryPresetComesBack(
    Then[PresetsAndACaller, PartialBulkPayload[DeploymentRevisionPresetNode]]
):
    """프리셋이 모두 처리된 목록에 온다. ``missing``이 있으면 그 id 만 실패 목록에 온다."""

    description: str
    missing: UUID | None = None

    @override
    def says(self) -> str:
        if self.missing is None:
            return f"프리셋이 모두 설명 '{self.description}'으로 오고, 실패한 것은 없다"
        return (
            f"프리셋이 모두 설명 '{self.description}'으로 오고, 없는 id 는 대상이 없다는 "
            "이유로 실패 목록에 온다"
        )

    @override
    def look(
        self,
        laid: PresetsAndACaller,
        answered: Answered[PartialBulkPayload[DeploymentRevisionPresetNode]],
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        verdicts: list[Verdict] = [
            Same("successes count", len(payload.successes), len(laid.presets))
        ]
        for i, (node, preset) in enumerate(zip(payload.successes, laid.presets, strict=False)):
            verdicts += [
                Held[UUID](f"successes[{i}].id", node.id, SameAs(preset.id, "심은 프리셋의 id")),
                Same(f"successes[{i}].description", node.description, self.description),
            ]
        if self.missing is None:
            return [*verdicts, Same("failed", payload.failed, [])]
        verdicts.append(Same("failed count", len(payload.failed), 1))
        for failure in payload.failed:
            verdicts += [
                Held[UUID]("failed[0].id", failure.id, SameAs(self.missing, "요청에 넣은 없는 id")),
                Held("failed[0].message", failure.message, Mentions("not found")),
            ]
        return verdicts


@dataclass(frozen=True)
class NoPresetIsProcessed(
    Then[PresetsAndACaller, PartialBulkPayload[DeploymentRevisionPresetNode]]
):
    """처리된 프리셋 없이, 프리셋이 모두 같은 이유로 실패 목록에 온다."""

    reason: str

    @override
    def says(self) -> str:
        return "처리된 프리셋 없이 프리셋이 모두 실패 목록에 온다"

    @override
    def look(
        self,
        laid: PresetsAndACaller,
        answered: Answered[PartialBulkPayload[DeploymentRevisionPresetNode]],
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        verdicts: list[Verdict] = [
            Same("successes", payload.successes, []),
            Same("failed count", len(payload.failed), len(laid.presets)),
        ]
        for i, (failure, preset) in enumerate(zip(payload.failed, laid.presets, strict=False)):
            verdicts += [
                Held[UUID](f"failed[{i}].id", failure.id, SameAs(preset.id, "심은 프리셋의 id")),
                Held(f"failed[{i}].message", failure.message, Mentions(self.reason)),
            ]
        return verdicts
