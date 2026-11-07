"""폴더 하나에서 사용자별 마운트 레벨 정하기, 되돌리기, 읽기."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override
from uuid import UUID

import pytest

from ai.backend.common.data.permission.types import Permission
from ai.backend.common.dto.manager.v2.vfolder.request import (
    SetVFolderMountPolicyInput,
    UnsetVFolderMountPolicyInput,
)
from ai.backend.common.dto.manager.v2.vfolder.response import (
    SetVFolderMountPolicyPayload,
    UnsetVFolderMountPolicyPayload,
    VFolderMountPoliciesPayload,
    VFolderMountPolicyNode,
)
from ai.backend.common.dto.manager.v2.vfolder.types import VFolderPermissionField
from ai.backend.manager.api.adapters.vfolder.adapter import VFolderAdapter
from ai.backend.manager.data.user.types import UserData
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.errors.storage import VFolderMountPolicyNotApplicable
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
from bai_scenario.components.vfolder import AFolderAndPeople, SomeoneWithAFolder
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type SettingStep = Scenario[
    TestSeedingSession, AFolderAndPeople, VFolderAdapter, SetVFolderMountPolicyPayload
]
type UnsettingStep = Scenario[
    TestSeedingSession, AFolderAndPeople, VFolderAdapter, UnsetVFolderMountPolicyPayload
]
type ListingStep = Scenario[
    TestSeedingSession, AFolderAndPeople, VFolderAdapter, VFolderMountPoliciesPayload
]


def _other(laid: AFolderAndPeople) -> UUID:
    if laid.other is None:
        raise LookupError("the second user was not seeded")
    return laid.other.id


def _other_user(laid: AFolderAndPeople) -> UserData:
    if laid.other is None:
        raise LookupError("the second user was not seeded")
    return laid.other


@dataclass(frozen=True)
class SettingTheOtherUsersLevel(
    When[AFolderAndPeople, VFolderAdapter, SetVFolderMountPolicyPayload]
):
    """다른 사용자의 마운트 레벨을 읽기 전용으로 정한다. ``owner``면 폴더 소유자를 가리킨다."""

    owner: bool = False

    @override
    def operation(self) -> str:
        return "set_mount_policy"

    @override
    def describe(self, laid: AFolderAndPeople) -> str:
        target = "소유자 자신" if self.owner else "다른 사용자"
        target_en = "the owner themselves" if self.owner else "another user"
        return Says(
            f"{laid.caller.username}이 {laid.folder.name} vfolder 에서 {target}의 마운트 레벨을 "
            "읽기 전용으로 정합니다",
            english=(
                f"{laid.caller.username} sets the mount level of {target_en} on the "
                f"{laid.folder.name} vfolder to read-only"
            ),
        )

    @override
    async def call(
        self, adapter: VFolderAdapter, laid: AFolderAndPeople
    ) -> SetVFolderMountPolicyPayload:
        user_id = laid.caller.id if self.owner else _other(laid)
        with ActingAs(laid.caller):
            return await adapter.set_mount_policy(
                laid.folder.id,
                SetVFolderMountPolicyInput(
                    user_id=user_id, permission=VFolderPermissionField.READ_ONLY
                ),
            )


@dataclass(frozen=True)
class UnsettingTheOtherUsersLevel(
    When[AFolderAndPeople, VFolderAdapter, UnsetVFolderMountPolicyPayload]
):
    """다른 사용자의 마운트 레벨을 먼저 정하고, 이어서 되돌린다.

    ``by_other``이면 레벨은 권한 있는 호출자가 정하고, 권한이 없는 다른 사용자가 되돌린다.
    """

    by_other: bool = False

    @override
    def operation(self) -> str:
        return "unset_mount_policy"

    @override
    def describe(self, laid: AFolderAndPeople) -> str:
        if self.by_other:
            other = _other_user(laid)
            return Says(
                f"{laid.caller.username}이 {laid.folder.name} vfolder 에서 다른 사용자의 마운트 "
                f"레벨을 정한 뒤, 권한이 없는 {other.username}이 그것을 되돌립니다",
                english=(
                    f"{laid.caller.username} sets another user's mount level on the "
                    f"{laid.folder.name} vfolder, and then {other.username}, holding no "
                    "permission, takes it back"
                ),
            )
        return Says(
            f"{laid.caller.username}이 {laid.folder.name} vfolder 에서 다른 사용자의 마운트 "
            "레벨을 정했다가 되돌립니다",
            english=(
                f"{laid.caller.username} sets and then takes back another user's mount level on "
                f"the {laid.folder.name} vfolder"
            ),
        )

    @override
    async def call(
        self, adapter: VFolderAdapter, laid: AFolderAndPeople
    ) -> UnsetVFolderMountPolicyPayload:
        other_id = _other(laid)
        with ActingAs(laid.caller):
            await adapter.set_mount_policy(
                laid.folder.id,
                SetVFolderMountPolicyInput(
                    user_id=other_id, permission=VFolderPermissionField.READ_ONLY
                ),
            )
        actor = _other_user(laid) if self.by_other else laid.caller
        with ActingAs(actor):
            return await adapter.unset_mount_policy(
                laid.folder.id, UnsetVFolderMountPolicyInput(user_id=other_id)
            )


@dataclass(frozen=True)
class ListingTheLevels(When[AFolderAndPeople, VFolderAdapter, VFolderMountPoliciesPayload]):
    """다른 사용자의 마운트 레벨을 정한 뒤 목록을 읽는다.

    ``by_other``이면 레벨은 권한 있는 호출자가 정하고, 권한이 없는 다른 사용자가 목록을 읽는다.
    """

    by_other: bool = False

    @override
    def operation(self) -> str:
        return "list_mount_policies"

    @override
    def describe(self, laid: AFolderAndPeople) -> str:
        if self.by_other:
            other = _other_user(laid)
            return Says(
                f"{laid.caller.username}이 {laid.folder.name} vfolder 에 다른 사용자의 마운트 "
                f"레벨을 정한 뒤, 권한이 없는 {other.username}이 걸린 레벨을 조회합니다",
                english=(
                    f"{laid.caller.username} sets another user's mount level on the "
                    f"{laid.folder.name} vfolder, and then {other.username}, holding no "
                    "permission, lists the levels set on it"
                ),
            )
        return Says(
            f"{laid.caller.username}이 {laid.folder.name} vfolder 에 걸린 마운트 레벨을 조회합니다",
            english=(
                f"{laid.caller.username} lists the mount levels set on the {laid.folder.name} "
                "vfolder"
            ),
        )

    @override
    async def call(
        self, adapter: VFolderAdapter, laid: AFolderAndPeople
    ) -> VFolderMountPoliciesPayload:
        other_id = _other(laid)
        with ActingAs(laid.caller):
            await adapter.set_mount_policy(
                laid.folder.id,
                SetVFolderMountPolicyInput(
                    user_id=other_id, permission=VFolderPermissionField.READ_ONLY
                ),
            )
        actor = _other_user(laid) if self.by_other else laid.caller
        with ActingAs(actor):
            return await adapter.list_mount_policies(laid.folder.id)


@dataclass(frozen=True)
class TheLevelSet(Then[AFolderAndPeople, SetVFolderMountPolicyPayload]):
    """정한 마운트 레벨이 통째로 온다."""

    started: datetime

    @override
    def says(self) -> str:
        return Says(
            "정한 마운트 레벨 전체가 응답으로 옵니다",
            english="the whole mount level just set comes back",
        )

    @override
    def look(
        self, laid: AFolderAndPeople, answered: Answered[SetVFolderMountPolicyPayload]
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        node = payload.policy
        return [
            Skipped(
                "policy.id",
                Says("데이터베이스가 생성합니다", english="the database generates it"),
            ),
            Held(
                "policy.field_id",
                node.field_id,
                SameAs(node.id, Says("응답의 id", english="the id in the answer")),
            ),
            Held(
                "policy.vfolder_id",
                node.vfolder_id,
                SameAs[UUID](laid.folder.id, Says("부른 vfolder", english="the vfolder called")),
            ),
            Held(
                "policy.user_id",
                node.user_id,
                SameAs(
                    _other(laid), Says("레벨을 받은 사용자", english="the user given the level")
                ),
            ),
            Same("policy.permission", node.permission, "ro"),
            Held("policy.created_at", node.created_at, WrittenByThisRun(self.started)),
            Held("policy.updated_at", node.updated_at, WrittenByThisRun(self.started)),
        ]


@dataclass(frozen=True)
class TheLevelTakenBack(Then[AFolderAndPeople, UnsetVFolderMountPolicyPayload]):
    """되돌린 레벨의 자리가 온다. 그 행은 지워졌다."""

    @override
    def says(self) -> str:
        return Says(
            "되돌린 마운트 레벨의 자리가 응답으로 오고, 그 행은 지워졌습니다",
            english="the place of the mount level taken back comes, and the row is gone",
        )

    @override
    def look(
        self, laid: AFolderAndPeople, answered: Answered[UnsetVFolderMountPolicyPayload]
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        return [
            Held(
                "vfolder_id",
                payload.vfolder_id,
                SameAs[UUID](laid.folder.id, Says("부른 vfolder", english="the vfolder called")),
            ),
            Held(
                "user_id",
                payload.user_id,
                SameAs(
                    _other(laid), Says("레벨을 잃은 사용자", english="the user who lost the level")
                ),
            ),
            Same("removed", payload.removed, True),
        ]


@dataclass(frozen=True)
class TheLevelsOnTheFolder(Then[AFolderAndPeople, VFolderMountPoliciesPayload]):
    """마운트 레벨 하나가 실린 목록이 온다."""

    started: datetime

    @override
    def says(self) -> str:
        return Says(
            "마운트 레벨 하나가 실린 목록이 응답으로 옵니다",
            english="the list holding the one mount level comes back",
        )

    @override
    def look(
        self, laid: AFolderAndPeople, answered: Answered[VFolderMountPoliciesPayload]
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        verdicts: list[Verdict] = [Same("items.length", len(payload.items), 1)]
        if not payload.items:
            return verdicts
        node: VFolderMountPolicyNode = payload.items[0]
        return [*verdicts, *_level_verdicts(self.started, laid, node)]


def _level_verdicts(
    started: datetime, laid: AFolderAndPeople, node: VFolderMountPolicyNode
) -> list[Verdict]:
    return [
        Skipped(
            "items[0].id",
            Says("데이터베이스가 생성합니다", english="the database generates it"),
        ),
        Held(
            "items[0].field_id",
            node.field_id,
            SameAs(node.id, Says("응답의 id", english="the id in the answer")),
        ),
        Held(
            "items[0].vfolder_id",
            node.vfolder_id,
            SameAs[UUID](laid.folder.id, Says("부른 vfolder", english="the vfolder called")),
        ),
        Held(
            "items[0].user_id",
            node.user_id,
            SameAs(_other(laid), Says("레벨을 받은 사용자", english="the user given the level")),
        ),
        Same("items[0].permission", node.permission, "ro"),
        Held("items[0].created_at", node.created_at, WrittenByThisRun(started)),
        Held("items[0].updated_at", node.updated_at, WrittenByThisRun(started)),
    ]


@dataclass(frozen=True)
class AGrantedOwnerSetsTheLevel(
    Scenario[TestSeedingSession, AFolderAndPeople, VFolderAdapter, SetVFolderMountPolicyPayload]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-user-granted-folder-update-sets-another-users-mount-level"

    @override
    def describe(self) -> str:
        return Says(
            "vfolder 수정 권한을 받은 사용자가 다른 사용자의 마운트 레벨을 읽기 전용으로 "
            "정하면, 정한 레벨이 응답으로 옵니다",
            english=(
                "when a user granted vfolder update sets another user's mount level to "
                "read-only, the level now set comes back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AFolderAndPeople]:
        return SomeoneWithAFolder(permissions=(Permission.UPDATE,), with_other=True)

    @override
    def when(self) -> When[AFolderAndPeople, VFolderAdapter, SetVFolderMountPolicyPayload]:
        return SettingTheOtherUsersLevel()

    @override
    def then(self) -> Then[AFolderAndPeople, SetVFolderMountPolicyPayload]:
        return TheLevelSet(started=self.started)


@dataclass(frozen=True)
class ALevelForTheOwnerIsRefused(
    Scenario[TestSeedingSession, AFolderAndPeople, VFolderAdapter, SetVFolderMountPolicyPayload]
):
    @override
    def summary(self) -> str:
        return "setting-the-owners-own-mount-level-is-refused"

    @override
    def describe(self) -> str:
        return Says(
            "폴더 소유자의 마운트 레벨을 정하려 하면 그 자체로 거부됩니다",
            english="when a user tries to set the folder owner's mount level, it is rejected",
        )

    @override
    def given(self) -> Given[TestSeedingSession, AFolderAndPeople]:
        return SomeoneWithAFolder(permissions=(Permission.UPDATE,), with_other=True)

    @override
    def when(self) -> When[AFolderAndPeople, VFolderAdapter, SetVFolderMountPolicyPayload]:
        return SettingTheOtherUsersLevel(owner=True)

    @override
    def then(self) -> Then[AFolderAndPeople, SetVFolderMountPolicyPayload]:
        return TheCallIsRefused(VFolderMountPolicyNotApplicable)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotSetALevel(
    Scenario[TestSeedingSession, AFolderAndPeople, VFolderAdapter, SetVFolderMountPolicyPayload]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-set-a-mount-level"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 받지 않은 사용자가 마운트 레벨을 정하려 하면 권한 부족으로 거부됩니다",
            english=(
                "when a user granted nothing tries to set a mount level, it is rejected for "
                "lack of permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AFolderAndPeople]:
        return SomeoneWithAFolder(with_other=True)

    @override
    def when(self) -> When[AFolderAndPeople, VFolderAdapter, SetVFolderMountPolicyPayload]:
        return SettingTheOtherUsersLevel()

    @override
    def then(self) -> Then[AFolderAndPeople, SetVFolderMountPolicyPayload]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class AGrantedOwnerTakesTheLevelBack(
    Scenario[TestSeedingSession, AFolderAndPeople, VFolderAdapter, UnsetVFolderMountPolicyPayload]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-folder-update-takes-another-users-level-back"

    @override
    def describe(self) -> str:
        return Says(
            "vfolder 수정 권한을 받은 사용자가 다른 사용자의 마운트 레벨을 되돌리면, 그 자리와 "
            "지워졌다는 사실이 응답으로 옵니다",
            english=(
                "when a user granted vfolder update takes back another user's mount level, its "
                "place and that the row is gone come back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AFolderAndPeople]:
        return SomeoneWithAFolder(permissions=(Permission.UPDATE,), with_other=True)

    @override
    def when(self) -> When[AFolderAndPeople, VFolderAdapter, UnsetVFolderMountPolicyPayload]:
        return UnsettingTheOtherUsersLevel()

    @override
    def then(self) -> Then[AFolderAndPeople, UnsetVFolderMountPolicyPayload]:
        return TheLevelTakenBack()


@dataclass(frozen=True)
class AUserGrantedNothingMayNotTakeALevelBack(
    Scenario[TestSeedingSession, AFolderAndPeople, VFolderAdapter, UnsetVFolderMountPolicyPayload]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-take-a-mount-level-back"

    @override
    def describe(self) -> str:
        return Says(
            "vfolder 수정 권한을 받은 사용자가 다른 사용자의 마운트 레벨을 정한 뒤, 아무 권한도 "
            "받지 않은 다른 사용자가 그것을 되돌리려 하면 권한 부족으로 거부됩니다",
            english=(
                "when a user granted vfolder update sets another user's mount level and then a "
                "user holding no permission tries to take it back, it is rejected for lack of "
                "permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AFolderAndPeople]:
        return SomeoneWithAFolder(permissions=(Permission.UPDATE,), with_other=True)

    @override
    def when(self) -> When[AFolderAndPeople, VFolderAdapter, UnsetVFolderMountPolicyPayload]:
        return UnsettingTheOtherUsersLevel(by_other=True)

    @override
    def then(self) -> Then[AFolderAndPeople, UnsetVFolderMountPolicyPayload]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class AGrantedReaderListsTheLevels(
    Scenario[TestSeedingSession, AFolderAndPeople, VFolderAdapter, VFolderMountPoliciesPayload]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-user-granted-folder-read-lists-the-mount-levels"

    @override
    def describe(self) -> str:
        return Says(
            "vfolder 읽기 권한을 받은 사용자가 폴더에 걸린 마운트 레벨을 조회하면, 걸린 레벨이 "
            "실린 목록이 응답으로 옵니다",
            english=(
                "when a user granted vfolder read lists the mount levels set on the folder, the "
                "list holding them comes back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AFolderAndPeople]:
        return SomeoneWithAFolder(permissions=(Permission.READ, Permission.UPDATE), with_other=True)

    @override
    def when(self) -> When[AFolderAndPeople, VFolderAdapter, VFolderMountPoliciesPayload]:
        return ListingTheLevels()

    @override
    def then(self) -> Then[AFolderAndPeople, VFolderMountPoliciesPayload]:
        return TheLevelsOnTheFolder(started=self.started)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotListLevels(
    Scenario[TestSeedingSession, AFolderAndPeople, VFolderAdapter, VFolderMountPoliciesPayload]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-list-the-mount-levels"

    @override
    def describe(self) -> str:
        return Says(
            "vfolder 수정 권한을 받은 사용자가 다른 사용자의 마운트 레벨을 정한 뒤, 아무 권한도 "
            "받지 않은 다른 사용자가 걸린 레벨을 조회하려 하면 권한 부족으로 거부됩니다",
            english=(
                "when a user granted vfolder update sets another user's mount level and then a "
                "user holding no permission tries to list the levels set on the folder, it is "
                "rejected for lack of permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AFolderAndPeople]:
        return SomeoneWithAFolder(permissions=(Permission.UPDATE,), with_other=True)

    @override
    def when(self) -> When[AFolderAndPeople, VFolderAdapter, VFolderMountPoliciesPayload]:
        return ListingTheLevels(by_other=True)

    @override
    def then(self) -> Then[AFolderAndPeople, VFolderMountPoliciesPayload]:
        return TheCallIsRefused(NotEnoughPermission)


SETTING: list[SettingStep] = [
    AGrantedOwnerSetsTheLevel(started=datetime.now(UTC)),
    ALevelForTheOwnerIsRefused(),
    AUserGrantedNothingMayNotSetALevel(),
]

UNSETTING: list[UnsettingStep] = [
    AGrantedOwnerTakesTheLevelBack(),
    AUserGrantedNothingMayNotTakeALevelBack(),
]

LISTING: list[ListingStep] = [
    AGrantedReaderListsTheLevels(started=datetime.now(UTC)),
    AUserGrantedNothingMayNotListLevels(),
]


@pytest.mark.parametrize("scenario", SETTING, ids=lambda s: s.summary())
async def test_setting(
    scenario: SettingStep, adapter: VFolderAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)


@pytest.mark.parametrize("scenario", UNSETTING, ids=lambda s: s.summary())
async def test_unsetting(
    scenario: UnsettingStep, adapter: VFolderAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)


@pytest.mark.parametrize("scenario", LISTING, ids=lambda s: s.summary())
async def test_listing(
    scenario: ListingStep, adapter: VFolderAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
