"""리비전 더하기 — 누가 더할 수 있고, 여러 겹을 포갠 결과가 무엇인가.

답은 더해진 리비전뿐이다. 자동 활성, 보관 개수를 넘은 리비전 지우기, 대지 않은 마운트
권한이 무엇으로 붙는지는 답에 드러나지 않아 여기 없다.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import override

import pytest

from ai.backend.common.dto.manager.v2.common import ResourceSlotEntryInput
from ai.backend.common.dto.manager.v2.deployment.request import (
    AddRevisionInput,
    AddRevisionOptions,
    ClusterConfigInput,
    ImageInput,
    ModelConfigInput,
    ModelDefinitionInput,
    ModelMountConfigInput,
    ModelRuntimeConfigInput,
    ResourceConfigInput,
    ResourceSlotInput,
)
from ai.backend.common.dto.manager.v2.deployment.response import RevisionNode
from ai.backend.common.exception import BackendAISchemaValidationFailed
from ai.backend.common.types import ClusterMode, IntrinsicSlotNames, MountPermission
from ai.backend.manager.api.adapters.deployment.adapter import DeploymentAdapter
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.errors.api import InvalidAPIParameters
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.errors.storage import VFolderNotFound, VFolderPermissionError
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Given,
    Language,
    Says,
    Scenario,
    Then,
    When,
    in_language,
)
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.deployment_revision import (
    MOUNTED_AT,
    SERVED,
    SLOTS,
    ADeploymentToRevise,
    AnothersDeploymentToRevise,
    RevisionsAndACaller,
    TheRevisionNode,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

MEMORY_ONLY: tuple[tuple[str, Decimal], ...] = tuple(
    one for one in SLOTS if one[0] == str(IntrinsicSlotNames.MEMORY.value)
)

type AddingStep = Scenario[TestSeedingSession, RevisionsAndACaller, DeploymentAdapter, RevisionNode]


@dataclass(frozen=True)
class AddingARevision(When[RevisionsAndACaller, DeploymentAdapter, RevisionNode]):
    """리비전 하나를 더한다. 끈 자리는 요청에서 뺀다.

    ``slots``가 없으면 자원과 클러스터를 함께 뺀다. 어댑터가 둘을 한 묶음으로 읽는다.
    """

    slots: tuple[tuple[str, Decimal], ...] | None = SLOTS
    image: bool = True
    runtime: bool = True
    definition: bool = True
    mount_perm: MountPermission | None = None

    @override
    def operation(self) -> str:
        return "add_revision"

    @override
    def describe(self, laid: RevisionsAndACaller) -> str:
        left_out = [
            what
            for what, given in (
                (Says("자원과 클러스터", english="resources and cluster"), self.slots is not None),
                (Says("이미지", english="the image"), self.image),
                (Says("인퍼런스 런타임 종류", english="the runtime variant"), self.runtime),
                (Says("모델 정의", english="the model definition"), self.definition),
            )
            if not given
        ]
        korean = (
            f" ({', '.join(in_language(what, Language.KOREAN) for what in left_out)} 없이)"
            if left_out
            else ""
        )
        english = (
            f" without {', '.join(in_language(what, Language.ENGLISH) for what in left_out)}"
            if left_out
            else ""
        )
        return Says(
            f"{laid.caller.username} 이 {laid.deployment.metadata.name}에 리비전을 추가합니다{korean}",
            english=(
                f"{laid.caller.username} adds a revision to "
                f"{laid.deployment.metadata.name}{english}"
            ),
        )

    @override
    async def call(self, adapter: DeploymentAdapter, laid: RevisionsAndACaller) -> RevisionNode:
        with ActingAs(laid.caller):
            payload = await adapter.add_revision(
                AddRevisionInput(
                    deployment_id=laid.deployment.id,
                    cluster_config=(
                        ClusterConfigInput(mode=ClusterMode.SINGLE_NODE, size=1)
                        if self.slots is not None
                        else None
                    ),
                    resource_config=(
                        ResourceConfigInput(
                            resource_slots=ResourceSlotInput(
                                entries=[
                                    ResourceSlotEntryInput(resource_type=name, quantity=str(amount))
                                    for name, amount in self.slots
                                ]
                            )
                        )
                        if self.slots is not None
                        else None
                    ),
                    image=ImageInput(id=laid.image.id) if self.image else None,
                    model_runtime_config=(
                        ModelRuntimeConfigInput(runtime_variant_id=laid.runtime.id)
                        if self.runtime
                        else None
                    ),
                    model_mount_config=ModelMountConfigInput(
                        vfolder_id=laid.folder.id,
                        mount_destination=MOUNTED_AT,
                        mount_perm=self.mount_perm,
                    ),
                    model_definition=(
                        ModelDefinitionInput(models=[ModelConfigInput(name=SERVED)])
                        if self.definition
                        else None
                    ),
                ),
                AddRevisionOptions(),
            )
        return payload.revision


@dataclass(frozen=True)
class TheGrantedUserAddsTheFirst(
    Scenario[TestSeedingSession, RevisionsAndACaller, DeploymentAdapter, RevisionNode]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-user-granted-create-adds-the-first-revision"

    @override
    def describe(self) -> str:
        return Says(
            "리비전 없는 배포에 생성 권한을 받은 사용자가 모든 설정을 주고 리비전을 추가하면, "
            "번호 1을 단 리비전이 준 설정 그대로 옵니다",
            english=(
                "when a user granted create adds a revision with every setting to a deployment "
                "that has no revision, the revision numbered 1 comes back with exactly the "
                "settings that were given"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, RevisionsAndACaller]:
        return ADeploymentToRevise(granted=(Permission.CREATE,))

    @override
    def when(self) -> When[RevisionsAndACaller, DeploymentAdapter, RevisionNode]:
        return AddingARevision()

    @override
    def then(self) -> Then[RevisionsAndACaller, RevisionNode]:
        return TheRevisionNode(started=self.started, number=1)


@dataclass(frozen=True)
class TheNextOneIsNumberedOnePast(
    Scenario[TestSeedingSession, RevisionsAndACaller, DeploymentAdapter, RevisionNode]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "the-next-revision-is-numbered-one-past-the-last"

    @override
    def describe(self) -> str:
        return Says(
            "리비전 하나가 딸린 배포에 리비전을 추가하면, 번호 2를 단 리비전이 옵니다",
            english=(
                "adding a revision to a deployment that holds one revision brings back the "
                "revision numbered 2"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, RevisionsAndACaller]:
        return ADeploymentToRevise(granted=(Permission.CREATE,), revisions=1)

    @override
    def when(self) -> When[RevisionsAndACaller, DeploymentAdapter, RevisionNode]:
        return AddingARevision()

    @override
    def then(self) -> Then[RevisionsAndACaller, RevisionNode]:
        return TheRevisionNode(started=self.started, number=2)


@dataclass(frozen=True)
class LeavingOutResourcesRunsOnOneNodeWithNoSlot(
    Scenario[TestSeedingSession, RevisionsAndACaller, DeploymentAdapter, RevisionNode]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-revision-added-without-resources-runs-on-one-node-with-no-slot"

    @override
    def describe(self) -> str:
        return Says(
            "프리셋도 필수 슬롯도 없이 자원과 클러스터를 빼고 리비전을 추가하면, "
            "노드 하나에 크기 1이고 자원 슬롯이 빈 리비전이 옵니다",
            english=(
                "adding a revision without resources and cluster when there is neither a preset "
                "nor a required slot brings back a revision on one node with size 1 and no "
                "resource slot"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, RevisionsAndACaller]:
        return ADeploymentToRevise(granted=(Permission.CREATE,))

    @override
    def when(self) -> When[RevisionsAndACaller, DeploymentAdapter, RevisionNode]:
        return AddingARevision(slots=None)

    @override
    def then(self) -> Then[RevisionsAndACaller, RevisionNode]:
        return TheRevisionNode(started=self.started, number=1, slots=())


@dataclass(frozen=True)
class AMountBeyondTheFolderIsRefused(
    Scenario[TestSeedingSession, RevisionsAndACaller, DeploymentAdapter, RevisionNode]
):
    @override
    def summary(self) -> str:
        return "a-mount-beyond-what-the-caller-holds-on-the-folder-is-refused"

    @override
    def describe(self) -> str:
        return Says(
            "남의 모델 vfolder 를 읽기 전용으로 빌린 사용자가 읽고 쓰기로 마운트하는 리비전을 "
            "추가하면, vfolder 권한을 넘는다는 이유로 거부됩니다",
            english=(
                "when a user who borrowed another user's model vfolder as read-only adds a "
                "revision that mounts it read-write, the call is rejected because it exceeds the "
                "vfolder permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, RevisionsAndACaller]:
        return ADeploymentToRevise(granted=(Permission.CREATE,), folder_lent=True)

    @override
    def when(self) -> When[RevisionsAndACaller, DeploymentAdapter, RevisionNode]:
        return AddingARevision(mount_perm=MountPermission.READ_WRITE)

    @override
    def then(self) -> Then[RevisionsAndACaller, RevisionNode]:
        return TheCallIsRefused(VFolderPermissionError)


@dataclass(frozen=True)
class NoImageAnywhereIsRefused(
    Scenario[TestSeedingSession, RevisionsAndACaller, DeploymentAdapter, RevisionNode]
):
    @override
    def summary(self) -> str:
        return "a-revision-with-no-image-from-any-layer-is-refused"

    @override
    def describe(self) -> str:
        return Says(
            "프리셋 없이 이미지를 빼고 리비전을 추가하면, 입력이 틀렸다는 이유로 거부됩니다",
            english=(
                "adding a revision without an image and without a preset is rejected because the "
                "input is wrong"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, RevisionsAndACaller]:
        return ADeploymentToRevise(granted=(Permission.CREATE,))

    @override
    def when(self) -> When[RevisionsAndACaller, DeploymentAdapter, RevisionNode]:
        return AddingARevision(image=False)

    @override
    def then(self) -> Then[RevisionsAndACaller, RevisionNode]:
        return TheCallIsRefused(InvalidAPIParameters)


@dataclass(frozen=True)
class NoRuntimeAnywhereIsRefused(
    Scenario[TestSeedingSession, RevisionsAndACaller, DeploymentAdapter, RevisionNode]
):
    @override
    def summary(self) -> str:
        return "a-revision-with-no-runtime-variant-from-any-layer-is-refused"

    @override
    def describe(self) -> str:
        return Says(
            "프리셋 없이 인퍼런스 런타임 종류를 빼고 리비전을 추가하면, "
            "입력이 틀렸다는 이유로 거부됩니다",
            english=(
                "adding a revision without a runtime variant and without a preset is rejected "
                "because the input is wrong"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, RevisionsAndACaller]:
        return ADeploymentToRevise(granted=(Permission.CREATE,))

    @override
    def when(self) -> When[RevisionsAndACaller, DeploymentAdapter, RevisionNode]:
        return AddingARevision(runtime=False)

    @override
    def then(self) -> Then[RevisionsAndACaller, RevisionNode]:
        return TheCallIsRefused(InvalidAPIParameters)


@dataclass(frozen=True)
class NoModelDefinitionAnywhereIsRefused(
    Scenario[TestSeedingSession, RevisionsAndACaller, DeploymentAdapter, RevisionNode]
):
    @override
    def summary(self) -> str:
        return "a-revision-with-no-model-definition-from-any-layer-is-refused"

    @override
    def describe(self) -> str:
        return Says(
            "vfolder 파일을 읽지 않는 인퍼런스 런타임 종류로 프리셋 없이 모델 정의를 빼고 "
            "리비전을 추가하면, 이름 없는 모델이 모델 정의 검증에서 거부됩니다",
            english=(
                "adding a revision with a runtime variant that does not read vfolder files, "
                "without a model definition and without a preset, is rejected in model definition "
                "validation because a model has no name"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, RevisionsAndACaller]:
        return ADeploymentToRevise(granted=(Permission.CREATE,))

    @override
    def when(self) -> When[RevisionsAndACaller, DeploymentAdapter, RevisionNode]:
        return AddingARevision(definition=False)

    @override
    def then(self) -> Then[RevisionsAndACaller, RevisionNode]:
        return TheCallIsRefused(BackendAISchemaValidationFailed)


@dataclass(frozen=True)
class AMissingRequiredSlotIsRefused(
    Scenario[TestSeedingSession, RevisionsAndACaller, DeploymentAdapter, RevisionNode]
):
    @override
    def summary(self) -> str:
        return "a-revision-missing-a-required-slot-is-refused"

    @override
    def describe(self) -> str:
        return Says(
            "모든 리비전이 채워야 하는 슬롯이 정해져 있고 그 슬롯을 빼고 리비전을 추가하면, "
            "입력이 틀렸다는 이유로 거부됩니다",
            english=(
                "when a slot every revision must fill is set and a revision is added without it, "
                "the call is rejected because the input is wrong"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, RevisionsAndACaller]:
        return ADeploymentToRevise(granted=(Permission.CREATE,), cpu_required=True)

    @override
    def when(self) -> When[RevisionsAndACaller, DeploymentAdapter, RevisionNode]:
        return AddingARevision(slots=MEMORY_ONLY)

    @override
    def then(self) -> Then[RevisionsAndACaller, RevisionNode]:
        return TheCallIsRefused(InvalidAPIParameters)


@dataclass(frozen=True)
class AReadGrantDoesNotAdd(
    Scenario[TestSeedingSession, RevisionsAndACaller, DeploymentAdapter, RevisionNode]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-only-read-may-not-add-a-revision"

    @override
    def describe(self) -> str:
        return Says(
            "배포 읽기 권한만 받은 사용자가 리비전을 추가하면, 권한 부족으로 거부됩니다",
            english=(
                "when a user granted only read on the deployment adds a revision, the call is "
                "rejected for lack of permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, RevisionsAndACaller]:
        return ADeploymentToRevise(granted=(Permission.READ,))

    @override
    def when(self) -> When[RevisionsAndACaller, DeploymentAdapter, RevisionNode]:
        return AddingARevision()

    @override
    def then(self) -> Then[RevisionsAndACaller, RevisionNode]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class TheSuperadminAddsToAnothers(
    Scenario[TestSeedingSession, RevisionsAndACaller, DeploymentAdapter, RevisionNode]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "the-superadmin-adds-a-revision-to-anothers-deployment-without-a-grant"

    @override
    def describe(self) -> str:
        return Says(
            "배포에도 자기 모델 vfolder 에도 권한을 받지 않은 superadmin 이 남의 배포에 리비전을 "
            "추가하면, 리비전이 추가됩니다. 역할이 배포 권한과 vfolder 권한을 함께 지나갑니다",
            english=(
                "when a superadmin holding no grant on the deployment or on their own model "
                "vfolder adds a revision to another user's deployment, the revision is added; the "
                "role passes through both the deployment permission and the vfolder permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, RevisionsAndACaller]:
        return AnothersDeploymentToRevise()

    @override
    def when(self) -> When[RevisionsAndACaller, DeploymentAdapter, RevisionNode]:
        return AddingARevision()

    @override
    def then(self) -> Then[RevisionsAndACaller, RevisionNode]:
        return TheRevisionNode(started=self.started, number=1)


@dataclass(frozen=True)
class AFolderTheCallerMayNotReadIsNotFound(
    Scenario[TestSeedingSession, RevisionsAndACaller, DeploymentAdapter, RevisionNode]
):
    @override
    def summary(self) -> str:
        return "a-model-folder-the-caller-may-not-read-is-not-found"

    @override
    def describe(self) -> str:
        return Says(
            "배포 생성 권한은 받았지만 모델 vfolder 를 읽을 권한이 없는 사용자가 그 vfolder 로 "
            "리비전을 추가하면, vfolder 를 찾을 수 없다는 이유로 거부됩니다",
            english=(
                "when a user granted create on the deployment but not read on the model vfolder "
                "adds a revision with that vfolder, the call is rejected because the vfolder is "
                "not found"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, RevisionsAndACaller]:
        return ADeploymentToRevise(granted=(Permission.CREATE,), folder_readable=False)

    @override
    def when(self) -> When[RevisionsAndACaller, DeploymentAdapter, RevisionNode]:
        return AddingARevision()

    @override
    def then(self) -> Then[RevisionsAndACaller, RevisionNode]:
        return TheCallIsRefused(VFolderNotFound)


SCENARIOS: list[AddingStep] = [
    TheGrantedUserAddsTheFirst(started=datetime.now(UTC)),
    TheNextOneIsNumberedOnePast(started=datetime.now(UTC)),
    LeavingOutResourcesRunsOnOneNodeWithNoSlot(started=datetime.now(UTC)),
    AMountBeyondTheFolderIsRefused(),
    NoImageAnywhereIsRefused(),
    NoRuntimeAnywhereIsRefused(),
    NoModelDefinitionAnywhereIsRefused(),
    AMissingRequiredSlotIsRefused(),
    AReadGrantDoesNotAdd(),
    TheSuperadminAddsToAnothers(started=datetime.now(UTC)),
    AFolderTheCallerMayNotReadIsNotFound(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_adding_revisions(
    scenario: AddingStep, adapter: DeploymentAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
