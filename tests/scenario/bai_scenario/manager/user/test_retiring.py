"""사용자 물리기, 되살리기, 지우기 — 무엇이 바뀌고 누가 할 수 있는가.

수정의 `status`로 물리고 되살리는 경로도 여기서 본다.
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, override
from uuid import UUID, uuid4

import pytest

from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.user.request import (
    BulkUpdateUserItemInput,
    BulkUpdateUsersInput,
    DeleteUserInput,
    PurgeUserInput,
    RestoreUserInput,
    UpdateUserInput,
)
from ai.backend.common.dto.manager.v2.user.response import (
    BulkPurgeUsersPayload,
    BulkUpdateUsersPayload,
    DeleteUserPayload,
    PurgeUserPayload,
    RestoreUserPayload,
    UserNode,
)
from ai.backend.common.dto.manager.v2.user.types import UserStatus as UserStatusDTO
from ai.backend.manager.api.adapters.user.adapter import UserAdapter
from ai.backend.manager.data.domain.types import DomainData
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.data.user.types import UserData, UserStatus
from ai.backend.manager.errors.auth import InsufficientPrivilege
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.errors.user import UserDeleted, UserModificationBadRequest, UserNotFound
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.services.user.actions.purge_user import BulkPurgeUserAction
from ai.backend.testutils.scenario_steps import (
    Answered,
    Condition,
    Given,
    Held,
    Language,
    Refused,
    Same,
    SameAs,
    Says,
    Scenario,
    Skipped,
    Then,
    Verdict,
    When,
    in_language,
)
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.domain import WAS_HERE, SomeoneOf
from bai_scenario.components.user import AGrant, UserNodeLook
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario
from bai_scenario.seeds.domain.domain import TestSeedDomain
from bai_scenario.seeds.resource_policy.keypair import TestSeedKeypairPolicy
from bai_scenario.seeds.resource_policy.project import TestSeedProjectPolicy
from bai_scenario.seeds.resource_policy.user import TestSeedUserPolicy
from bai_scenario.seeds.seeder import Laid, TestSeeder, TestSeedNest
from bai_scenario.seeds.user.user import TestSeedUserOf

type Loaded = list[UserNode | Exception | None]
type Answer = (
    tuple[DeleteUserPayload | RestoreUserPayload, UserNode]
    | tuple[PurgeUserPayload, Loaded]
    | DeleteUserPayload
    | RestoreUserPayload
    | PurgeUserPayload
    | BulkPurgeUsersPayload
    | UserNode
    | BulkUpdateUsersPayload
)

RENAMED = "renamed"
"""수정으로 바꿔 넣는 전체 이름. 시나리오가 정한 값이다."""


@dataclass(frozen=True)
class ACallerAndATarget:
    """부르는 사람, 건드릴 사람, 그리고 지운 뒤를 읽어 볼 슈퍼관리자."""

    caller: UserData
    target: UserData
    overseer: UserData | None


@dataclass(frozen=True)
class ASuperadminAndUsers:
    """일괄로 지우는 사람과, 지울 사용자들. `missing`은 어떤 사용자도 아닌 id다."""

    caller: UserData
    users: tuple[UserData, ...]
    missing: UUID | None


@dataclass(frozen=True)
class SomeoneStandingAs(TestSeedNest[Laid[UserData]]):
    """그 도메인에 속한 사용자 한 명을 `status` 상태로. 매니저가 사용자를 만드는 경로를 그대로 탄다."""

    domain: Laid[DomainData]
    status: UserStatus

    @override
    def kind(self) -> str:
        return Says(
            f"도메인에 속한 {self.status.value} 상태 사용자 한 명 준비",
            english=f"Prepare one {self.status.value} user in the domain",
        )

    @override
    def lay(self, seed: TestSeeder) -> Laid[UserData]:
        seed.once(TestSeedProjectPolicy())
        policy = seed.creating(TestSeedUserPolicy())
        key_policy = seed.creating(TestSeedKeypairPolicy())
        return seed.provisioning(
            TestSeedUserOf(is_active=False, status=self.status), self.domain, policy, key_policy
        )


@dataclass(frozen=True)
class ATargetAndSomeone(Given[Any, ACallerAndATarget]):
    """한 도메인의 대상 사용자와 부르는 사람. 부르는 사람은 대상 사용자에 `permissions`를 받는다."""

    permissions: tuple[Permission, ...] = ()
    target_status: UserStatus = UserStatus.ACTIVE
    overseer: bool = False

    @override
    def describe(self) -> str:
        if self.target_status == UserStatus.ACTIVE:
            state_ko, state_en = "사용자", "user"
        else:
            state_ko = f"{self.target_status.value} 상태 사용자"
            state_en = f"{self.target_status.value} user"
        if self.permissions:
            names = ", ".join(str(p.name) for p in self.permissions)
            granted_ko = f", 부르는 사람은 대상에 대한 사용자 {names} 권한을 받았습니다"
            granted_en = f", with the caller holding the user {names} permission on the target"
        else:
            granted_ko = ", 부르는 사람은 아무 권한도 받지 않았습니다"
            granted_en = ", with the caller holding no permission"
        return Says(
            f"도메인 하나와 대상 {state_ko} 하나, 부르는 사람 하나{granted_ko}",
            english=f"one domain, one target {state_en}, and one caller{granted_en}",
        )

    @override
    async def lay(self, seeding: Any) -> ACallerAndATarget:
        domain = await seeding.creating(TestSeedDomain(name_hint="home", description=WAS_HERE))
        target = await seeding.within(
            SomeoneOf(domain)
            if self.target_status == UserStatus.ACTIVE
            else SomeoneStandingAs(domain, self.target_status)
        )
        caller = await seeding.within(SomeoneOf(domain))
        if self.permissions:
            await seeding.within(AGrant.on_user(target, caller, *self.permissions))
        overseer = (
            await seeding.within(SomeoneOf(domain, role=UserRole.SUPERADMIN))
            if self.overseer
            else None
        )
        return ACallerAndATarget(
            seeding.made(caller),
            seeding.made(target),
            seeding.made(overseer) if overseer is not None else None,
        )


@dataclass(frozen=True)
class ASuperadminAndSomeUsers(Given[Any, ASuperadminAndUsers]):
    """한 도메인의 슈퍼관리자와 사용자 `count`명. `with_missing`이면 없는 id 하나를 곁들인다."""

    count: int
    with_missing: bool = False

    @override
    def describe(self) -> str:
        if self.with_missing:
            return Says(
                f"도메인 하나와 superadmin 하나, 사용자 {self.count}명, 그리고 어떤 사용자도 아닌 id 하나",
                english=(
                    f"one domain, one superadmin, {self.count} users, and an id that is no user"
                ),
            )
        return Says(
            f"도메인 하나와 superadmin 하나, 사용자 {self.count}명",
            english=f"one domain, one superadmin, and {self.count} users",
        )

    @override
    async def lay(self, seeding: Any) -> ASuperadminAndUsers:
        domain = await seeding.creating(TestSeedDomain(name_hint="home", description=WAS_HERE))
        users = [await seeding.within(SomeoneOf(domain)) for _ in range(self.count)]
        caller = await seeding.within(SomeoneOf(domain, role=UserRole.SUPERADMIN))
        return ASuperadminAndUsers(
            seeding.made(caller),
            tuple(seeding.made(one) for one in users),
            uuid4() if self.with_missing else None,
        )


@dataclass(frozen=True)
class SomeoneGrantedOnTheDomain(Given[Any, ASuperadminAndUsers]):
    """한 도메인의 사용자 하나와, 도메인 스코프에서 사용자 HARD_DELETE를 받은 사람."""

    @override
    def describe(self) -> str:
        return Says(
            "도메인 하나와 사용자 하나, 부르는 사람은 도메인 스코프의 사용자 HARD_DELETE 권한을 "
            "받았습니다",
            english=(
                "one domain and one user, and the caller holds the user HARD_DELETE permission "
                "in the domain scope"
            ),
        )

    @override
    async def lay(self, seeding: Any) -> ASuperadminAndUsers:
        domain = await seeding.creating(TestSeedDomain(name_hint="home", description=WAS_HERE))
        user = await seeding.within(SomeoneOf(domain))
        caller = await seeding.within(SomeoneOf(domain))
        await seeding.within(AGrant.on_domain(domain, caller, Permission.HARD_DELETE))
        return ASuperadminAndUsers(seeding.made(caller), (seeding.made(user),), None)


@dataclass(frozen=True)
class DeletingTheTarget(When[ACallerAndATarget, UserAdapter, Answer]):
    """대상 사용자를 물린다. `then_reading`이면 뒤이어 그 사용자를 읽는다."""

    then_reading: bool = True

    @override
    def operation(self) -> str:
        return "delete_user_by_id"

    @override
    def describe(self, laid: ACallerAndATarget) -> str:
        if self.then_reading:
            return Says(
                f"{laid.caller.username}이 {laid.target.username}을 삭제하고 다시 읽습니다",
                english=(
                    f"{laid.caller.username} deletes {laid.target.username} and reads it again"
                ),
            )
        return Says(
            f"{laid.caller.username}이 {laid.target.username}을 삭제합니다",
            english=f"{laid.caller.username} deletes {laid.target.username}",
        )

    @override
    async def call(self, adapter: UserAdapter, laid: ACallerAndATarget) -> Answer:
        with ActingAs(laid.caller):
            payload = await adapter.delete_user_by_id(DeleteUserInput(user_id=laid.target.id))
            if not self.then_reading:
                return payload
            node = (await adapter.get(laid.target.id)).user
        return payload, node


@dataclass(frozen=True)
class RestoringTheTarget(When[ACallerAndATarget, UserAdapter, Answer]):
    """대상 사용자를 되살린다. `then_reading`이면 뒤이어 그 사용자를 읽는다."""

    then_reading: bool = True

    @override
    def operation(self) -> str:
        return "restore_user_by_id"

    @override
    def describe(self, laid: ACallerAndATarget) -> str:
        if self.then_reading:
            return Says(
                f"{laid.caller.username}이 {laid.target.username}을 복원하고 다시 읽습니다",
                english=(
                    f"{laid.caller.username} restores {laid.target.username} and reads it again"
                ),
            )
        return Says(
            f"{laid.caller.username}이 {laid.target.username}을 복원합니다",
            english=f"{laid.caller.username} restores {laid.target.username}",
        )

    @override
    async def call(self, adapter: UserAdapter, laid: ACallerAndATarget) -> Answer:
        with ActingAs(laid.caller):
            payload = await adapter.restore_user_by_id(RestoreUserInput(user_id=laid.target.id))
            if not self.then_reading:
                return payload
            node = (await adapter.get(laid.target.id)).user
        return payload, node


@dataclass(frozen=True)
class PurgingTheTarget(When[ACallerAndATarget, UserAdapter, Answer]):
    """대상 사용자를 지운다. 넘겨받을 관리자는 부르는 사람이고, `to_nobody`면 없는 id다.

    지켜보는 슈퍼관리자가 있으면 뒤이어 그 사람이 대상을 일괄로 읽는다.
    """

    to_nobody: bool = False

    @override
    def operation(self) -> str:
        return "purge_user_by_id"

    @override
    def describe(self, laid: ACallerAndATarget) -> str:
        heir_ko = "없는 관리자 id" if self.to_nobody else "자기"
        heir_en = "an admin id that does not exist" if self.to_nobody else "themselves"
        if laid.overseer is not None:
            return Says(
                f"{laid.caller.username}이 {heir_ko}에게 넘기며 {laid.target.username}을 "
                f"영구 삭제하고, 뒤이어 {laid.overseer.username}이 일괄 읽습니다",
                english=(
                    f"{laid.caller.username} purges {laid.target.username} handing it over to "
                    f"{heir_en}, and {laid.overseer.username} batch reads it afterwards"
                ),
            )
        return Says(
            f"{laid.caller.username}이 {heir_ko}에게 넘기며 {laid.target.username}을 영구 삭제합니다",
            english=(
                f"{laid.caller.username} purges {laid.target.username} handing it over to {heir_en}"
            ),
        )

    @override
    async def call(self, adapter: UserAdapter, laid: ACallerAndATarget) -> Answer:
        heir = uuid4() if self.to_nobody else laid.caller.id
        with ActingAs(laid.caller):
            payload = await adapter.purge_user_by_id(
                PurgeUserInput(user_id=laid.target.id), admin_user_id=heir
            )
        if laid.overseer is None:
            return payload
        with ActingAs(laid.overseer):
            loaded = await adapter.batch_load_by_ids([UserID(laid.target.id)])
        return payload, loaded


@dataclass(frozen=True)
class PurgingInBulk(When[ASuperadminAndUsers, UserAdapter, Answer]):
    """사용자들을, 있으면 없는 id까지 함께 일괄로 지운다. 넘겨받는 사람은 부르는 사람이다."""

    @override
    def operation(self) -> str:
        return "bulk_purge_users"

    @override
    def describe(self, laid: ASuperadminAndUsers) -> str:
        names = ", ".join(one.username for one in laid.users)
        if laid.missing is not None:
            return Says(
                f"{laid.caller.username}이 {names}와 없는 id 를 일괄로 영구 삭제합니다",
                english=(
                    f"{laid.caller.username} bulk purges {names} and an id that does not exist"
                ),
            )
        return Says(
            f"{laid.caller.username}이 {names}를 일괄로 영구 삭제합니다",
            english=f"{laid.caller.username} bulk purges {names}",
        )

    @override
    async def call(self, adapter: UserAdapter, laid: ASuperadminAndUsers) -> Answer:
        ids = [one.id for one in laid.users]
        if laid.missing is not None:
            ids.append(laid.missing)
        with ActingAs(laid.caller):
            return await adapter.bulk_purge_users(
                BulkPurgeUserAction(user_ids=ids, admin_user_id=laid.caller.id)
            )


@dataclass(frozen=True)
class NoKey(Condition[str | None]):
    """기본 키가 비어 있다. 비활성 사용자의 기본 키는 활성이 아니다."""

    @override
    def says(self) -> str:
        return Says(
            "활성 기본 키가 없어 비어 있습니다",
            english="it is empty because there is no active default key",
        )

    @override
    def holds(self, got: str | None) -> bool:
        return got is None


@dataclass(frozen=True)
class TheTargetNowStands(Then[ACallerAndATarget, Answer]):
    """성공이 오고, 다시 읽은 대상은 `status` 상태다."""

    started: datetime
    status: str
    key_is_active: bool = True

    @override
    def says(self) -> str:
        return Says(
            f"성공이 오고, 다시 읽은 사용자는 {self.status} 상태입니다",
            english=f"the call succeeds and the user read back is in the {self.status} state",
        )

    @override
    def look(self, laid: ACallerAndATarget, answered: Answered[Answer]) -> list[Verdict]:
        answer = answered.response
        if not isinstance(answer, tuple) or not isinstance(answer[1], UserNode):
            return [Refused(NotEnoughPermission, answered.raised)]
        payload, node = answer
        expected = dataclasses.replace(
            laid.target, status=self.status, status_info="admin-requested"
        )
        return [
            Same("success", payload.success, True),
            *UserNodeLook(self.started).verdicts(
                node,
                expected,
                main_access_key=None if self.key_is_active else NoKey(),
                at="the read that follows.",
            ),
        ]


@dataclass(frozen=True)
class TheTargetIsGone(Then[ACallerAndATarget, Answer]):
    """성공이 오고, 슈퍼관리자가 일괄로 읽으면 그 자리가 비어 온다."""

    @override
    def says(self) -> str:
        return Says(
            "성공이 오고, 그 사용자를 더 찾을 수 없습니다",
            english="the call succeeds and that user is no longer found",
        )

    @override
    def look(self, laid: ACallerAndATarget, answered: Answered[Answer]) -> list[Verdict]:
        answer = answered.response
        if not isinstance(answer, tuple) or not isinstance(answer[1], list):
            return [Refused(NotEnoughPermission, answered.raised)]
        payload, loaded = answer
        return [
            Same("success", payload.success, True),
            Skipped(
                "the batch read that follows",
                Says(
                    "없는 id 에 superadmin 이 받는 응답은 아직 정해지지 않았습니다",
                    english=("the response a superadmin gets for a missing id is not decided yet"),
                ),
            ),
        ]


@dataclass(frozen=True)
class EveryoneIsPurged(Then[ASuperadminAndUsers, Answer]):
    """심은 사용자가 모두 지워지고, 없는 id가 있으면 그것만 실패로 담긴다."""

    @override
    def says(self) -> str:
        return Says(
            "삭제한 사용자 id 와 개수, 그리고 실패가 응답으로 옵니다",
            english="the purged user ids, the count, and the failures come back",
        )

    @override
    def look(self, laid: ASuperadminAndUsers, answered: Answered[Answer]) -> list[Verdict]:
        payload = answered.response
        if not isinstance(payload, BulkPurgeUsersPayload):
            return [Refused(InsufficientPrivilege, answered.raised)]
        seen: list[Verdict] = [
            Held(
                "successes",
                list(payload.successes),
                SameAs(
                    [one.id for one in laid.users],
                    Says("미리 저장한 사용자 전부", english="every user seeded in advance"),
                ),
            ),
            Same("purged_count", payload.purged_count, len(laid.users)),
        ]
        if laid.missing is None:
            seen.append(Same("failed", list(payload.failed), []))
        else:
            seen.append(
                Held(
                    "failed.user_id",
                    [one.user_id for one in payload.failed],
                    SameAs(
                        [laid.missing],
                        Says("없는 id", english="an id that does not exist"),
                    ),
                )
            )
            seen.append(
                Skipped(
                    "failed.message",
                    Says(
                        "예외 메시지는 변경되어도 되는 값입니다",
                        english="the exception message may change",
                    ),
                )
            )
        return seen


@dataclass(frozen=True)
class AGrantedUserDeletesAUser(
    Scenario[TestSeedingSession, ACallerAndATarget, UserAdapter, Answer]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-user-granted-soft-delete-marks-another-user-deleted"

    @override
    def describe(self) -> str:
        return Says(
            "대상 사용자 스코프에서 SOFT_DELETE 를 받은 사용자가 삭제하면, "
            "성공이 오고 그 사용자 상태가 삭제로 변경됩니다",
            english=(
                "when a user granted SOFT_DELETE in the target user scope deletes the user, "
                "success comes back and the state of that user changes to deleted"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ACallerAndATarget]:
        return ATargetAndSomeone(permissions=(Permission.SOFT_DELETE, Permission.READ))

    @override
    def when(self) -> When[ACallerAndATarget, UserAdapter, Answer]:
        return DeletingTheTarget()

    @override
    def then(self) -> Then[ACallerAndATarget, Answer]:
        return TheTargetNowStands(started=self.started, status="deleted")


@dataclass(frozen=True)
class AUserGrantedNothingMayNotDelete(
    Scenario[TestSeedingSession, ACallerAndATarget, UserAdapter, Answer]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-delete-another-user"

    @override
    def describe(self) -> str:
        return Says(
            "역할 없이 삭제하려 하면, 엔티티 권한 문이 막습니다",
            english=(
                "a user holding no role who tries to delete a user is rejected by the entity "
                "permission gate"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ACallerAndATarget]:
        return ATargetAndSomeone()

    @override
    def when(self) -> When[ACallerAndATarget, UserAdapter, Answer]:
        return DeletingTheTarget(then_reading=False)

    @override
    def then(self) -> Then[ACallerAndATarget, Answer]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class AGrantedUserRestoresADeletedUser(
    Scenario[TestSeedingSession, ACallerAndATarget, UserAdapter, Answer]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-user-granted-soft-delete-restores-a-deleted-user-to-active"

    @override
    def describe(self) -> str:
        return Says(
            "대상 사용자 스코프에서 SOFT_DELETE 를 받은 사용자가 삭제 상태 사용자를 복원하면, "
            "성공이 오고 상태가 활성으로 변경됩니다",
            english=(
                "when a user granted SOFT_DELETE in the target user scope restores a deleted "
                "user, success comes back and the state changes to active"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ACallerAndATarget]:
        return ATargetAndSomeone(
            permissions=(Permission.SOFT_DELETE, Permission.READ),
            target_status=UserStatus.DELETED,
        )

    @override
    def when(self) -> When[ACallerAndATarget, UserAdapter, Answer]:
        return RestoringTheTarget()

    @override
    def then(self) -> Then[ACallerAndATarget, Answer]:
        return TheTargetNowStands(started=self.started, status="active", key_is_active=False)


@dataclass(frozen=True)
class RestoringAUserWhoWasNotDeletedIsRefused(
    Scenario[TestSeedingSession, ACallerAndATarget, UserAdapter, Answer]
):
    @override
    def summary(self) -> str:
        return "restoring-a-user-who-was-not-deleted-is-refused"

    @override
    def describe(self) -> str:
        return Says(
            "권한 받은 사용자가 삭제되지 않은 비활성 사용자를 복원하려 하면, "
            "삭제 상태가 아니라 거부됩니다",
            english=(
                "when a user holding the permission tries to restore an inactive user that was "
                "not deleted, it is rejected because the user is not deleted"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ACallerAndATarget]:
        return ATargetAndSomeone(
            permissions=(Permission.SOFT_DELETE, Permission.READ),
            target_status=UserStatus.INACTIVE,
        )

    @override
    def when(self) -> When[ACallerAndATarget, UserAdapter, Answer]:
        return RestoringTheTarget(then_reading=False)

    @override
    def then(self) -> Then[ACallerAndATarget, Answer]:
        return TheCallIsRefused(UserModificationBadRequest)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotRestore(
    Scenario[TestSeedingSession, ACallerAndATarget, UserAdapter, Answer]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-restore-another-user"

    @override
    def describe(self) -> str:
        return Says(
            "역할 없이 복원하려 하면, 엔티티 권한 문이 막습니다",
            english=(
                "a user holding no role who tries to restore a user is rejected by the entity "
                "permission gate"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ACallerAndATarget]:
        return ATargetAndSomeone(target_status=UserStatus.DELETED)

    @override
    def when(self) -> When[ACallerAndATarget, UserAdapter, Answer]:
        return RestoringTheTarget(then_reading=False)

    @override
    def then(self) -> Then[ACallerAndATarget, Answer]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class AGrantedUserPurgesAUser(Scenario[TestSeedingSession, ACallerAndATarget, UserAdapter, Answer]):
    @override
    def summary(self) -> str:
        return "a-user-granted-hard-delete-purges-a-user-with-no-folders-or-sessions"

    @override
    def describe(self) -> str:
        return Says(
            "대상 사용자 스코프에서 HARD_DELETE 를 받은 사용자가 삭제되지 않은 사용자를 "
            "영구 삭제해도, 성공이 오고 그 사용자를 더 찾을 수 없습니다",
            english=(
                "when a user granted HARD_DELETE in the target user scope purges a user that "
                "was not deleted, success comes back and that user is no longer found"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ACallerAndATarget]:
        return ATargetAndSomeone(permissions=(Permission.HARD_DELETE,), overseer=True)

    @override
    def when(self) -> When[ACallerAndATarget, UserAdapter, Answer]:
        return PurgingTheTarget()

    @override
    def then(self) -> Then[ACallerAndATarget, Answer]:
        return TheTargetIsGone()


@dataclass(frozen=True)
class AUserGrantedNothingMayNotPurge(
    Scenario[TestSeedingSession, ACallerAndATarget, UserAdapter, Answer]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-purge-another-user"

    @override
    def describe(self) -> str:
        return Says(
            "역할 없이 영구 삭제하려 하면, 엔티티 권한 문이 막습니다",
            english=(
                "a user holding no role who tries to purge a user is rejected by the entity "
                "permission gate"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ACallerAndATarget]:
        return ATargetAndSomeone()

    @override
    def when(self) -> When[ACallerAndATarget, UserAdapter, Answer]:
        return PurgingTheTarget()

    @override
    def then(self) -> Then[ACallerAndATarget, Answer]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class PurgingToNobodyIsRefused(
    Scenario[TestSeedingSession, ACallerAndATarget, UserAdapter, Answer]
):
    @override
    def summary(self) -> str:
        return "purging-a-user-to-an-admin-who-does-not-exist-is-refused"

    @override
    def describe(self) -> str:
        return Says(
            "권한 받은 사용자가 넘겨받을 관리자로 없는 id 를 주면, 입력 검증이 막습니다",
            english=(
                "when a user holding the permission gives an admin id that does not exist as "
                "the heir, input validation rejects it"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ACallerAndATarget]:
        return ATargetAndSomeone(permissions=(Permission.HARD_DELETE,))

    @override
    def when(self) -> When[ACallerAndATarget, UserAdapter, Answer]:
        return PurgingTheTarget(to_nobody=True)

    @override
    def then(self) -> Then[ACallerAndATarget, Answer]:
        return TheCallIsRefused(UserNotFound)


@dataclass(frozen=True)
class TheSuperadminPurgesTwoInBulk(
    Scenario[TestSeedingSession, ASuperadminAndUsers, UserAdapter, Answer]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-bulk-purge-answers-the-purged-ids-and-count"

    @override
    def describe(self) -> str:
        return Says(
            "전역 역할이 문인 일괄 영구 삭제에서 superadmin 이 사용자 둘을 주면, "
            "두 id 와 개수 둘이 응답으로 옵니다",
            english=(
                "when the superadmin gives two users in a bulk purge gated by the global role, "
                "the two ids and a count of two come back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ASuperadminAndUsers]:
        return ASuperadminAndSomeUsers(count=2)

    @override
    def when(self) -> When[ASuperadminAndUsers, UserAdapter, Answer]:
        return PurgingInBulk()

    @override
    def then(self) -> Then[ASuperadminAndUsers, Answer]:
        return EveryoneIsPurged()


@dataclass(frozen=True)
class ABulkPurgeRecordsAMissingIdAsAFailure(
    Scenario[TestSeedingSession, ASuperadminAndUsers, UserAdapter, Answer]
):
    @override
    def summary(self) -> str:
        return "a-bulk-purge-records-a-missing-id-as-a-failure"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 있는 사용자와 없는 id 를 함께 주면, "
            "하나는 영구 삭제되고 없는 id 는 실패로 담깁니다",
            english=(
                "when the superadmin gives an existing user and a missing id together, one is "
                "purged and the missing id comes back as failed"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ASuperadminAndUsers]:
        return ASuperadminAndSomeUsers(count=1, with_missing=True)

    @override
    def when(self) -> When[ASuperadminAndUsers, UserAdapter, Answer]:
        return PurgingInBulk()

    @override
    def then(self) -> Then[ASuperadminAndUsers, Answer]:
        return EveryoneIsPurged()


@dataclass(frozen=True)
class AUserWhoIsNotTheSuperadminMayNotPurgeInBulk(
    Scenario[TestSeedingSession, ASuperadminAndUsers, UserAdapter, Answer]
):
    @override
    def summary(self) -> str:
        return "a-user-who-is-not-the-superadmin-may-not-purge-in-bulk"

    @override
    def describe(self) -> str:
        return Says(
            "도메인 스코프에서 HARD_DELETE 를 받은 사용자라도 일괄 영구 삭제를 하려 하면, "
            "전역 역할 문이 막습니다",
            english=(
                "even a user granted HARD_DELETE in the domain scope is rejected by the global "
                "role gate when purging in bulk"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ASuperadminAndUsers]:
        return SomeoneGrantedOnTheDomain()

    @override
    def when(self) -> When[ASuperadminAndUsers, UserAdapter, Answer]:
        return PurgingInBulk()

    @override
    def then(self) -> Then[ASuperadminAndUsers, Answer]:
        return TheCallIsRefused(InsufficientPrivilege)


@dataclass(frozen=True)
class ASuperadminAndThreeTargets:
    """일괄로 고치는 슈퍼관리자와, 활성 사용자 하나, 삭제 상태 사용자 둘."""

    caller: UserData
    active: UserData
    deleted: UserData
    other_deleted: UserData


@dataclass(frozen=True)
class ASuperadminWithActiveAndDeleted(Given[Any, ASuperadminAndThreeTargets]):
    """한 도메인의 슈퍼관리자와, 활성 사용자 하나, 삭제 상태 사용자 둘."""

    @override
    def describe(self) -> str:
        return Says(
            "도메인 하나와 superadmin 하나, 활성 사용자 하나, 삭제 상태 사용자 둘",
            english=("one domain, one superadmin, one active user, and two deleted users"),
        )

    @override
    async def lay(self, seeding: Any) -> ASuperadminAndThreeTargets:
        domain = await seeding.creating(TestSeedDomain(name_hint="home", description=WAS_HERE))
        active = await seeding.within(SomeoneOf(domain))
        deleted = await seeding.within(SomeoneStandingAs(domain, UserStatus.DELETED))
        other_deleted = await seeding.within(SomeoneStandingAs(domain, UserStatus.DELETED))
        caller = await seeding.within(SomeoneOf(domain, role=UserRole.SUPERADMIN))
        return ASuperadminAndThreeTargets(
            seeding.made(caller),
            seeding.made(active),
            seeding.made(deleted),
            seeding.made(other_deleted),
        )


@dataclass(frozen=True)
class EditingTheTarget(When[ACallerAndATarget, UserAdapter, Answer]):
    """대상 사용자를 `input`으로 수정한다."""

    input: UpdateUserInput
    says_what: str

    @override
    def operation(self) -> str:
        return "update_user_by_id"

    @override
    def describe(self, laid: ACallerAndATarget) -> str:
        return Says(
            f"{laid.caller.username}이 {laid.target.username}의 {self.says_what}",
            english=(
                f"{laid.caller.username} edits {laid.target.username}: "
                f"{in_language(self.says_what, Language.ENGLISH)}"
            ),
        )

    @override
    async def call(self, adapter: UserAdapter, laid: ACallerAndATarget) -> Answer:
        with ActingAs(laid.caller):
            payload = await adapter.update_user_by_id(laid.target.id, self.input)
        return payload.user


@dataclass(frozen=True)
class BulkEditingTheStatuses(When[ASuperadminAndThreeTargets, UserAdapter, Answer]):
    """활성 사용자는 DELETED로, 삭제 상태 사용자 하나는 ACTIVE로, 다른 하나는 전체 이름만 고친다."""

    @override
    def operation(self) -> str:
        return "bulk_update_users"

    @override
    def describe(self, laid: ASuperadminAndThreeTargets) -> str:
        return Says(
            f"{laid.caller.username}이 {laid.active.username}에 DELETED, "
            f"{laid.deleted.username}에 ACTIVE, {laid.other_deleted.username}에 전체 이름을 "
            "일괄 수정으로 줍니다",
            english=(
                f"{laid.caller.username} bulk edits: DELETED for {laid.active.username}, "
                f"ACTIVE for {laid.deleted.username}, and a full name for "
                f"{laid.other_deleted.username}"
            ),
        )

    @override
    async def call(self, adapter: UserAdapter, laid: ASuperadminAndThreeTargets) -> Answer:
        input = BulkUpdateUsersInput(
            users=[
                BulkUpdateUserItemInput(
                    user_id=laid.active.id, input=UpdateUserInput(status=UserStatusDTO.DELETED)
                ),
                BulkUpdateUserItemInput(
                    user_id=laid.deleted.id, input=UpdateUserInput(status=UserStatusDTO.ACTIVE)
                ),
                BulkUpdateUserItemInput(
                    user_id=laid.other_deleted.id, input=UpdateUserInput(full_name=RENAMED)
                ),
            ]
        )
        with ActingAs(laid.caller):
            return await adapter.bulk_update_users(input)


@dataclass(frozen=True)
class TheEditedNodeStands(Then[ACallerAndATarget, Answer]):
    """수정의 답으로 `status` 상태의 사용자 전체가 온다."""

    started: datetime
    status: str
    key_is_active: bool = True

    @override
    def says(self) -> str:
        return Says(
            f"{self.status} 상태의 사용자 전체가 응답으로 옵니다",
            english=f"the whole user in the {self.status} state comes back",
        )

    @override
    def look(self, laid: ACallerAndATarget, answered: Answered[Answer]) -> list[Verdict]:
        node = answered.response
        if not isinstance(node, UserNode):
            return [Refused(NotEnoughPermission, answered.raised)]
        expected = dataclasses.replace(
            laid.target, status=self.status, status_info="admin-requested"
        )
        return UserNodeLook(self.started).verdicts(
            node, expected, main_access_key=None if self.key_is_active else NoKey()
        )


@dataclass(frozen=True)
class TheDeletedTargetIsUntouched(Then[ACallerAndATarget, Answer]):
    """이미 삭제 상태인 대상 사용자가 그대로 온다."""

    started: datetime

    @override
    def says(self) -> str:
        return Says(
            "삭제 상태 그대로인 사용자 전체가 응답으로 옵니다",
            english="the whole user still in the deleted state comes back",
        )

    @override
    def look(self, laid: ACallerAndATarget, answered: Answered[Answer]) -> list[Verdict]:
        node = answered.response
        if not isinstance(node, UserNode):
            return [Refused(NotEnoughPermission, answered.raised)]
        return UserNodeLook(self.started).verdicts(node, laid.target, main_access_key=NoKey())


@dataclass(frozen=True)
class DeletedAndRestoredOneRefused(Then[ASuperadminAndThreeTargets, Answer]):
    """물린 사용자와 되살린 사용자는 수정 목록에, 삭제 상태에서 이름만 고친 사용자는 실패로 온다."""

    started: datetime

    @override
    def says(self) -> str:
        return Says(
            "삭제한 사용자와 복원한 사용자가 수정 목록에, 나머지 하나가 실패 목록에 옵니다",
            english=(
                "the deleted user and the restored user come back in the updated list and the "
                "remaining one in the failed list"
            ),
        )

    @override
    def look(self, laid: ASuperadminAndThreeTargets, answered: Answered[Answer]) -> list[Verdict]:
        payload = answered.response
        if not isinstance(payload, BulkUpdateUsersPayload):
            return [Refused(InsufficientPrivilege, answered.raised)]
        by_id = {node.id: node for node in payload.updated_users}
        seen: list[Verdict] = [
            Held(
                "updated_users.id",
                sorted(str(node.id) for node in payload.updated_users),
                SameAs(
                    sorted([str(laid.active.id), str(laid.deleted.id)]),
                    Says(
                        "DELETED 와 ACTIVE 를 준 사용자",
                        english="the users given DELETED and ACTIVE",
                    ),
                ),
            ),
            Held(
                "failed.user_id",
                [one.user_id for one in payload.failed],
                SameAs(
                    [laid.other_deleted.id],
                    Says(
                        "삭제 상태에서 전체 이름만 변경한 사용자",
                        english="the deleted user whose full name alone was changed",
                    ),
                ),
            ),
            Skipped(
                "failed.message",
                Says(
                    "예외 메시지는 변경되어도 되는 값입니다",
                    english="the exception message may change",
                ),
            ),
        ]
        if laid.active.id in by_id:
            seen.extend(
                UserNodeLook(self.started).verdicts(
                    by_id[laid.active.id],
                    dataclasses.replace(
                        laid.active, status="deleted", status_info="admin-requested"
                    ),
                    at="updated_users[deleted user].",
                )
            )
        if laid.deleted.id in by_id:
            seen.extend(
                UserNodeLook(self.started).verdicts(
                    by_id[laid.deleted.id],
                    dataclasses.replace(
                        laid.deleted, status="active", status_info="admin-requested"
                    ),
                    main_access_key=NoKey(),
                    at="updated_users[restored user].",
                )
            )
        return seen


@dataclass(frozen=True)
class EditingToDeletedDeletes(Scenario[TestSeedingSession, ACallerAndATarget, UserAdapter, Answer]):
    started: datetime

    @override
    def summary(self) -> str:
        return "an-edit-to-deleted-soft-deletes-the-user"

    @override
    def describe(self) -> str:
        return Says(
            "대상 사용자 스코프에서 SOFT_DELETE 와 READ 를 받은 사용자가 수정으로 DELETED 를 주면, "
            "삭제와 같이 삭제 상태가 됩니다",
            english=(
                "when a user granted SOFT_DELETE and READ in the target user scope gives "
                "DELETED in an edit, the user enters the deleted state as with a delete"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ACallerAndATarget]:
        return ATargetAndSomeone(permissions=(Permission.SOFT_DELETE, Permission.READ))

    @override
    def when(self) -> When[ACallerAndATarget, UserAdapter, Answer]:
        return EditingTheTarget(
            UpdateUserInput(status=UserStatusDTO.DELETED),
            Says("상태에 DELETED 를 줍니다", english="sets the status to DELETED"),
        )

    @override
    def then(self) -> Then[ACallerAndATarget, Answer]:
        return TheEditedNodeStands(started=self.started, status="deleted")


@dataclass(frozen=True)
class EditingToDeletedNeedsSoftDelete(
    Scenario[TestSeedingSession, ACallerAndATarget, UserAdapter, Answer]
):
    @override
    def summary(self) -> str:
        return "an-edit-to-deleted-is-refused-without-soft-delete"

    @override
    def describe(self) -> str:
        return Says(
            "대상 사용자 스코프에서 UPDATE 와 READ 만 받은 사용자가 수정으로 DELETED 를 주면, "
            "삭제의 엔티티 권한 문이 막습니다",
            english=(
                "when a user granted only UPDATE and READ in the target user scope gives "
                "DELETED in an edit, the entity permission gate of the delete rejects it"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ACallerAndATarget]:
        return ATargetAndSomeone(permissions=(Permission.UPDATE, Permission.READ))

    @override
    def when(self) -> When[ACallerAndATarget, UserAdapter, Answer]:
        return EditingTheTarget(
            UpdateUserInput(status=UserStatusDTO.DELETED),
            Says("상태에 DELETED 를 줍니다", english="sets the status to DELETED"),
        )

    @override
    def then(self) -> Then[ACallerAndATarget, Answer]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class EditingADeletedUserToDeletedChangesNothing(
    Scenario[TestSeedingSession, ACallerAndATarget, UserAdapter, Answer]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "an-edit-to-deleted-on-a-deleted-user-changes-nothing"

    @override
    def describe(self) -> str:
        return Says(
            "삭제 상태 사용자에 수정으로 DELETED 만 주면, "
            "아무것도 변경되지 않고 그 사용자가 응답으로 옵니다",
            english=(
                "when only DELETED is given in an edit of a deleted user, nothing changes and "
                "that user comes back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ACallerAndATarget]:
        return ATargetAndSomeone(
            permissions=(Permission.SOFT_DELETE, Permission.READ),
            target_status=UserStatus.DELETED,
        )

    @override
    def when(self) -> When[ACallerAndATarget, UserAdapter, Answer]:
        return EditingTheTarget(
            UpdateUserInput(status=UserStatusDTO.DELETED),
            Says("상태에 DELETED 를 줍니다", english="sets the status to DELETED"),
        )

    @override
    def then(self) -> Then[ACallerAndATarget, Answer]:
        return TheDeletedTargetIsUntouched(started=self.started)


@dataclass(frozen=True)
class EditingADeletedUserToActiveRestores(
    Scenario[TestSeedingSession, ACallerAndATarget, UserAdapter, Answer]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "an-edit-to-active-on-a-deleted-user-restores-the-user"

    @override
    def describe(self) -> str:
        return Says(
            "대상 사용자 스코프에서 SOFT_DELETE 와 READ 를 받은 사용자가 삭제 상태 사용자에 "
            "수정으로 ACTIVE 를 주면, 복원과 같이 활성이 됩니다",
            english=(
                "when a user granted SOFT_DELETE and READ in the target user scope gives ACTIVE "
                "in an edit of a deleted user, the user becomes active as with a restore"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ACallerAndATarget]:
        return ATargetAndSomeone(
            permissions=(Permission.SOFT_DELETE, Permission.READ),
            target_status=UserStatus.DELETED,
        )

    @override
    def when(self) -> When[ACallerAndATarget, UserAdapter, Answer]:
        return EditingTheTarget(
            UpdateUserInput(status=UserStatusDTO.ACTIVE),
            Says("상태에 ACTIVE 를 줍니다", english="sets the status to ACTIVE"),
        )

    @override
    def then(self) -> Then[ACallerAndATarget, Answer]:
        return TheEditedNodeStands(started=self.started, status="active", key_is_active=False)


@dataclass(frozen=True)
class EditingADeletedUserIsRefused(
    Scenario[TestSeedingSession, ACallerAndATarget, UserAdapter, Answer]
):
    @override
    def summary(self) -> str:
        return "an-edit-of-another-field-on-a-deleted-user-is-refused"

    @override
    def describe(self) -> str:
        return Says(
            "대상 사용자 스코프에서 UPDATE 와 READ 를 받은 사용자가 삭제 상태 사용자의 "
            "전체 이름을 변경하면, 삭제된 사용자라 거부됩니다",
            english=(
                "when a user granted UPDATE and READ in the target user scope changes the full "
                "name of a deleted user, it is rejected because the user is deleted"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ACallerAndATarget]:
        return ATargetAndSomeone(
            permissions=(Permission.UPDATE, Permission.READ),
            target_status=UserStatus.DELETED,
        )

    @override
    def when(self) -> When[ACallerAndATarget, UserAdapter, Answer]:
        return EditingTheTarget(
            UpdateUserInput(full_name=RENAMED),
            Says("전체 이름을 변경합니다", english="changes the full name"),
        )

    @override
    def then(self) -> Then[ACallerAndATarget, Answer]:
        return TheCallIsRefused(UserDeleted)


@dataclass(frozen=True)
class EditingToAnotherStatusIsRefused(
    Scenario[TestSeedingSession, ACallerAndATarget, UserAdapter, Answer]
):
    @override
    def summary(self) -> str:
        return "an-edit-to-a-status-other-than-active-or-inactive-is-refused"

    @override
    def describe(self) -> str:
        return Says(
            "대상 사용자 스코프에서 UPDATE 와 READ 를 받은 사용자가 수정으로 "
            "BEFORE_VERIFICATION 을 주면, 입력 검증이 막습니다",
            english=(
                "when a user granted UPDATE and READ in the target user scope gives "
                "BEFORE_VERIFICATION in an edit, input validation rejects it"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ACallerAndATarget]:
        return ATargetAndSomeone(permissions=(Permission.UPDATE, Permission.READ))

    @override
    def when(self) -> When[ACallerAndATarget, UserAdapter, Answer]:
        return EditingTheTarget(
            UpdateUserInput(status=UserStatusDTO.BEFORE_VERIFICATION),
            Says(
                "상태에 BEFORE_VERIFICATION 을 줍니다",
                english="sets the status to BEFORE_VERIFICATION",
            ),
        )

    @override
    def then(self) -> Then[ACallerAndATarget, Answer]:
        return TheCallIsRefused(UserModificationBadRequest)


@dataclass(frozen=True)
class ABulkEditDeletesAndRestoresPerItem(
    Scenario[TestSeedingSession, ASuperadminAndThreeTargets, UserAdapter, Answer]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-bulk-edit-deletes-and-restores-per-item-and-refuses-a-deleted-user-edit"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 일괄 수정으로 활성 사용자에 DELETED, 삭제 상태 사용자에 ACTIVE, "
            "다른 삭제 상태 사용자에 전체 이름을 주면, 둘은 삭제와 복원을 거쳐 수정 목록에, "
            "하나는 실패로 담깁니다",
            english=(
                "when the superadmin bulk edits with DELETED for an active user, ACTIVE for a "
                "deleted user, and a full name for another deleted user, the first two are "
                "deleted and restored and come back in the updated list, and the third comes "
                "back as failed"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ASuperadminAndThreeTargets]:
        return ASuperadminWithActiveAndDeleted()

    @override
    def when(self) -> When[ASuperadminAndThreeTargets, UserAdapter, Answer]:
        return BulkEditingTheStatuses()

    @override
    def then(self) -> Then[ASuperadminAndThreeTargets, Answer]:
        return DeletedAndRestoredOneRefused(started=self.started)


SCENARIOS: list[Scenario[TestSeedingSession, Any, UserAdapter, Answer]] = [
    AGrantedUserDeletesAUser(started=datetime.now(UTC)),
    AUserGrantedNothingMayNotDelete(),
    AGrantedUserRestoresADeletedUser(started=datetime.now(UTC)),
    RestoringAUserWhoWasNotDeletedIsRefused(),
    AUserGrantedNothingMayNotRestore(),
    AGrantedUserPurgesAUser(),
    AUserGrantedNothingMayNotPurge(),
    PurgingToNobodyIsRefused(),
    TheSuperadminPurgesTwoInBulk(),
    ABulkPurgeRecordsAMissingIdAsAFailure(),
    AUserWhoIsNotTheSuperadminMayNotPurgeInBulk(),
    EditingToDeletedDeletes(started=datetime.now(UTC)),
    EditingToDeletedNeedsSoftDelete(),
    EditingADeletedUserToDeletedChangesNothing(started=datetime.now(UTC)),
    EditingADeletedUserToActiveRestores(started=datetime.now(UTC)),
    EditingADeletedUserIsRefused(),
    EditingToAnotherStatusIsRefused(),
    ABulkEditDeletesAndRestoresPerItem(started=datetime.now(UTC)),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_retiring(
    scenario: Scenario[TestSeedingSession, Any, UserAdapter, Answer],
    adapter: UserAdapter,
    engine: ExtendedAsyncSAEngine,
) -> None:
    await run_scenario(scenario, adapter, engine)
