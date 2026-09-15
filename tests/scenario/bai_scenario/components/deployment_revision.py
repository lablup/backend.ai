"""What a revision scenario table says besides the call.

A revision is a row a deployment owns, so every table lays a deployment first and
authorizes through it. A revision also stands on an image, a model folder, a runtime
variant and the slot types it allocates; those are laid together. The model folder is
the caller's own, and whether the caller may read it is the row's to say: the mount is
granted from those bits, and no role passes over them.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any, override
from uuid import UUID

from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.deployment.response import (
    AdminSearchRevisionsPayload,
    RevisionNode,
)
from ai.backend.common.dto.manager.v2.deployment.types import (
    ClusterConfigInfoDTO,
    ModelConfigInfoDTO,
    ModelDefinitionInfoDTO,
)
from ai.backend.common.dto.manager.v2.resource_slot.response import (
    SearchAllocatedResourceSlotsPayload,
)
from ai.backend.common.types import ClusterMode, IntrinsicSlotNames
from ai.backend.manager.data.deployment.types import DeploymentInfo, ModelRevisionData
from ai.backend.manager.data.image.types import ImageData
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.data.runtime_variant.types import RuntimeVariantData
from ai.backend.manager.data.user.types import UserData
from ai.backend.manager.data.vfolder.types import VFolderData
from ai.backend.manager.errors.base.entity import EntityNotFoundError
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Held,
    Refused,
    Same,
    SameAs,
    Skipped,
    Then,
    Verdict,
)
from bai_scenario.components.deployment import (
    APlaceAndACaller,
    LaidPlace,
    lay_a_deployment,
    lay_a_place,
)
from bai_scenario.components.domain import SomeoneOf, WrittenByThisRun
from bai_scenario.components.vfolder import STORAGE_HOST, SomeoneReadingFoldersIn
from bai_scenario.seeds.deployment.revision import SeedRevisionOf
from bai_scenario.seeds.image.image import SeedImage
from bai_scenario.seeds.image.registry import SeedContainerRegistry
from bai_scenario.seeds.project.project import SeedProject
from bai_scenario.seeds.resource_policy.project import SeedProjectPolicy
from bai_scenario.seeds.resource_slot.slot_type import SeedSlotType
from bai_scenario.seeds.runtime_variant.runtime_variant import SeedRuntimeVariant
from bai_scenario.seeds.seeder import Laid, Seeder, SeedNest
from bai_scenario.seeds.vfolder.vfolder import SeedPersonalVFolder

MOUNTED_AT = "/models"
SERVED = "served"
SLOTS: tuple[tuple[str, Decimal], ...] = (
    (str(IntrinsicSlotNames.CPU.value), Decimal("1")),
    (str(IntrinsicSlotNames.MEMORY.value), Decimal("1073741824")),
)
"""What every revision a table lays or asks for allocates, unless the row says otherwise."""

type Loaded = list[RevisionNode | Exception | None]


def _names(granted: Sequence[Permission]) -> str:
    return ", ".join(one.name or str(int(one)) for one in granted)


@dataclass(frozen=True)
class RevisionsAndACaller:
    """리비전을 더하거나 읽을 배포와, 그것을 부를 사람.

    ``revisions``는 그 배포에 심은 리비전, ``elsewhere``는 다른 프로젝트의 배포에 심은
    리비전이다. 이미지, 모델 폴더, 런타임 변형은 리비전이 딛는 것이다.
    """

    place: APlaceAndACaller
    deployment: DeploymentInfo
    image: ImageData
    folder: VFolderData
    runtime: RuntimeVariantData
    revisions: tuple[ModelRevisionData, ...] = ()
    elsewhere: tuple[ModelRevisionData, ...] = ()

    @property
    def caller(self) -> UserData:
        return self.place.caller


@dataclass(frozen=True)
class LaidMaterials:
    """리비전이 딛는 행들의 손잡이."""

    image: Laid[ImageData]
    folder: Laid[VFolderData]
    runtime: Laid[RuntimeVariantData]


@dataclass(frozen=True)
class WhatARevisionStandsOn(SeedNest[LaidMaterials]):
    """리비전이 딛는 이미지, 모델 폴더, 런타임 변형, 자원 슬롯 타입.

    모델 폴더는 ``folder_owner``의 개인 폴더다. ``folder_readable``이면 그 사람이 자기 개인
    프로젝트에서 폴더를 읽을 수 있고, 마운트는 읽기 전용으로 잡힌다. 슬롯 타입은 리비전의
    슬롯 행이 가리키므로 함께 심는다.
    """

    folder_owner: Laid[UserData]
    folder_readable: bool = True
    cpu_required: bool = False

    @override
    def kind(self) -> str:
        return "리비전이 딛는 이미지, 모델 폴더, 런타임 변형, 자원 슬롯 타입 준비"

    @override
    def lay(self, seed: Seeder) -> LaidMaterials:
        registry = seed.creating(SeedContainerRegistry())
        image = seed.creating_from(SeedImage(), registry)
        folder = seed.creating_from(SeedPersonalVFolder(host=STORAGE_HOST), self.folder_owner)
        if self.folder_readable:
            own = seed.personal_project_of(self.folder_owner)
            seed.within(SomeoneReadingFoldersIn(own, lambda p: ProjectID(p.id), self.folder_owner))
        runtime = seed.creating(SeedRuntimeVariant())
        seed.creating(SeedSlotType(IntrinsicSlotNames.CPU, required=self.cpu_required))
        seed.creating(SeedSlotType(IntrinsicSlotNames.MEMORY))
        return LaidMaterials(image=image, folder=folder, runtime=runtime)


async def lay_revisions(
    seeding: Any,
    place: LaidPlace,
    deployment: Laid[DeploymentInfo],
    materials: LaidMaterials,
    count: int,
) -> tuple[ModelRevisionData, ...]:
    """그 배포에 리비전을 ``count``개 심는다. 번호는 1부터 차례로 붙는다."""
    image = seeding.made(materials.image)
    folder = seeding.made(materials.folder)
    runtime = seeding.made(materials.runtime)
    group = seeding.made(place.resource_group)
    made: list[ModelRevisionData] = []
    for _ in range(count):
        laid = await seeding.adding(
            SeedRevisionOf(
                image_id=image.id,
                folder_id=folder.id,
                runtime_variant_id=runtime.id,
                resource_group=group.name,
                slots=SLOTS,
                model_name=SERVED,
                mounted_at=MOUNTED_AT,
            ),
            deployment,
        )
        made.append(seeding.made(laid))
    return tuple(made)


def _revisions_and_a_caller(
    seeding: Any,
    place: LaidPlace,
    deployment: Laid[DeploymentInfo],
    materials: LaidMaterials,
    revisions: tuple[ModelRevisionData, ...] = (),
    elsewhere: tuple[ModelRevisionData, ...] = (),
) -> RevisionsAndACaller:
    return RevisionsAndACaller(
        place=place.made(seeding),
        deployment=seeding.made(deployment),
        image=seeding.made(materials.image),
        folder=seeding.made(materials.folder),
        runtime=seeding.made(materials.runtime),
        revisions=revisions,
        elsewhere=elsewhere,
    )


@dataclass(frozen=True)
class ADeploymentToRevise(Given[Any, RevisionsAndACaller]):
    """배포 하나와 거기 딸린 리비전들, 그리고 그 프로젝트 안의 사용자 한 명.

    모델 폴더는 부르는 사람의 것이고, 부르는 사람은 그 폴더를 읽을 수만 있다.
    """

    granted: tuple[Permission, ...] = ()
    role: UserRole = UserRole.USER
    revisions: int = 0
    cpu_required: bool = False

    @override
    def describe(self) -> str:
        who = (
            f"배포에 {_names(self.granted)} 권한을 받은 사용자 한 명"
            if self.granted
            else "아무 배포 권한도 받지 않은 사용자 한 명"
        )
        return (
            f"리비전 {self.revisions}개가 딸린 배포 하나와, 자기 모델 폴더를 읽을 수만 있는 {who}"
        )

    @override
    async def lay(self, seeding: Any) -> RevisionsAndACaller:
        place = await lay_a_place(seeding, granted=self.granted, role=self.role)
        deployment = await lay_a_deployment(seeding, place)
        materials = await seeding.within(
            WhatARevisionStandsOn(place.caller, cpu_required=self.cpu_required)
        )
        made = await lay_revisions(seeding, place, deployment, materials, self.revisions)
        return _revisions_and_a_caller(seeding, place, deployment, materials, made)


@dataclass(frozen=True)
class AnothersDeploymentToRevise(Given[Any, RevisionsAndACaller]):
    """다른 사람이 만든 리비전 없는 배포와, 배포 권한을 받지 않은 슈퍼관리자.

    모델 폴더는 슈퍼관리자 자신의 것이다. ``folder_readable``이 거짓이면 그 폴더를 읽을
    권한이 없다. 폴더 마운트에는 역할이 지나가지 않는지 보는 자리다.
    """

    folder_readable: bool = True

    @override
    def describe(self) -> str:
        folder = "읽을 수 있는" if self.folder_readable else "읽을 권한이 없는"
        return (
            f"다른 사람이 만든 배포 하나와, 배포 권한은 없고 자기 모델 폴더를 {folder} 슈퍼관리자"
        )

    @override
    async def lay(self, seeding: Any) -> RevisionsAndACaller:
        place = await lay_a_place(seeding, role=UserRole.SUPERADMIN)
        other = await seeding.within(SomeoneOf(place.domain))
        theirs = LaidPlace(
            domain=place.domain,
            project=place.project,
            resource_group=place.resource_group,
            caller=other,
        )
        deployment = await lay_a_deployment(seeding, theirs, name_hint="theirs")
        materials = await seeding.within(
            WhatARevisionStandsOn(place.caller, folder_readable=self.folder_readable)
        )
        return _revisions_and_a_caller(seeding, place, deployment, materials)


@dataclass(frozen=True)
class RevisionsInTwoProjects(Given[Any, RevisionsAndACaller]):
    """두 프로젝트의 배포에 나뉜 리비전과, 한쪽 프로젝트에만 권한을 받은 사용자.

    부를 배포는 권한을 받은 프로젝트의 것이다. 다른 프로젝트의 배포에 심은 리비전은
    ``elsewhere``로 답한다.
    """

    granted: tuple[Permission, ...] = ()
    role: UserRole = UserRole.USER
    named: int = 1
    elsewhere: int = 1

    @override
    def describe(self) -> str:
        who = (
            f"한쪽 프로젝트에서만 배포에 {_names(self.granted)} 권한을 받은 사용자 한 명"
            if self.granted
            else "아무 배포 권한도 받지 않은 사용자 한 명"
        )
        return (
            f"두 프로젝트의 배포에 리비전 {self.named}개와 {self.elsewhere}개가 나뉘어 있고, {who}"
        )

    @override
    async def lay(self, seeding: Any) -> RevisionsAndACaller:
        place = await lay_a_place(seeding, granted=self.granted, role=self.role)
        policy = await seeding.once(SeedProjectPolicy())
        other = await seeding.creating_from_two(
            SeedProject(name_hint="other"), place.domain, policy
        )
        beside = LaidPlace(
            domain=place.domain,
            project=other,
            resource_group=place.resource_group,
            caller=place.caller,
        )
        wanted = await lay_a_deployment(seeding, place, name_hint="wanted")
        elsewhere = await lay_a_deployment(seeding, beside, name_hint="elsewhere")
        materials = await seeding.within(WhatARevisionStandsOn(place.caller))
        named = await lay_revisions(seeding, place, wanted, materials, self.named)
        others = await lay_revisions(seeding, beside, elsewhere, materials, self.elsewhere)
        return _revisions_and_a_caller(seeding, place, wanted, materials, named, others)


def revision_verdicts(
    at: str,
    node: RevisionNode,
    laid: RevisionsAndACaller,
    *,
    started: datetime,
    number: int,
    slots: tuple[tuple[str, Decimal], ...],
    seeded: ModelRevisionData | None,
) -> list[Verdict]:
    """리비전 노드 한 개의 자리를 모두 본다. ``at``은 자리 이름 앞에 붙는다."""
    mount = node.model_mount_config
    runtime = node.model_runtime_config
    resources = node.resource_config
    identity: Verdict = (
        Held(f"{at}id", node.id, SameAs[UUID](seeded.id, "심은 리비전"))
        if seeded is not None
        else Skipped(f"{at}id", "데이터베이스가 만든다")
    )
    return [
        identity,
        Held(
            f"{at}deployment_id", node.deployment_id, SameAs[UUID](laid.deployment.id, "심은 배포")
        ),
        Same(f"{at}revision_number", node.revision_number, number),
        Held(f"{at}image_id", node.image_id, SameAs[UUID | None](laid.image.id, "심은 이미지")),
        Same(
            f"{at}cluster_config",
            node.cluster_config,
            ClusterConfigInfoDTO(mode=ClusterMode.SINGLE_NODE.name, size=1),
        ),
        Same(
            f"{at}resource_config.resource_group_name",
            resources.resource_group_name,
            laid.place.resource_group.name,
        ),
        Same(
            f"{at}resource_config.resource_slots",
            sorted((e.resource_type, e.quantity) for e in resources.resource_slots.entries),
            sorted(slots),
        ),
        Same(f"{at}resource_config.resource_opts", resources.resource_opts, None),
        Held(
            f"{at}model_runtime_config.runtime_variant_id",
            runtime.runtime_variant_id,
            SameAs[UUID](laid.runtime.id, "심은 런타임 변형"),
        ),
        Same(
            f"{at}model_runtime_config.inference_runtime_config",
            runtime.inference_runtime_config,
            None,
        ),
        Same(f"{at}model_runtime_config.environ", runtime.environ, None),
        Same(
            f"{at}model_runtime_config.runtime_variant_preset_values",
            runtime.runtime_variant_preset_values,
            [],
        ),
        Held(
            f"{at}model_mount_config.vfolder_id",
            mount.vfolder_id if mount is not None else None,
            SameAs[str | None](str(laid.folder.id), "심은 모델 폴더"),
        ),
        Same(
            f"{at}model_mount_config.mount_destination",
            mount.mount_destination if mount is not None else None,
            MOUNTED_AT,
        ),
        Same(
            f"{at}model_mount_config.definition_path",
            mount.definition_path if mount is not None else None,
            "",
        ),
        Same(f"{at}model_mount_config.subpath", mount.subpath if mount is not None else None, None),
        Same(
            f"{at}model_definition",
            node.model_definition,
            ModelDefinitionInfoDTO(
                models=[
                    ModelConfigInfoDTO(
                        name=SERVED, model_path=MOUNTED_AT, service=None, metadata=None
                    )
                ]
            ),
        ),
        Held(f"{at}created_at", node.created_at, WrittenByThisRun(started)),
        Same(f"{at}extra_mounts", node.extra_mounts, []),
        Same(f"{at}revision_preset_id", node.revision_preset_id, None),
    ]


@dataclass(frozen=True)
class TheRevisionNode(Then[RevisionsAndACaller, RevisionNode]):
    """리비전 하나가 통째로 온다.

    ``seeded``를 대면 심은 리비전 중 그 차례의 것이어야 한다. 대지 않으면 방금 더한
    것이다.
    """

    started: datetime
    number: int
    slots: tuple[tuple[str, Decimal], ...] = SLOTS
    seeded: int | None = None

    @override
    def says(self) -> str:
        return "리비전 전체가 온다"

    @override
    def look(self, laid: RevisionsAndACaller, answered: Answered[RevisionNode]) -> list[Verdict]:
        node = answered.response
        if node is None:
            return [Refused(EntityNotFoundError, answered.raised)]
        return revision_verdicts(
            "",
            node,
            laid,
            started=self.started,
            number=self.number,
            slots=self.slots,
            seeded=laid.revisions[self.seeded] if self.seeded is not None else None,
        )


@dataclass(frozen=True)
class EachNamedRevisionIsAnswered(Then[RevisionsAndACaller, Loaded]):
    """읽을 수 있는 것, 볼 수 없는 것, 없는 것을 차례로 이름 댄 답.

    읽을 수 있는 것은 리비전으로, 볼 수 없는 것은 거부로, 없는 것은 빈 자리로 온다.
    """

    started: datetime

    @override
    def says(self) -> str:
        return "이름 댄 순서대로 리비전, 거부, 빈 자리가 온다"

    @override
    def look(self, laid: RevisionsAndACaller, answered: Answered[Loaded]) -> list[Verdict]:
        items = answered.response
        if items is None:
            return [Refused(EntityNotFoundError, answered.raised)]
        seen: list[Verdict] = [Same("len", len(items), 3)]
        if len(items) != 3:
            return seen
        readable, hidden, missing = items
        if isinstance(readable, RevisionNode):
            seen.extend(
                revision_verdicts(
                    "[0].",
                    readable,
                    laid,
                    started=self.started,
                    number=1,
                    slots=SLOTS,
                    seeded=laid.revisions[0],
                )
            )
        else:
            seen.append(Same("[0]", type(readable).__name__, RevisionNode.__name__))
        seen.append(Same("[1]", type(hidden).__name__, NotEnoughPermission.__name__))
        seen.append(Same("[2]", missing, None))
        return seen


@dataclass(frozen=True)
class EveryLaidRevisionIsCounted(Then[RevisionsAndACaller, AdminSearchRevisionsPayload]):
    """심은 리비전이 모두, 그리고 그것만 세어진다.

    ``elsewhere_too``면 다른 프로젝트의 것까지, ``number``를 대면 그 번호의 것만 센다.
    """

    elsewhere_too: bool = False
    number: int | None = None

    @override
    def says(self) -> str:
        return "심은 리비전이 모두, 그리고 그것만 세어진다"

    @override
    def look(
        self, laid: RevisionsAndACaller, answered: Answered[AdminSearchRevisionsPayload]
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        wanted = [*laid.revisions, *(laid.elsewhere if self.elsewhere_too else ())]
        if self.number is not None:
            wanted = [one for one in wanted if one.revision_number == self.number]
        return [
            Held(
                "items.id",
                sorted(str(one.id) for one in payload.items),
                SameAs(sorted(str(one.id) for one in wanted), "센 리비전들"),
            ),
            Same(
                "items.revision_number",
                sorted(one.revision_number for one in payload.items),
                sorted(one.revision_number for one in wanted),
            ),
            Same("total_count", payload.total_count, len(wanted)),
            Same("has_next_page", payload.has_next_page, False),
            Same("has_previous_page", payload.has_previous_page, False),
        ]


@dataclass(frozen=True)
class EveryRevisionSlotIsCounted(Then[RevisionsAndACaller, SearchAllocatedResourceSlotsPayload]):
    """심은 리비전이 잡은 슬롯이 모두 세어진다."""

    @override
    def says(self) -> str:
        return "리비전이 잡은 슬롯이 모두 세어진다"

    @override
    def look(
        self,
        laid: RevisionsAndACaller,
        answered: Answered[SearchAllocatedResourceSlotsPayload],
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(EntityNotFoundError, answered.raised)]
        return [
            Same(
                "items",
                sorted((one.slot_name, one.quantity) for one in payload.items),
                sorted(SLOTS),
            ),
            Same("total_count", payload.total_count, len(SLOTS)),
            Same("has_next_page", payload.has_next_page, False),
            Same("has_previous_page", payload.has_previous_page, False),
        ]
