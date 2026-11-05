"""폴더 복제 — 복제할 수 있는 폴더만, 내 이름으로."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override
from uuid import UUID

import pytest

from ai.backend.common.data.permission.types import Permission
from ai.backend.common.dto.manager.v2.vfolder.request import CloneVFolderInput
from ai.backend.common.dto.manager.v2.vfolder.response import CloneVFolderPayload
from ai.backend.manager.api.adapters.vfolder.adapter import VFolderAdapter
from ai.backend.manager.errors.common import Forbidden
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Held,
    Refused,
    Same,
    SameAs,
    Says,
    Scenario,
    Skipped,
    Then,
    Verdict,
    When,
)
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.domain import WrittenByThisRun
from bai_scenario.components.vfolder import (
    STORAGE_HOST,
    AFolderAndPeople,
    SomeoneWithAFolder,
)
from bai_scenario.fakes.storage_proxy import CLONE_TASK_ID
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

MADE = "copy"

type CloningStep = Scenario[
    TestSeedingSession, AFolderAndPeople, VFolderAdapter, CloneVFolderPayload
]


@dataclass(frozen=True)
class CloningTheFolder(When[AFolderAndPeople, VFolderAdapter, CloneVFolderPayload]):
    """자기 폴더를 새 이름으로 복제한다."""

    @override
    def operation(self) -> str:
        return "clone"

    @override
    def describe(self, laid: AFolderAndPeople) -> str:
        return Says(
            f"{laid.caller.username}이 {laid.folder.name} vfolder 를 {MADE} 라는 이름으로 "
            "복제합니다",
            english=(
                f"{laid.caller.username} clones the {laid.folder.name} vfolder under the name "
                f"{MADE}"
            ),
        )

    @override
    async def call(self, adapter: VFolderAdapter, laid: AFolderAndPeople) -> CloneVFolderPayload:
        with ActingAs(laid.caller):
            return await adapter.clone(laid.folder.id, CloneVFolderInput(name=MADE))


@dataclass(frozen=True)
class TheClonedFolder(Then[AFolderAndPeople, CloneVFolderPayload]):
    """복제된 폴더가 통째로 온다. 이름은 시나리오가 정한 값이다."""

    started: datetime

    @override
    def says(self) -> str:
        return Says(
            "복제된 vfolder 전체가 응답으로 옵니다",
            english="the whole cloned vfolder comes back",
        )

    @override
    def look(
        self, laid: AFolderAndPeople, answered: Answered[CloneVFolderPayload]
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        node = payload.vfolder
        return [
            Same("bgtask_id", payload.bgtask_id, str(CLONE_TASK_ID)),
            Held(
                "vfolder.id",
                node.id,
                SameAs(node.entity_id, Says("응답의 entity_id", english="the entity_id")),
            ),
            Same("vfolder.host", node.host, STORAGE_HOST),
            Same("vfolder.status", node.status, "ready"),
            Same("vfolder.metadata.name", node.metadata.name, MADE),
            Same("vfolder.metadata.cloneable", node.metadata.cloneable, False),
            Same("vfolder.metadata.last_used", node.metadata.last_used, None),
            Same(
                "vfolder.access_control.ownership_type", node.access_control.ownership_type, "user"
            ),
            Held(
                "vfolder.ownership.user_id",
                node.ownership.user_id,
                SameAs[UUID | None](laid.caller.id, Says("복제한 사람", english="the cloner")),
            ),
            Skipped(
                "vfolder.ownership.project_id",
                Says(
                    "개인 vfolder 는 그 사용자의 개인 프로젝트에 붙고, 그 id 는 실행마다 다릅니다",
                    english=(
                        "a personal folder lands in the user's personal project, whose id "
                        "differs per run"
                    ),
                ),
            ),
            Held(
                "vfolder.ownership.creator_id",
                node.ownership.creator_id,
                SameAs[UUID | None](laid.caller.id, Says("복제한 사람", english="the cloner")),
            ),
            Same(
                "vfolder.ownership.creator_email", node.ownership.creator_email, laid.caller.email
            ),
            Same("vfolder.unmanaged_path", node.unmanaged_path, None),
            Skipped(
                "vfolder.metadata.usage_mode",
                Says("타입이 이미 값을 고정합니다", english="the type already fixes the value"),
            ),
            Skipped(
                "vfolder.metadata.quota_scope_id",
                Says(
                    "복제한 사람의 id 로 만들어져 실행마다 다릅니다",
                    english="it is made from the cloner's id, so it differs per run",
                ),
            ),
            Skipped(
                "vfolder.access_control.permission",
                Says(
                    "마운트 권한이라 이 표가 확인하는 값이 아닙니다",
                    english="it is a mount permission, which this table does not check",
                ),
            ),
            Skipped(
                "vfolder.quota",
                Says(
                    "저장소가 응답하는 값이라 여기서 말할 수 없습니다",
                    english="the storage answers it, so it cannot be stated here",
                ),
            ),
            Held(
                "vfolder.metadata.created_at",
                node.metadata.created_at,
                WrittenByThisRun(self.started),
            ),
        ]


@dataclass(frozen=True)
class AGrantedUserClonesTheFolder(
    Scenario[TestSeedingSession, AFolderAndPeople, VFolderAdapter, CloneVFolderPayload]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-user-granted-clone-copies-a-cloneable-folder"

    @override
    def describe(self) -> str:
        return Says(
            "복제할 수 있는 자기 vfolder 에 대해 복제 권한을 받은 사용자가 새 이름으로 복제하면, "
            "복제된 vfolder 가 응답으로 옵니다",
            english=(
                "when a user granted clone on a cloneable vfolder of their own clones it under "
                "a new name, the cloned vfolder comes back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AFolderAndPeople]:
        return SomeoneWithAFolder(permissions=(Permission.CREATE, Permission.READ), cloneable=True)

    @override
    def when(self) -> When[AFolderAndPeople, VFolderAdapter, CloneVFolderPayload]:
        return CloningTheFolder()

    @override
    def then(self) -> Then[AFolderAndPeople, CloneVFolderPayload]:
        return TheClonedFolder(started=self.started)


@dataclass(frozen=True)
class AFolderNotCloneableMayNotBeCloned(
    Scenario[TestSeedingSession, AFolderAndPeople, VFolderAdapter, CloneVFolderPayload]
):
    @override
    def summary(self) -> str:
        return "cloning-a-folder-not-marked-cloneable-is-refused"

    @override
    def describe(self) -> str:
        return Says(
            "복제할 수 있다고 표시되지 않은 vfolder 를 복제하려 하면 거부됩니다",
            english="when a user tries to clone a vfolder not marked cloneable, it is rejected",
        )

    @override
    def given(self) -> Given[TestSeedingSession, AFolderAndPeople]:
        return SomeoneWithAFolder(permissions=(Permission.CREATE, Permission.READ))

    @override
    def when(self) -> When[AFolderAndPeople, VFolderAdapter, CloneVFolderPayload]:
        return CloningTheFolder()

    @override
    def then(self) -> Then[AFolderAndPeople, CloneVFolderPayload]:
        return TheCallIsRefused(Forbidden)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotCloneTheFolder(
    Scenario[TestSeedingSession, AFolderAndPeople, VFolderAdapter, CloneVFolderPayload]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-clone-their-folder"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 받지 않은 사용자가 자기 vfolder 를 복제하려 하면 권한 부족으로 거부됩니다",
            english=(
                "when a user granted nothing tries to clone their own vfolder, it is rejected "
                "for lack of permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AFolderAndPeople]:
        return SomeoneWithAFolder(cloneable=True)

    @override
    def when(self) -> When[AFolderAndPeople, VFolderAdapter, CloneVFolderPayload]:
        return CloningTheFolder()

    @override
    def then(self) -> Then[AFolderAndPeople, CloneVFolderPayload]:
        return TheCallIsRefused(NotEnoughPermission)


SCENARIOS: list[CloningStep] = [
    AGrantedUserClonesTheFolder(started=datetime.now(UTC)),
    AFolderNotCloneableMayNotBeCloned(),
    AUserGrantedNothingMayNotCloneTheFolder(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_cloning(
    scenario: CloningStep, adapter: VFolderAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
