"""What a deployment revision preset scenario table says besides the call.

Presets live in public: a plain user only reads them.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, override
from uuid import UUID

from ai.backend.common.data.entity.deployment_preset import DeploymentPresetEntityType
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.common import PartialBulkPayload
from ai.backend.common.dto.manager.v2.deployment_revision_preset.response import (
    DeploymentRevisionPresetNode,
)
from ai.backend.manager.data.deployment_revision_preset.types import DeploymentRevisionPresetData
from ai.backend.manager.data.runtime_variant.types import RuntimeVariantData
from ai.backend.manager.data.user.types import UserData
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Held,
    Language,
    Refused,
    Same,
    SameAs,
    Says,
    Then,
    Verdict,
    in_language,
)
from bai_scenario.components.domain import Mentions
from bai_scenario.components.system import lay_a_caller, lay_a_public_reader, role_named
from bai_scenario.seeds.deployment.revision_preset import TestSeedDeploymentRevisionPreset
from bai_scenario.seeds.runtime_variant.runtime_variant import TestSeedRuntimeVariant

LAID_DESCRIPTION = Says("미리 저장한 프리셋", english="a preset seeded in advance")

PRESET_ID = Says("미리 저장한 프리셋의 id", english="the id of the preset seeded in advance")
VARIANT_ID = Says(
    "프리셋이 놓인 변형의 id", english="the id of the runtime variant the preset is laid on"
)
PRESET_CREATED_AT = Says(
    "미리 저장한 프리셋이 만들어진 시각", english="the time the preset seeded in advance was made"
)


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
        who = role_named(self.role)
        return Says(
            f"변형 하나와 그 변형의 배포 리비전 프리셋 {self.count}개, 그리고 {who} 한 명",
            english=(
                f"one runtime variant and {self.count} deployment revision presets of it, "
                f"and one {in_language(who, Language.ENGLISH)}"
            ),
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
class PresetsAndAnOutsider(Given[Any, PresetsAndACaller]):
    """변형 하나, 그 변형의 프리셋 여럿, 프리셋을 읽을 권한이 없는 사용자 한 명."""

    role: UserRole = UserRole.USER
    count: int = 2

    @override
    def describe(self) -> str:
        who = role_named(self.role)
        return Says(
            f"변형 하나와 그 변형의 배포 리비전 프리셋 {self.count}개, 그리고 프리셋을 읽을 "
            f"권한이 없는 {who} 한 명",
            english=(
                f"one runtime variant and {self.count} deployment revision presets of it, "
                f"and one {in_language(who, Language.ENGLISH)} granted nothing on presets"
            ),
        )

    @override
    async def lay(self, seeding: Any) -> PresetsAndACaller:
        variant = await seeding.creating(TestSeedRuntimeVariant())
        presets = [
            await seeding.creating_from(TestSeedDeploymentRevisionPreset(), variant)
            for _ in range(self.count)
        ]
        caller = await lay_a_caller(seeding, self.role)
        return PresetsAndACaller(
            presets=tuple(seeding.made(preset) for preset in presets),
            caller=seeding.made(caller),
        )


@dataclass(frozen=True)
class AVariantAndACaller:
    """변형 하나와, 그것으로 프리셋을 만들 사람."""

    variant: RuntimeVariantData
    caller: UserData


@dataclass(frozen=True)
class AVariantAndSomeoneToCreate(Given[Any, AVariantAndACaller]):
    """변형 하나와, 그것으로 프리셋을 만들 사용자 한 명."""

    role: UserRole = UserRole.USER

    @override
    def describe(self) -> str:
        who = role_named(self.role)
        return Says(
            f"변형 하나와 그것으로 프리셋을 만들 {who} 한 명",
            english=f"one runtime variant and one {in_language(who, Language.ENGLISH)} to make a preset of it",
        )

    @override
    async def lay(self, seeding: Any) -> AVariantAndACaller:
        variant = await seeding.creating(TestSeedRuntimeVariant())
        caller = await lay_a_public_reader(seeding, DeploymentPresetEntityType(), self.role)
        return AVariantAndACaller(
            variant=seeding.made(variant),
            caller=seeding.made(caller),
        )


@dataclass(frozen=True)
class ThePresetNode:
    """미리 저장한 프리셋의 노드가 어떤 값으로 와야 하는지. 이름은 미리 저장한 것에서 읽는다."""

    started: datetime
    described: str | None = None

    def verdicts(
        self, node: DeploymentRevisionPresetNode, laid: DeploymentRevisionPresetData, at: str = ""
    ) -> list[Verdict]:
        described = self.described if self.described is not None else laid.description
        return [
            Held[UUID](f"{at}id", node.id, SameAs(laid.id, PRESET_ID)),
            Held[UUID](f"{at}entity_id", node.entity_id, SameAs(laid.id, PRESET_ID)),
            Held(f"{at}runtime_variant_id", node.runtime_variant_id, SameAs(laid.runtime_variant_id, VARIANT_ID)),
            Same(f"{at}name", node.name, laid.name),
            Same(f"{at}description", node.description, described),
            Same(f"{at}rank", node.rank, laid.rank),
            Same(f"{at}cluster.cluster_mode", node.cluster.cluster_mode, laid.cluster_mode),
            Same(f"{at}cluster.cluster_size", node.cluster.cluster_size, laid.cluster_size),
            Same(f"{at}resource.resource_opts", node.resource.resource_opts, laid.resource_opts),
            Held(
                f"{at}execution.image_id",
                node.execution.image_id,
                SameAs(
                    laid.image_id,
                    Says(
                        "미리 정한 이미지 id",
                        english="the image id fixed in advance",
                    ),
                ),
            ),
            Same(f"{at}execution.startup_command", node.execution.startup_command, laid.startup_command),
            Same(f"{at}execution.bootstrap_script", node.execution.bootstrap_script, laid.bootstrap_script),
            Same(f"{at}execution.environ", node.execution.environ, laid.environ),
            Same(
                f"{at}deployment_defaults.open_to_public",
                node.deployment_defaults.open_to_public,
                laid.open_to_public,
            ),
            Same(
                f"{at}deployment_defaults.replica_count",
                node.deployment_defaults.replica_count,
                laid.replica_count,
            ),
            Same(
                f"{at}deployment_defaults.revision_history_limit",
                node.deployment_defaults.revision_history_limit,
                laid.revision_history_limit,
            ),
            Same(
                f"{at}deployment_defaults.deployment_strategy",
                node.deployment_defaults.deployment_strategy,
                laid.deployment_strategy,
            ),
            Same(
                f"{at}deployment_defaults.deployment_strategy_spec",
                node.deployment_defaults.deployment_strategy_spec,
                laid.deployment_strategy_spec,
            ),
            Same(f"{at}model_definition", node.model_definition, laid.model_definition),
            Same(f"{at}preset_values", node.preset_values, laid.runtime_variant_preset_values),
            Held(f"{at}created_at", node.created_at, SameAs(laid.created_at, PRESET_CREATED_AT)),
            Held(f"{at}updated_at", node.updated_at, SameAs(laid.updated_at, PRESET_CREATED_AT)),
        ]


@dataclass(frozen=True)
class EveryPresetComesBack(
    Then[PresetsAndACaller, PartialBulkPayload[DeploymentRevisionPresetNode]]
):
    """프리셋이 모두 처리된 목록에 온다. ``missing``이 있으면 그 id 만 실패 목록에 온다."""

    description: str
    missing: UUID | None = None

    @override
    def says(self) -> str:
        described = in_language(self.description, Language.ENGLISH)
        if self.missing is None:
            return Says(
                f"프리셋이 모두 설명 '{self.description}'으로 오고, 실패한 것은 없습니다",
                english=(
                    f"every preset comes back with the description '{described}' and nothing failed"
                ),
            )
        return Says(
            f"프리셋이 모두 설명 '{self.description}'으로 오고, 없는 id 는 대상이 없다는 "
            "이유로 실패 목록에 옵니다",
            english=(
                f"every preset comes back with the description '{described}' and an unknown id "
                "comes back in the failed list because no target answers to it"
            ),
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
                Held[UUID](
                    f"successes[{i}].id",
                    node.id,
                    SameAs(
                        preset.id,
                        Says(
                            "미리 저장한 프리셋의 id",
                            english="the id of the preset seeded in advance",
                        ),
                    ),
                ),
                Same(f"successes[{i}].description", node.description, self.description),
            ]
        if self.missing is None:
            return [*verdicts, Same("failed", payload.failed, [])]
        verdicts.append(Same("failed count", len(payload.failed), 1))
        for failure in payload.failed:
            verdicts += [
                Held[UUID](
                    "failed[0].id",
                    failure.id,
                    SameAs(
                        self.missing,
                        Says("요청에 넣은 없는 id", english="the unknown id put in the request"),
                    ),
                ),
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
        return Says(
            "처리된 프리셋 없이 프리셋이 모두 실패 목록에 옵니다",
            english="no preset is processed and every preset comes back in the failed list",
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
            Same("successes", payload.successes, []),
            Same("failed count", len(payload.failed), len(laid.presets)),
        ]
        for i, (failure, preset) in enumerate(zip(payload.failed, laid.presets, strict=False)):
            verdicts += [
                Held[UUID](
                    f"failed[{i}].id",
                    failure.id,
                    SameAs(
                        preset.id,
                        Says(
                            "미리 저장한 프리셋의 id",
                            english="the id of the preset seeded in advance",
                        ),
                    ),
                ),
                Held(f"failed[{i}].message", failure.message, Mentions(self.reason)),
            ]
        return verdicts
