"""사용자 물리기, 되살리기, 지우기 — 무엇이 바뀌고 누가 할 수 있는가."""

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
    DeleteUserInput,
    PurgeUserInput,
    RestoreUserInput,
)
from ai.backend.common.dto.manager.v2.user.response import (
    BulkPurgeUsersPayload,
    DeleteUserPayload,
    PurgeUserPayload,
    RestoreUserPayload,
    UserNode,
)
from ai.backend.manager.api.adapters.user.adapter import UserAdapter
from ai.backend.manager.data.domain.types import DomainData
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.data.user.types import UserData, UserStatus
from ai.backend.manager.errors.auth import InsufficientPrivilege
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.errors.user import UserNotFound
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.services.user.actions.purge_user import BulkPurgeUserAction
from ai.backend.testutils.scenario_steps import (
    Answered,
    Condition,
    Given,
    Held,
    Refused,
    Same,
    SameAs,
    Scenario,
    Skipped,
    Then,
    Verdict,
    When,
)
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.domain import WAS_HERE, SomeoneOf
from bai_scenario.components.user import AGrant, UserNodeLook
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario
from bai_scenario.seeds.domain.domain import SeedDomain
from bai_scenario.seeds.resource_policy.keypair import SeedKeypairPolicy
from bai_scenario.seeds.resource_policy.project import SeedProjectPolicy
from bai_scenario.seeds.resource_policy.user import SeedUserPolicy
from bai_scenario.seeds.seeder import Laid, Seeder, SeedNest
from bai_scenario.seeds.user.user import SeedUserOf

type Loaded = list[UserNode | Exception | None]
type Answer = (
    tuple[DeleteUserPayload | RestoreUserPayload, UserNode]
    | tuple[PurgeUserPayload, Loaded]
    | DeleteUserPayload
    | RestoreUserPayload
    | PurgeUserPayload
    | BulkPurgeUsersPayload
)


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
class SomeoneStandingAs(SeedNest[Laid[UserData]]):
    """그 도메인에 속한 사용자 한 명을 `status` 상태로. 매니저가 사용자를 만드는 경로를 그대로 탄다."""

    domain: Laid[DomainData]
    status: UserStatus

    @override
    def kind(self) -> str:
        return f"도메인에 속한 {self.status.value} 상태 사용자 한 명 준비"

    @override
    def lay(self, seed: Seeder) -> Laid[UserData]:
        seed.once(SeedProjectPolicy())
        policy = seed.creating(SeedUserPolicy())
        key_policy = seed.creating(SeedKeypairPolicy())
        return seed.provisioning(
            SeedUserOf(is_active=False, status=self.status), self.domain, policy, key_policy
        )


@dataclass(frozen=True)
class ATargetAndSomeone(Given[Any, ACallerAndATarget]):
    """한 도메인의 대상 사용자와 부르는 사람. 부르는 사람은 대상 사용자에 `permissions`를 받는다."""

    permissions: tuple[Permission, ...] = ()
    target_status: UserStatus = UserStatus.ACTIVE
    overseer: bool = False

    @override
    def describe(self) -> str:
        state = (
            "사용자"
            if self.target_status == UserStatus.ACTIVE
            else f"{self.target_status.value} 상태 사용자"
        )
        granted = (
            f", 부르는 사람은 대상에 대한 사용자 {', '.join(str(p.name) for p in self.permissions)} 권한을 받았다"
            if self.permissions
            else ", 부르는 사람은 아무 권한도 받지 않았다"
        )
        return f"도메인 하나와 대상 {state} 하나, 부르는 사람 하나{granted}"

    @override
    async def lay(self, seeding: Any) -> ACallerAndATarget:
        domain = await seeding.creating(SeedDomain(name_hint="home", description=WAS_HERE))
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
        missing = ", 그리고 어떤 사용자도 아닌 id 하나" if self.with_missing else ""
        return f"도메인 하나와 슈퍼관리자 하나, 사용자 {self.count}명{missing}"

    @override
    async def lay(self, seeding: Any) -> ASuperadminAndUsers:
        domain = await seeding.creating(SeedDomain(name_hint="home", description=WAS_HERE))
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
        return "도메인 하나와 사용자 하나, 부르는 사람은 도메인 스코프의 사용자 HARD_DELETE 권한을 받았다"

    @override
    async def lay(self, seeding: Any) -> ASuperadminAndUsers:
        domain = await seeding.creating(SeedDomain(name_hint="home", description=WAS_HERE))
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
        after = " 뒤 다시 읽음" if self.then_reading else ""
        return f"{laid.caller.username}이 {laid.target.username}을 물림{after}"

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
        after = " 뒤 다시 읽음" if self.then_reading else ""
        return f"{laid.caller.username}이 {laid.target.username}을 되살림{after}"

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
        heir = "없는 관리자 id" if self.to_nobody else "자기"
        after = f", 뒤이어 {laid.overseer.username}이 일괄 읽음" if laid.overseer else ""
        return f"{laid.caller.username}이 {heir}에게 넘기며 {laid.target.username}을 지움{after}"

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
        missing = "와 없는 id" if laid.missing is not None else ""
        return f"{laid.caller.username}이 {names}{missing}를 일괄로 지움"

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
        return "활성 기본 키가 없어 비어 있다"

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
        return f"성공이 오고, 다시 읽은 사용자는 {self.status} 상태다"

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
                at="뒤이은 읽기.",
            ),
        ]


@dataclass(frozen=True)
class TheTargetIsGone(Then[ACallerAndATarget, Answer]):
    """성공이 오고, 슈퍼관리자가 일괄로 읽으면 그 자리가 비어 온다."""

    @override
    def says(self) -> str:
        return "성공이 오고, 그 사용자를 더 찾을 수 없다"

    @override
    def look(self, laid: ACallerAndATarget, answered: Answered[Answer]) -> list[Verdict]:
        answer = answered.response
        if not isinstance(answer, tuple) or not isinstance(answer[1], list):
            return [Refused(NotEnoughPermission, answered.raised)]
        payload, loaded = answer
        return [
            Same("success", payload.success, True),
            Skipped("뒤이은 일괄 읽기", "없는 id에 superadmin이 받는 답은 아직 정해지지 않았다"),
        ]


@dataclass(frozen=True)
class EveryoneIsPurged(Then[ASuperadminAndUsers, Answer]):
    """심은 사용자가 모두 지워지고, 없는 id가 있으면 그것만 실패로 담긴다."""

    @override
    def says(self) -> str:
        return "지운 사용자 id와 개수, 그리고 실패가 온다"

    @override
    def look(self, laid: ASuperadminAndUsers, answered: Answered[Answer]) -> list[Verdict]:
        payload = answered.response
        if not isinstance(payload, BulkPurgeUsersPayload):
            return [Refused(InsufficientPrivilege, answered.raised)]
        seen: list[Verdict] = [
            Held(
                "successes",
                list(payload.successes),
                SameAs([one.id for one in laid.users], "심은 사용자 전부"),
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
                    SameAs([laid.missing], "없는 id"),
                )
            )
            seen.append(Skipped("failed.message", "예외 문장은 바뀌어도 되는 값이다"))
        return seen


@dataclass(frozen=True)
class AGrantedUserDeletesAUser(Scenario[SeedingSession, ACallerAndATarget, UserAdapter, Answer]):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-user-granted-soft-delete-marks-another-user-deleted"

    @override
    def describe(self) -> str:
        return "대상 사용자 스코프에서 SOFT_DELETE를 받은 사용자가 물리면, 성공이 오고 그 사용자 상태가 삭제로 바뀐다"

    @override
    def given(self) -> Given[SeedingSession, ACallerAndATarget]:
        return ATargetAndSomeone(permissions=(Permission.SOFT_DELETE, Permission.READ))

    @override
    def when(self) -> When[ACallerAndATarget, UserAdapter, Answer]:
        return DeletingTheTarget()

    @override
    def then(self) -> Then[ACallerAndATarget, Answer]:
        return TheTargetNowStands(started=self.started, status="deleted")


@dataclass(frozen=True)
class AUserGrantedNothingMayNotDelete(
    Scenario[SeedingSession, ACallerAndATarget, UserAdapter, Answer]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-delete-another-user"

    @override
    def describe(self) -> str:
        return "역할 없이 물리려 하면, 엔티티 권한 문이 막는다"

    @override
    def given(self) -> Given[SeedingSession, ACallerAndATarget]:
        return ATargetAndSomeone()

    @override
    def when(self) -> When[ACallerAndATarget, UserAdapter, Answer]:
        return DeletingTheTarget(then_reading=False)

    @override
    def then(self) -> Then[ACallerAndATarget, Answer]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class AGrantedUserRestoresADeletedUser(
    Scenario[SeedingSession, ACallerAndATarget, UserAdapter, Answer]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-user-granted-soft-delete-restores-a-deleted-user-to-active"

    @override
    def describe(self) -> str:
        return "대상 사용자 스코프에서 SOFT_DELETE를 받은 사용자가 삭제 상태 사용자를 되살리면, 성공이 오고 상태가 활성으로 바뀐다"

    @override
    def given(self) -> Given[SeedingSession, ACallerAndATarget]:
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
class RestoringAnInactiveUserMakesThemActive(
    Scenario[SeedingSession, ACallerAndATarget, UserAdapter, Answer]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "restoring-a-user-who-was-never-deleted-still-makes-them-active"

    @override
    def describe(self) -> str:
        return "권한 받은 사용자가 비활성 사용자를 되살리면, 현재 상태와 무관하게 활성이 된다"

    @override
    def given(self) -> Given[SeedingSession, ACallerAndATarget]:
        return ATargetAndSomeone(
            permissions=(Permission.SOFT_DELETE, Permission.READ),
            target_status=UserStatus.INACTIVE,
        )

    @override
    def when(self) -> When[ACallerAndATarget, UserAdapter, Answer]:
        return RestoringTheTarget()

    @override
    def then(self) -> Then[ACallerAndATarget, Answer]:
        return TheTargetNowStands(started=self.started, status="active", key_is_active=False)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotRestore(
    Scenario[SeedingSession, ACallerAndATarget, UserAdapter, Answer]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-restore-another-user"

    @override
    def describe(self) -> str:
        return "역할 없이 되살리려 하면, 엔티티 권한 문이 막는다"

    @override
    def given(self) -> Given[SeedingSession, ACallerAndATarget]:
        return ATargetAndSomeone(target_status=UserStatus.DELETED)

    @override
    def when(self) -> When[ACallerAndATarget, UserAdapter, Answer]:
        return RestoringTheTarget(then_reading=False)

    @override
    def then(self) -> Then[ACallerAndATarget, Answer]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class AGrantedUserPurgesAUser(Scenario[SeedingSession, ACallerAndATarget, UserAdapter, Answer]):
    @override
    def summary(self) -> str:
        return "a-user-granted-hard-delete-purges-a-user-with-no-folders-or-sessions"

    @override
    def describe(self) -> str:
        return "대상 사용자 스코프에서 HARD_DELETE를 받은 사용자가 물리지 않은 사용자를 지워도, 성공이 오고 그 사용자를 더 찾을 수 없다"

    @override
    def given(self) -> Given[SeedingSession, ACallerAndATarget]:
        return ATargetAndSomeone(permissions=(Permission.HARD_DELETE,), overseer=True)

    @override
    def when(self) -> When[ACallerAndATarget, UserAdapter, Answer]:
        return PurgingTheTarget()

    @override
    def then(self) -> Then[ACallerAndATarget, Answer]:
        return TheTargetIsGone()


@dataclass(frozen=True)
class AUserGrantedNothingMayNotPurge(
    Scenario[SeedingSession, ACallerAndATarget, UserAdapter, Answer]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-purge-another-user"

    @override
    def describe(self) -> str:
        return "역할 없이 지우려 하면, 엔티티 권한 문이 막는다"

    @override
    def given(self) -> Given[SeedingSession, ACallerAndATarget]:
        return ATargetAndSomeone()

    @override
    def when(self) -> When[ACallerAndATarget, UserAdapter, Answer]:
        return PurgingTheTarget()

    @override
    def then(self) -> Then[ACallerAndATarget, Answer]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class PurgingToNobodyIsRefused(Scenario[SeedingSession, ACallerAndATarget, UserAdapter, Answer]):
    @override
    def summary(self) -> str:
        return "purging-a-user-to-an-admin-who-does-not-exist-is-refused"

    @override
    def describe(self) -> str:
        return "권한 받은 사용자가 넘겨받을 관리자로 없는 id를 주면, 입력 검증이 막는다"

    @override
    def given(self) -> Given[SeedingSession, ACallerAndATarget]:
        return ATargetAndSomeone(permissions=(Permission.HARD_DELETE,))

    @override
    def when(self) -> When[ACallerAndATarget, UserAdapter, Answer]:
        return PurgingTheTarget(to_nobody=True)

    @override
    def then(self) -> Then[ACallerAndATarget, Answer]:
        return TheCallIsRefused(UserNotFound)


@dataclass(frozen=True)
class TheSuperadminPurgesTwoInBulk(
    Scenario[SeedingSession, ASuperadminAndUsers, UserAdapter, Answer]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-bulk-purge-answers-the-purged-ids-and-count"

    @override
    def describe(self) -> str:
        return (
            "전역 역할이 문인 일괄 지우기에서 슈퍼관리자가 사용자 둘을 주면, 두 id와 개수 둘이 온다"
        )

    @override
    def given(self) -> Given[SeedingSession, ASuperadminAndUsers]:
        return ASuperadminAndSomeUsers(count=2)

    @override
    def when(self) -> When[ASuperadminAndUsers, UserAdapter, Answer]:
        return PurgingInBulk()

    @override
    def then(self) -> Then[ASuperadminAndUsers, Answer]:
        return EveryoneIsPurged()


@dataclass(frozen=True)
class ABulkPurgeRecordsAMissingIdAsAFailure(
    Scenario[SeedingSession, ASuperadminAndUsers, UserAdapter, Answer]
):
    @override
    def summary(self) -> str:
        return "a-bulk-purge-records-a-missing-id-as-a-failure"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 있는 사용자와 없는 id를 함께 주면, 하나는 지워지고 없는 id는 실패로 담긴다"

    @override
    def given(self) -> Given[SeedingSession, ASuperadminAndUsers]:
        return ASuperadminAndSomeUsers(count=1, with_missing=True)

    @override
    def when(self) -> When[ASuperadminAndUsers, UserAdapter, Answer]:
        return PurgingInBulk()

    @override
    def then(self) -> Then[ASuperadminAndUsers, Answer]:
        return EveryoneIsPurged()


@dataclass(frozen=True)
class AUserWhoIsNotTheSuperadminMayNotPurgeInBulk(
    Scenario[SeedingSession, ASuperadminAndUsers, UserAdapter, Answer]
):
    @override
    def summary(self) -> str:
        return "a-user-who-is-not-the-superadmin-may-not-purge-in-bulk"

    @override
    def describe(self) -> str:
        return "도메인 스코프에서 HARD_DELETE를 받은 사용자라도 일괄 지우기를 하려 하면, 전역 역할 문이 막는다"

    @override
    def given(self) -> Given[SeedingSession, ASuperadminAndUsers]:
        return SomeoneGrantedOnTheDomain()

    @override
    def when(self) -> When[ASuperadminAndUsers, UserAdapter, Answer]:
        return PurgingInBulk()

    @override
    def then(self) -> Then[ASuperadminAndUsers, Answer]:
        return TheCallIsRefused(InsufficientPrivilege)


SCENARIOS: list[Scenario[SeedingSession, Any, UserAdapter, Answer]] = [
    AGrantedUserDeletesAUser(started=datetime.now(UTC)),
    AUserGrantedNothingMayNotDelete(),
    AGrantedUserRestoresADeletedUser(started=datetime.now(UTC)),
    RestoringAnInactiveUserMakesThemActive(started=datetime.now(UTC)),
    AUserGrantedNothingMayNotRestore(),
    AGrantedUserPurgesAUser(),
    AUserGrantedNothingMayNotPurge(),
    PurgingToNobodyIsRefused(),
    TheSuperadminPurgesTwoInBulk(),
    ABulkPurgeRecordsAMissingIdAsAFailure(),
    AUserWhoIsNotTheSuperadminMayNotPurgeInBulk(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_retiring(
    scenario: Scenario[SeedingSession, Any, UserAdapter, Answer],
    adapter: UserAdapter,
    engine: ExtendedAsyncSAEngine,
) -> None:
    await run_scenario(scenario, adapter, engine)
