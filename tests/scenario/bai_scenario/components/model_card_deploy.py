"""What a model card scenario table says about deploying a card and the presets it fits."""

from __future__ import annotations

import string
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Any, override
from uuid import UUID

from ai.backend.common.data.entity.deployment import DeploymentEntityType
from ai.backend.common.data.entity.deployment_preset import DeploymentPresetEntityType
from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.model_deployment.types import DeploymentStrategy
from ai.backend.common.dto.manager.v2.deployment_revision_preset.response import (
    DeploymentRevisionPresetNode,
    SearchDeploymentRevisionPresetsPayload,
)
from ai.backend.common.dto.manager.v2.model_card.response import DeployModelCardPayload
from ai.backend.common.types import ClusterMode, IntrinsicSlotNames
from ai.backend.manager.data.deployment_revision_preset.types import DeploymentRevisionPresetData
from ai.backend.manager.data.model_card.types import ModelCardData
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.data.project.types import ProjectData
from ai.backend.manager.data.resource_group.types import ResourceGroupData
from ai.backend.manager.data.runtime_variant.types import RuntimeVariantData
from ai.backend.manager.data.user.types import UserData
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.deployment_revision_preset.creators import RANK_GAP
from ai.backend.testutils.scenario_steps import (
    Answered,
    Condition,
    Given,
    Held,
    Refused,
    Same,
    SameAs,
    Says,
    Skipped,
    Then,
    Verdict,
)
from bai_scenario.components.answers import MissingResponse
from bai_scenario.components.domain import WAS_HERE, SomeoneOf, WrittenByThisRun
from bai_scenario.components.model_card import CARD_TITLE, SomeoneHandlingCardsIn
from bai_scenario.components.system import SomeoneReadingInPublic
from bai_scenario.components.vfolder import STORAGE_HOST, SomeoneReadingFoldersIn
from bai_scenario.seeds.deployment.revision_preset import (
    TestSeedDeployablePreset,
    TestSeedDeploymentRevisionPreset,
    TestSeedPresetSlotOf,
)
from bai_scenario.seeds.domain.domain import TestSeedDomain
from bai_scenario.seeds.image.image import TestSeedImage
from bai_scenario.seeds.image.registry import TestSeedContainerRegistry
from bai_scenario.seeds.model_card.model_card import TestSeedCardRequirement, TestSeedModelCard
from bai_scenario.seeds.project.project import TestSeedProject
from bai_scenario.seeds.rbac.role import TestSeedPermission, TestSeedRole
from bai_scenario.seeds.resource_group.resource_group import TestSeedResourceGroup
from bai_scenario.seeds.resource_policy.project import TestSeedProjectPolicy
from bai_scenario.seeds.resource_slot.slot_type import TestSeedSlotType
from bai_scenario.seeds.runtime_variant.runtime_variant import TestSeedRuntimeVariant
from bai_scenario.seeds.seeder import Laid, TestSeeder, TestSeedNest
from bai_scenario.seeds.vfolder.vfolder import TestSeedProjectVFolder

SERVED = "served"
CPU = str(IntrinsicSlotNames.CPU.value)
FITTING = "fits"
"""The name hint the preset search filters on. A preset under another hint is filtered out."""


def _names(granted: Sequence[Permission]) -> str:
    return ", ".join(one.name or str(int(one)) for one in granted)


@dataclass(frozen=True)
class SomeoneDeployingIn(TestSeedNest[Laid[None]]):
    """그 프로젝트에서 배포에 주어진 일들을 할 수 있게 된 사용자."""

    project: Laid[ProjectData]
    someone: Laid[UserData]
    permissions: tuple[Permission, ...]

    @override
    def kind(self) -> str:
        return Says("배포 권한 부여", english="Grant deployment permissions")

    @override
    def lay(self, seed: TestSeeder) -> Laid[None]:
        role = seed.creating_from(
            TestSeedRole(lambda p: ProjectID(p.id), name_hint="deployer"), self.project
        )
        for permission in self.permissions:
            seed.adding(
                TestSeedPermission(entity_type=DeploymentEntityType(), permission=permission),
                role,
            )
        return seed.granting(
            role, self.someone, role_id=lambda r: r.id, user_id=lambda u: UserID(u.id)
        )


@dataclass(frozen=True)
class ACardToDeploy:
    """배포할 카드와, 배포가 놓일 자원 그룹과 딛을 프리셋, 그리고 배포하려는 사람."""

    card: ModelCardData
    project: ProjectData
    resource_group: ResourceGroupData
    preset: DeploymentRevisionPresetData
    caller: UserData


@dataclass(frozen=True)
class ACardToDeployAndSomeone(Given[Any, ACardToDeploy]):
    """모델 카드 하나와 그 프리셋, 그리고 그 프로젝트의 사용자 한 명.

    사용자는 카드와 카드의 vfolder 를 읽을 수 있다. 배포 권한은 행이 정한다.
    """

    granted: tuple[Permission, ...] = ()

    @override
    def describe(self) -> str:
        if self.granted:
            names = _names(self.granted)
            grant_ko = f"배포에 {names} 권한을 받은"
            grant_en = f"granted {names} on deployments"
        else:
            grant_ko = "배포 권한은 받지 않은"
            grant_en = "granted no deployment permission"
        return Says(
            "모델 카드 하나가 놓인 프로젝트와 배포할 프리셋, 그리고 그 프로젝트에서 카드와 "
            f"vfolder 를 읽을 수 있고 {grant_ko} 사용자 한 명",
            english=(
                "a project holding one model card and a preset to deploy it on, and one user "
                f"who can read the card and its vfolder in that project and is {grant_en}"
            ),
        )

    @override
    async def lay(self, seeding: Any) -> ACardToDeploy:
        domain = await seeding.creating(
            TestSeedDomain(name_hint="home", description=WAS_HERE, vfolder_hosts=[STORAGE_HOST])
        )
        owner = await seeding.within(SomeoneOf(domain, vfolder_hosts=[STORAGE_HOST]))
        policy = await seeding.once(TestSeedProjectPolicy())
        project = await seeding.creating_from_two(
            TestSeedProject(name_hint="model-store"), domain, policy
        )
        folder = await seeding.creating_from_two(
            TestSeedProjectVFolder(host=STORAGE_HOST), project, owner
        )
        card = await seeding.creating_from_three(
            TestSeedModelCard(title=CARD_TITLE), project, folder, owner
        )
        group = await seeding.creating(TestSeedResourceGroup())
        registry = await seeding.creating(TestSeedContainerRegistry())
        image = await seeding.creating_from(TestSeedImage(), registry)
        runtime = await seeding.creating(TestSeedRuntimeVariant())
        preset = await seeding.creating_from_two(
            TestSeedDeployablePreset(model_name=SERVED), runtime, image
        )
        caller = await seeding.within(SomeoneOf(domain))
        await seeding.within(SomeoneHandlingCardsIn(project, caller, (Permission.READ,)))
        await seeding.within(SomeoneReadingFoldersIn(project, lambda p: ProjectID(p.id), caller))
        if self.granted:
            await seeding.within(SomeoneDeployingIn(project, caller, self.granted))
        return ACardToDeploy(
            card=seeding.made(card),
            project=seeding.made(project),
            resource_group=seeding.made(group),
            preset=seeding.made(preset),
            caller=seeding.made(caller),
        )


@dataclass(frozen=True)
class NamedAfterTheCard(Condition[str]):
    """카드 이름 뒤에 하이픈과 16진수 여덟 자리가 붙은 이름. 뒷부분은 실행마다 다르다."""

    card_name: str

    @override
    def says(self) -> str:
        return Says(
            f"'{self.card_name}-' 뒤에 16진수 여덟 자리가 붙은 이름",
            english=f"'{self.card_name}-' followed by eight hex digits",
        )

    @override
    def holds(self, got: str) -> bool:
        prefix = f"{self.card_name}-"
        if not got.startswith(prefix):
            return False
        suffix = got[len(prefix) :]
        return len(suffix) == 8 and all(c in string.hexdigits for c in suffix)


@dataclass(frozen=True)
class TheCardIsDeployed(Then[ACardToDeploy, DeployModelCardPayload]):
    """카드 이름을 딴 배포가 만들어진다."""

    @override
    def says(self) -> str:
        return Says(
            "카드 이름을 딴 배포가 만들어집니다",
            english="a deployment named after the card is created",
        )

    @override
    def look(
        self, laid: ACardToDeploy, answered: Answered[DeployModelCardPayload]
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [MissingResponse(answered.raised)]
        return [
            Skipped(
                "deployment_id",
                Says("데이터베이스가 만든 id 입니다", english="the database generates it"),
            ),
            Held("deployment_name", payload.deployment_name, NamedAfterTheCard(laid.card.name)),
        ]


@dataclass(frozen=True)
class TheDeployIsRefused(Then[ACardToDeploy, DeployModelCardPayload]):
    """권한이 없다는 이유로 배포하지 못한다."""

    @override
    def says(self) -> str:
        return Says(
            "권한이 없다는 이유로 거부됩니다",
            english="the call is rejected for lack of permission",
        )

    @override
    def look(
        self, laid: ACardToDeploy, answered: Answered[DeployModelCardPayload]
    ) -> list[Verdict]:
        return [Refused(NotEnoughPermission, answered.raised)]


@dataclass(frozen=True)
class PresetsForACard:
    """최소 자원을 요구하는 카드, 그 요구를 채우는 프리셋들, 그리고 프리셋을 찾는 사람.

    ``fitting``은 필터에 걸리는 이름의 프리셋 가운데 요구를 채우는 것들로, 심은 순서다.
    """

    card: ModelCardData
    runtime: RuntimeVariantData
    fitting: tuple[DeploymentRevisionPresetData, ...]
    caller: UserData


@dataclass(frozen=True)
class PresetsForACardAndAReader(Given[Any, PresetsForACard]):
    """cpu 를 2 이상 요구하는 카드와 프리셋 넷, 그리고 프리셋과 카드를 읽을 수 있는 사용자.

    필터에 걸리는 이름의 프리셋 셋 가운데 둘은 요구를 채우고 하나는 모자란다. 나머지 하나는
    요구를 채우지만 다른 이름이다.
    """

    @override
    def describe(self) -> str:
        return Says(
            f"cpu 를 2 이상 요구하는 모델 카드 하나, '{FITTING}' 로 시작하는 이름의 프리셋 셋"
            "(cpu 4, cpu 2, cpu 1), 다른 이름의 cpu 4 프리셋 하나, 그리고 public 에서 프리셋을 "
            "읽고 그 프로젝트에서 카드를 읽을 수 있는 사용자 한 명",
            english=(
                "one model card requiring at least 2 cpu, three presets named starting with "
                f"'{FITTING}' (cpu 4, cpu 2, cpu 1), one cpu 4 preset under another name, and "
                "one user who reads presets in public and the card in that project"
            ),
        )

    @override
    async def lay(self, seeding: Any) -> PresetsForACard:
        domain = await seeding.creating(
            TestSeedDomain(name_hint="home", description=WAS_HERE, vfolder_hosts=[STORAGE_HOST])
        )
        owner = await seeding.within(SomeoneOf(domain, vfolder_hosts=[STORAGE_HOST]))
        policy = await seeding.once(TestSeedProjectPolicy())
        project = await seeding.creating_from_two(
            TestSeedProject(name_hint="model-store"), domain, policy
        )
        folder = await seeding.creating_from_two(
            TestSeedProjectVFolder(host=STORAGE_HOST), project, owner
        )
        await seeding.creating(TestSeedSlotType(IntrinsicSlotNames.CPU))
        card = await seeding.creating_from_three(
            TestSeedModelCard(title=CARD_TITLE), project, folder, owner
        )
        await seeding.adding(TestSeedCardRequirement(slot_name=CPU, min_quantity="2"), card)
        runtime = await seeding.creating(TestSeedRuntimeVariant())
        fitting: list[Laid[DeploymentRevisionPresetData]] = []
        for name_hint, quantity in ((FITTING, "4"), (FITTING, "2"), (FITTING, "1"), ("other", "4")):
            preset = await seeding.creating_from(
                TestSeedDeploymentRevisionPreset(name_hint=name_hint), runtime
            )
            await seeding.adding(TestSeedPresetSlotOf(resource_type=CPU, quantity=quantity), preset)
            if name_hint == FITTING and quantity != "1":
                fitting.append(preset)
        caller = await seeding.within(SomeoneReadingInPublic(domain, DeploymentPresetEntityType()))
        await seeding.within(SomeoneHandlingCardsIn(project, caller, (Permission.READ,)))
        return PresetsForACard(
            card=seeding.made(card),
            runtime=seeding.made(runtime),
            fitting=tuple(seeding.made(preset) for preset in fitting),
            caller=seeding.made(caller),
        )


@dataclass(frozen=True)
class TheLastFittingPresetComesFirst(Then[PresetsForACard, SearchDeploymentRevisionPresetsPayload]):
    """요구를 채우고 필터에 걸리는 프리셋 둘이 세어지고, 이름 역순 첫 쪽에 하나가 온다."""

    started: datetime

    @override
    def says(self) -> str:
        return Says(
            "요구를 채우고 이름이 걸리는 프리셋 둘이 세어지고, 이름 역순 첫 쪽에는 그중 "
            "이름이 늦은 cpu 2 프리셋 하나가 옵니다. 모자란 프리셋과 다른 이름의 프리셋은 "
            "오지 않습니다",
            english=(
                "the two presets meeting the requirement under the filtered name are counted, "
                "and the first page in reverse name order holds the later-named cpu 2 preset. "
                "The preset falling short and the one under another name do not come back"
            ),
        )

    @override
    def look(
        self,
        laid: PresetsForACard,
        answered: Answered[SearchDeploymentRevisionPresetsPayload],
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [MissingResponse(answered.raised)]
        expected = laid.fitting[-1]
        verdicts: list[Verdict] = [
            Same("items count", len(payload.items), 1),
            Same("total_count", payload.total_count, len(laid.fitting)),
            Same("has_next_page", payload.has_next_page, True),
            Same("has_previous_page", payload.has_previous_page, False),
        ]
        for node in payload.items:
            verdicts += _preset_verdicts("items[0].", node, expected, laid.runtime, self.started)
        return verdicts


def _preset_verdicts(
    prefix: str,
    node: DeploymentRevisionPresetNode,
    preset: DeploymentRevisionPresetData,
    runtime: RuntimeVariantData,
    started: datetime,
) -> list[Verdict]:
    seeded = Says("미리 저장한 프리셋", english="the preset created in advance")
    return [
        Held[UUID](f"{prefix}id", node.id, SameAs(preset.id, seeded)),
        Held[UUID](f"{prefix}entity_id", node.entity_id, SameAs(preset.id, seeded)),
        Held[UUID](
            f"{prefix}runtime_variant_id",
            node.runtime_variant_id,
            SameAs(
                runtime.id,
                Says("프리셋의 인퍼런스 런타임 종류", english="the runtime variant of the preset"),
            ),
        ),
        Same(f"{prefix}name", node.name, preset.name),
        Same(f"{prefix}description", node.description, preset.description),
        Same(f"{prefix}rank", node.rank, 2 * RANK_GAP),
        Same(
            f"{prefix}cluster.cluster_mode",
            node.cluster.cluster_mode,
            ClusterMode.SINGLE_NODE.value,
        ),
        Same(f"{prefix}cluster.cluster_size", node.cluster.cluster_size, 1),
        Same(f"{prefix}resource.resource_opts", node.resource.resource_opts, []),
        Same(f"{prefix}execution.image_id", node.execution.image_id, preset.image_id),
        Same(f"{prefix}execution.startup_command", node.execution.startup_command, None),
        Same(f"{prefix}execution.bootstrap_script", node.execution.bootstrap_script, None),
        Same(f"{prefix}execution.environ", node.execution.environ, []),
        Same(
            f"{prefix}deployment_defaults.open_to_public",
            node.deployment_defaults.open_to_public,
            None,
        ),
        Same(
            f"{prefix}deployment_defaults.replica_count",
            node.deployment_defaults.replica_count,
            1,
        ),
        Same(
            f"{prefix}deployment_defaults.revision_history_limit",
            node.deployment_defaults.revision_history_limit,
            None,
        ),
        Same(
            f"{prefix}deployment_defaults.deployment_strategy",
            node.deployment_defaults.deployment_strategy,
            DeploymentStrategy.ROLLING,
        ),
        Same(
            f"{prefix}deployment_defaults.deployment_strategy_spec",
            node.deployment_defaults.deployment_strategy_spec,
            {},
        ),
        Same(f"{prefix}model_definition", node.model_definition, None),
        Same(f"{prefix}preset_values", node.preset_values, []),
        Held(f"{prefix}created_at", node.created_at, WrittenByThisRun(started)),
        Held(f"{prefix}updated_at", node.updated_at, WrittenByThisRun(started)),
    ]
