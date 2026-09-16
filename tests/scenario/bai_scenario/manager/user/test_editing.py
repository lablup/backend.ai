"""사용자 수정 — 하나를 고칠 때, 허용 IP만 고칠 때, 여럿을 한 번에 고칠 때."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import UTC, datetime
from typing import Any, override

import pytest

from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.user.request import SearchUsersRequest, UpdateUserInput
from ai.backend.common.dto.manager.v2.user.response import (
    BulkUpdateUsersPayload,
    SearchUsersPayload,
    UpdateMyAllowedClientIPPayload,
    UserNode,
)
from ai.backend.common.types import AccessKey
from ai.backend.manager.api.adapters.user.adapter import UserAdapter
from ai.backend.manager.data.keypair.types import KeyPairData
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.data.project.types import ProjectData
from ai.backend.manager.data.user.types import UserData
from ai.backend.manager.errors.auth import InsufficientPrivilege
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.errors.user import UserModificationBadRequest
from ai.backend.manager.models.user.updaters import UserUpdater
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.services.user.actions.update_user import (
    BulkUpdateUserAction,
    UpdateUserAction,
)
from ai.backend.manager.types import OptionalState, TriState
from ai.backend.testutils.scenario_steps import (
    Answered,
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
from bai_scenario.seeds.project.project import SeedProject
from bai_scenario.seeds.resource_policy.keypair import SeedKeypairPolicy
from bai_scenario.seeds.resource_policy.project import SeedProjectPolicy
from bai_scenario.seeds.user.fields import SeedKeypairOf

RENAMED = "renamed"
"""바꿔 넣는 전체 이름. 시나리오가 정한 값이다."""

ALLOWED_IP = ["10.0.0.1"]
"""바꿔 넣는 허용 IP. 시나리오가 정한 값이다."""

STORED_IP = ["10.0.0.1/32"]
"""같은 허용 IP를 다시 읽으면 오는 모양. 저장할 때 네트워크 표기로 바뀐다."""


@dataclass(frozen=True)
class AnEdit:
    """고칠 사람, 고치는 사람, 결과를 따로 읽어 볼 슈퍼관리자, 그리고 행이 더 필요로 하는 것."""

    caller: UserData
    target: UserData
    observer: UserData
    others: tuple[UserData, ...]
    extra_key: KeyPairData | None


@dataclass(frozen=True)
class AllowedIpChanged:
    """허용 IP 수정의 답과, 뒤이어 읽은 대상 사용자."""

    payload: UpdateMyAllowedClientIPPayload
    after: UserNode


@dataclass(frozen=True)
class AMemberEdit:
    """프로젝트 하나와 그 명부의 대상 사용자, 고치는 사람, 결과를 따로 읽어 볼 슈퍼관리자."""

    project: ProjectData
    caller: UserData
    target: UserData
    observer: UserData


@dataclass(frozen=True)
class EditedThenSearched:
    """수정의 답과, 뒤이어 프로젝트로 훑은 답."""

    node: UserNode
    members: SearchUsersPayload


type Answer = UserNode | AllowedIpChanged | BulkUpdateUsersPayload | EditedThenSearched


@dataclass(frozen=True)
class AProjectMemberAndAnEditor(Given[Any, AMemberEdit]):
    """프로젝트 하나와 그 명부에 오른 대상 사용자, 대상에게 UPDATE와 READ를 받은 사용자."""

    @override
    def describe(self) -> str:
        return (
            "도메인 하나와 프로젝트 하나, 그 명부에 오른 대상 사용자, "
            "대상 사용자 스코프에서 UPDATE와 READ를 받은 사용자 한 명"
        )

    @override
    async def lay(self, seeding: Any) -> AMemberEdit:
        domain = await seeding.creating(SeedDomain(name_hint="home", description=WAS_HERE))
        target = await seeding.within(SomeoneOf(domain))
        policy = await seeding.once(SeedProjectPolicy())
        project = await seeding.creating_from_two(SeedProject(name_hint="team"), domain, policy)
        await seeding.joining(
            project,
            target,
            project_id=lambda one: ProjectID(one.id),
            user_id=lambda one: UserID(one.id),
        )
        caller = await seeding.within(SomeoneOf(domain))
        observer = await seeding.within(SomeoneOf(domain, role=UserRole.SUPERADMIN))
        await seeding.within(AGrant.on_user(target, caller, Permission.UPDATE, Permission.READ))
        return AMemberEdit(
            project=seeding.made(project),
            caller=seeding.made(caller),
            target=seeding.made(target),
            observer=seeding.made(observer),
        )


@dataclass(frozen=True)
class ClearingTheProjectsWithNull(When[AMemberEdit, UserAdapter, Answer]):
    """소속 프로젝트 자리에 빈 값을 주고, 슈퍼관리자가 그 프로젝트로 훑는다."""

    @override
    def operation(self) -> str:
        return "update_user_by_id"

    @override
    def describe(self, laid: AMemberEdit) -> str:
        return (
            f"{laid.caller.username}이 {laid.target.username}의 소속 프로젝트에 빈 값을 주고, "
            f"{laid.observer.username}이 {laid.project.name}으로 훑음"
        )

    @override
    async def call(self, adapter: UserAdapter, laid: AMemberEdit) -> Answer:
        with ActingAs(laid.caller):
            payload = await adapter.update_user_by_id(
                laid.target.id, UpdateUserInput(group_ids=None)
            )
        with ActingAs(laid.observer):
            members = await adapter.project_search(laid.project.id, SearchUsersRequest())
        return EditedThenSearched(payload.user, members)


@dataclass(frozen=True)
class TheMembershipStays(Then[AMemberEdit, Answer]):
    """노드는 그대로이고, 프로젝트로 훑으면 대상 사용자가 남아 있다."""

    started: datetime

    @override
    def says(self) -> str:
        return "사용자는 그대로이고 프로젝트 명부에 남아 있다"

    @override
    def look(self, laid: AMemberEdit, answered: Answered[Answer]) -> list[Verdict]:
        edited = answered.response
        if not isinstance(edited, EditedThenSearched):
            return [Refused(NotEnoughPermission, answered.raised)]
        return [
            *UserNodeLook(self.started).verdicts(edited.node, laid.target),
            Held(
                "뒤이은 프로젝트 검색.items",
                [one.id for one in edited.members.items],
                SameAs([laid.target.id], "명부에 올린 대상 사용자 하나"),
            ),
            Same("뒤이은 프로젝트 검색.pagination.total", edited.members.pagination.total, 1),
            Same("뒤이은 프로젝트 검색.pagination.offset", edited.members.pagination.offset, 0),
            Same("뒤이은 프로젝트 검색.pagination.limit", edited.members.pagination.limit, 50),
        ]


@dataclass(frozen=True)
class NullProjectsLeaveTheMembership(Scenario[SeedingSession, AMemberEdit, UserAdapter, Answer]):
    started: datetime

    @override
    def summary(self) -> str:
        return "null-project-ids-in-an-edit-leave-the-membership-as-it-is"

    @override
    def describe(self) -> str:
        return (
            "권한 받은 사용자가 소속 프로젝트 자리에 빈 값을 주면, "
            "소속을 건드리지 않고 나머지 수정만 반영된다"
        )

    @override
    def given(self) -> Given[SeedingSession, AMemberEdit]:
        return AProjectMemberAndAnEditor()

    @override
    def when(self) -> When[AMemberEdit, UserAdapter, Answer]:
        return ClearingTheProjectsWithNull()

    @override
    def then(self) -> Then[AMemberEdit, Answer]:
        return TheMembershipStays(started=self.started)


@dataclass(frozen=True)
class SomeoneEditingAnother(Given[Any, AnEdit]):
    """한 도메인의 대상 사용자와 부르는 사람, 결과를 읽을 슈퍼관리자.

    `on_target`은 대상 사용자 스코프에서, `on_domain`은 도메인 스코프에서 부르는 사람이 받는
    사용자 권한이다. `others`만큼 사용자를 더 두고, `key_on`이 가리키는 사람에게 기본이 아닌
    키를 하나 더 준다.
    """

    role: UserRole = UserRole.USER
    on_target: tuple[Permission, ...] = ()
    on_domain: tuple[Permission, ...] = ()
    others: int = 0
    key_on: str | None = None

    @override
    def describe(self) -> str:
        parts = [
            f"도메인 하나와 대상 사용자, 사용자 {self.others}명 더, 부르는 {self.role.value} 한 명"
        ]
        if self.on_target:
            parts.append(
                f"부르는 사람은 대상 사용자 스코프에서 {', '.join(str(p.name) for p in self.on_target)}를 받았다"
            )
        if self.on_domain:
            parts.append(
                f"부르는 사람은 도메인 스코프에서 {', '.join(str(p.name) for p in self.on_domain)}를 받았다"
            )
        if self.key_on is not None:
            parts.append("한 사람에게 기본이 아닌 키가 하나 더 있다")
        return ", ".join(parts)

    @override
    async def lay(self, seeding: Any) -> AnEdit:
        domain = await seeding.creating(SeedDomain(name_hint="home", description=WAS_HERE))
        target = await seeding.within(SomeoneOf(domain))
        others = [await seeding.within(SomeoneOf(domain)) for _ in range(self.others)]
        caller = await seeding.within(SomeoneOf(domain, role=self.role))
        observer = await seeding.within(SomeoneOf(domain, role=UserRole.SUPERADMIN))
        if self.on_target:
            await seeding.within(AGrant.on_user(target, caller, *self.on_target))
        if self.on_domain:
            await seeding.within(AGrant.on_domain(domain, caller, *self.on_domain))
        extra_key = None
        if self.key_on is not None:
            policy = await seeding.creating(SeedKeypairPolicy())
            owner = target if self.key_on == "target" else others[0]
            extra_key = await seeding.adding(
                SeedKeypairOf(resource_policy=seeding.made(policy).name), owner
            )
        return AnEdit(
            caller=seeding.made(caller),
            target=seeding.made(target),
            observer=seeding.made(observer),
            others=tuple(seeding.made(one) for one in others),
            extra_key=seeding.made(extra_key) if extra_key is not None else None,
        )


@dataclass(frozen=True)
class ChangingTheFullName(When[AnEdit, UserAdapter, Answer]):
    """대상 사용자의 전체 이름만 바꾼다."""

    @override
    def operation(self) -> str:
        return "update_user_by_id"

    @override
    def describe(self, laid: AnEdit) -> str:
        return f"{laid.caller.username}이 {laid.target.username}의 전체 이름을 {RENAMED}로 바꿈"

    @override
    async def call(self, adapter: UserAdapter, laid: AnEdit) -> Answer:
        with ActingAs(laid.caller):
            payload = await adapter.update_user_by_id(
                laid.target.id, UpdateUserInput(full_name=RENAMED)
            )
        return payload.user


@dataclass(frozen=True)
class TakingAnotherUsersName(When[AnEdit, UserAdapter, Answer]):
    """대상 사용자의 이름을 다른 사용자가 쓰는 이름으로 바꾼다."""

    @override
    def operation(self) -> str:
        return "update_user_by_id"

    @override
    def describe(self, laid: AnEdit) -> str:
        return (
            f"{laid.caller.username}이 {laid.target.username}의 이름을 "
            f"{laid.others[0].username}로 바꿈"
        )

    @override
    async def call(self, adapter: UserAdapter, laid: AnEdit) -> Answer:
        with ActingAs(laid.caller):
            payload = await adapter.update_user_by_id(
                laid.target.id, UpdateUserInput(username=laid.others[0].username)
            )
        return payload.user


@dataclass(frozen=True)
class NamingTheOtherKeyAsDefault(When[AnEdit, UserAdapter, Answer]):
    """수정 요청에 대상 사용자의 다른 키를 기본 키로 준다."""

    @override
    def operation(self) -> str:
        return "update_user_by_id"

    @override
    def describe(self, laid: AnEdit) -> str:
        return f"{laid.caller.username}이 {laid.target.username}의 추가한 키를 기본 키로 줌"

    @override
    async def call(self, adapter: UserAdapter, laid: AnEdit) -> Answer:
        assert laid.extra_key is not None
        with ActingAs(laid.caller):
            payload = await adapter.update_user_by_id(
                laid.target.id, UpdateUserInput(main_access_key=str(laid.extra_key.access_key))
            )
        return payload.user


@dataclass(frozen=True)
class ChangingTheAllowedIp(When[AnEdit, UserAdapter, Answer]):
    """허용 IP만 담은 수정을 보내고, 슈퍼관리자가 대상 사용자를 다시 읽는다."""

    @override
    def operation(self) -> str:
        return "update_user"

    @override
    def describe(self, laid: AnEdit) -> str:
        return (
            f"{laid.caller.username}이 {laid.target.username}의 허용 IP를 바꾸고, "
            f"{laid.observer.username}이 다시 읽음"
        )

    @override
    async def call(self, adapter: UserAdapter, laid: AnEdit) -> Answer:
        with ActingAs(laid.caller):
            payload = await adapter.update_user(
                UpdateUserAction(
                    updater=UserUpdater(
                        user_id=UserID(laid.target.id),
                        allowed_client_ip=TriState.update(ALLOWED_IP),
                    )
                )
            )
        with ActingAs(laid.observer):
            after = await adapter.get(laid.target.id)
        return AllowedIpChanged(payload, after.user)


@dataclass(frozen=True)
class BulkRenamingOneAndCollidingAnother(When[AnEdit, UserAdapter, Answer]):
    """대상 사용자의 전체 이름을 바꾸고, 셋째 사용자의 이름을 둘째 사용자의 이름으로 바꾼다."""

    @override
    def operation(self) -> str:
        return "bulk_modify_users"

    @override
    def describe(self, laid: AnEdit) -> str:
        return (
            f"{laid.caller.username}이 {laid.target.username}의 전체 이름을 바꾸고 "
            f"{laid.others[1].username}의 이름을 {laid.others[0].username}로 일괄 수정"
        )

    @override
    async def call(self, adapter: UserAdapter, laid: AnEdit) -> Answer:
        action = BulkUpdateUserAction(
            items=[
                UserUpdater(user_id=UserID(laid.target.id), full_name=TriState.update(RENAMED)),
                UserUpdater(
                    user_id=UserID(laid.others[1].id),
                    username=OptionalState.update(laid.others[0].username),
                ),
            ]
        )
        with ActingAs(laid.caller):
            return await adapter.bulk_modify_users(action, {})


@dataclass(frozen=True)
class BulkRenamingWithSomeoneElsesKey(When[AnEdit, UserAdapter, Answer]):
    """대상 사용자의 전체 이름을 바꾸면서 다른 사용자의 키로 기본 키를 옮긴다."""

    @override
    def operation(self) -> str:
        return "bulk_modify_users"

    @override
    def describe(self, laid: AnEdit) -> str:
        return (
            f"{laid.caller.username}이 {laid.target.username}을 일괄 수정하며 "
            f"{laid.others[0].username}의 키로 기본 키를 옮김"
        )

    @override
    async def call(self, adapter: UserAdapter, laid: AnEdit) -> Answer:
        assert laid.extra_key is not None
        action = BulkUpdateUserAction(
            items=[UserUpdater(user_id=UserID(laid.target.id), full_name=TriState.update(RENAMED))]
        )
        with ActingAs(laid.caller):
            return await adapter.bulk_modify_users(
                action, {UserID(laid.target.id): AccessKey(str(laid.extra_key.access_key))}
            )


@dataclass(frozen=True)
class TheRenamedNode(Then[AnEdit, Answer]):
    """전체 이름만 바뀐 노드가 통째로 온다."""

    started: datetime

    @override
    def says(self) -> str:
        return "전체 이름만 바뀐 사용자 전체가 온다"

    @override
    def look(self, laid: AnEdit, answered: Answered[Answer]) -> list[Verdict]:
        node = answered.response
        if not isinstance(node, UserNode):
            return [Refused(NotEnoughPermission, answered.raised)]
        return UserNodeLook(self.started).verdicts(node, replace(laid.target, full_name=RENAMED))


@dataclass(frozen=True)
class TheDefaultKeyMoved(Then[AnEdit, Answer]):
    """기본 키가 추가한 키로 옮겨간 노드가 통째로 온다."""

    started: datetime

    @override
    def says(self) -> str:
        return "기본 키가 추가한 키로 옮겨간 사용자 전체가 온다"

    @override
    def look(self, laid: AnEdit, answered: Answered[Answer]) -> list[Verdict]:
        node = answered.response
        if not isinstance(node, UserNode) or laid.extra_key is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        return UserNodeLook(self.started).verdicts(
            node,
            laid.target,
            main_access_key=SameAs(str(laid.extra_key.access_key), "추가한 키"),
        )


@dataclass(frozen=True)
class TheAllowedIpChanged(Then[AnEdit, Answer]):
    """성공이 오고, 다시 읽은 사용자는 허용 IP만 바뀌어 있다."""

    started: datetime

    @override
    def says(self) -> str:
        return "성공이 오고, 다시 읽은 사용자는 허용 IP만 바뀌어 있다"

    @override
    def look(self, laid: AnEdit, answered: Answered[Answer]) -> list[Verdict]:
        changed = answered.response
        if not isinstance(changed, AllowedIpChanged):
            return [Refused(NotEnoughPermission, answered.raised)]
        return [
            Same("success", changed.payload.success, True),
            *UserNodeLook(self.started).verdicts(
                changed.after,
                replace(laid.target, allowed_client_ip=STORED_IP),
                at="뒤이은 읽기.",
            ),
        ]


@dataclass(frozen=True)
class OneUpdatedOneFailed(Then[AnEdit, Answer]):
    """전체 이름을 바꾼 사람은 수정 목록에, 이름이 겹친 사람은 실패 목록에 온다."""

    started: datetime

    @override
    def says(self) -> str:
        return "하나는 수정 목록에, 하나는 실패 목록에 온다"

    @override
    def look(self, laid: AnEdit, answered: Answered[Answer]) -> list[Verdict]:
        payload = answered.response
        if not isinstance(payload, BulkUpdateUsersPayload):
            return [Refused(InsufficientPrivilege, answered.raised)]
        seen: list[Verdict] = [
            Same("updated_users.length", len(payload.updated_users), 1),
            Same("failed.length", len(payload.failed), 1),
        ]
        if payload.updated_users:
            seen.extend(
                UserNodeLook(self.started).verdicts(
                    payload.updated_users[0],
                    replace(laid.target, full_name=RENAMED),
                    at="updated_users[0].",
                )
            )
        if payload.failed:
            seen.append(
                Held(
                    "failed[0].user_id",
                    payload.failed[0].user_id,
                    SameAs(laid.others[1].id, "이름이 겹치게 바꾼 사용자"),
                )
            )
            seen.append(Skipped("failed[0].message", "예외 메시지는 바뀌어도 되는 값이다"))
        return seen


@dataclass(frozen=True)
class TheSwitchFailureIsAFailure(Then[AnEdit, Answer]):
    """수정 목록은 비고, 기본 키를 옮기려던 사람이 실패 목록에 온다."""

    @override
    def says(self) -> str:
        return "수정 목록은 비고, 그 사용자가 실패 목록에 온다"

    @override
    def look(self, laid: AnEdit, answered: Answered[Answer]) -> list[Verdict]:
        payload = answered.response
        if not isinstance(payload, BulkUpdateUsersPayload):
            return [Refused(InsufficientPrivilege, answered.raised)]
        seen: list[Verdict] = [
            Same("updated_users", list(payload.updated_users), []),
            Same("failed.length", len(payload.failed), 1),
        ]
        if payload.failed:
            seen.append(
                Held(
                    "failed[0].user_id",
                    payload.failed[0].user_id,
                    SameAs(laid.target.id, "기본 키를 옮기려던 사용자"),
                )
            )
            seen.append(Skipped("failed[0].message", "예외 메시지는 바뀌어도 되는 값이다"))
        return seen


@dataclass(frozen=True)
class AGrantedUserChangesOnlyTheFullName(Scenario[SeedingSession, AnEdit, UserAdapter, Answer]):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-user-granted-update-changing-only-the-full-name-leaves-the-rest"

    @override
    def describe(self) -> str:
        return (
            "대상 사용자 스코프에서 UPDATE와 READ를 받은 사용자가 전체 이름만 주면, "
            "전체 이름만 바뀐 노드가 온다"
        )

    @override
    def given(self) -> Given[SeedingSession, AnEdit]:
        return SomeoneEditingAnother(on_target=(Permission.UPDATE, Permission.READ))

    @override
    def when(self) -> When[AnEdit, UserAdapter, Answer]:
        return ChangingTheFullName()

    @override
    def then(self) -> Then[AnEdit, Answer]:
        return TheRenamedNode(started=self.started)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotEditAnother(Scenario[SeedingSession, AnEdit, UserAdapter, Answer]):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-edit-another-user"

    @override
    def describe(self) -> str:
        return "역할을 받지 않은 사용자가 수정하려 하면, 엔티티 권한 문이 막는다"

    @override
    def given(self) -> Given[SeedingSession, AnEdit]:
        return SomeoneEditingAnother()

    @override
    def when(self) -> When[AnEdit, UserAdapter, Answer]:
        return ChangingTheFullName()

    @override
    def then(self) -> Then[AnEdit, Answer]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class ANameAnotherUserHoldsMayNotBeTaken(Scenario[SeedingSession, AnEdit, UserAdapter, Answer]):
    @override
    def summary(self) -> str:
        return "a-username-another-user-holds-may-not-be-taken"

    @override
    def describe(self) -> str:
        return "권한 받은 사용자가 이미 쓰이는 사용자 이름을 주면, 입력 검증이 막는다"

    @override
    def given(self) -> Given[SeedingSession, AnEdit]:
        return SomeoneEditingAnother(on_target=(Permission.UPDATE,), others=1)

    @override
    def when(self) -> When[AnEdit, UserAdapter, Answer]:
        return TakingAnotherUsersName()

    @override
    def then(self) -> Then[AnEdit, Answer]:
        return TheCallIsRefused(UserModificationBadRequest)


@dataclass(frozen=True)
class NamingADefaultKeyMovesItAfterTheEdit(Scenario[SeedingSession, AnEdit, UserAdapter, Answer]):
    started: datetime

    @override
    def summary(self) -> str:
        return "naming-a-default-key-in-an-edit-moves-the-default-to-it"

    @override
    def describe(self) -> str:
        return (
            "권한 받은 사용자가 대상 사용자의 다른 키를 기본 키로 주면, "
            "수정이 반영된 뒤 기본 키가 옮겨간 노드가 온다"
        )

    @override
    def given(self) -> Given[SeedingSession, AnEdit]:
        return SomeoneEditingAnother(
            on_target=(Permission.UPDATE, Permission.READ), key_on="target"
        )

    @override
    def when(self) -> When[AnEdit, UserAdapter, Answer]:
        return NamingTheOtherKeyAsDefault()

    @override
    def then(self) -> Then[AnEdit, Answer]:
        return TheDefaultKeyMoved(started=self.started)


@dataclass(frozen=True)
class AGrantedUserChangesTheAllowedIp(Scenario[SeedingSession, AnEdit, UserAdapter, Answer]):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-user-granted-update-changes-the-allowed-client-ip"

    @override
    def describe(self) -> str:
        return (
            "대상 사용자 스코프에서 UPDATE를 받은 사용자가 허용 IP만 담은 수정을 보내면, "
            "성공 표시가 오고 그 사용자의 허용 IP가 바뀐다"
        )

    @override
    def given(self) -> Given[SeedingSession, AnEdit]:
        return SomeoneEditingAnother(on_target=(Permission.UPDATE,))

    @override
    def when(self) -> When[AnEdit, UserAdapter, Answer]:
        return ChangingTheAllowedIp()

    @override
    def then(self) -> Then[AnEdit, Answer]:
        return TheAllowedIpChanged(started=self.started)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotChangeTheAllowedIp(
    Scenario[SeedingSession, AnEdit, UserAdapter, Answer]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-change-the-allowed-client-ip"

    @override
    def describe(self) -> str:
        return "역할 없이 허용 IP 수정을 보내면, 엔티티 권한 문이 막는다"

    @override
    def given(self) -> Given[SeedingSession, AnEdit]:
        return SomeoneEditingAnother()

    @override
    def when(self) -> When[AnEdit, UserAdapter, Answer]:
        return ChangingTheAllowedIp()

    @override
    def then(self) -> Then[AnEdit, Answer]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class TheSuperadminBulkEditSplitsUpdatedAndFailed(
    Scenario[SeedingSession, AnEdit, UserAdapter, Answer]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "the-superadmin-bulk-edit-answers-the-updated-and-the-failed-apart"

    @override
    def describe(self) -> str:
        return (
            "전역 역할이 문인 일괄 수정에서 슈퍼관리자가 있는 사용자와 이름이 겹치게 바꾸는 사용자를 "
            "함께 주면, 하나는 수정되고 하나는 사용자 id와 함께 실패로 담긴다"
        )

    @override
    def given(self) -> Given[SeedingSession, AnEdit]:
        return SomeoneEditingAnother(role=UserRole.SUPERADMIN, others=2)

    @override
    def when(self) -> When[AnEdit, UserAdapter, Answer]:
        return BulkRenamingOneAndCollidingAnother()

    @override
    def then(self) -> Then[AnEdit, Answer]:
        return OneUpdatedOneFailed(started=self.started)


@dataclass(frozen=True)
class AFailedKeySwitchTurnsTheUserIntoAFailure(
    Scenario[SeedingSession, AnEdit, UserAdapter, Answer]
):
    @override
    def summary(self) -> str:
        return "a-bulk-edit-whose-default-key-switch-fails-reports-that-user-as-failed"

    @override
    def describe(self) -> str:
        return (
            "슈퍼관리자가 일괄 수정과 함께 남의 키로 기본 키 전환을 주면, "
            "그 사용자는 수정 목록에서 빠지고 실패로 담긴다"
        )

    @override
    def given(self) -> Given[SeedingSession, AnEdit]:
        return SomeoneEditingAnother(role=UserRole.SUPERADMIN, others=1, key_on="other")

    @override
    def when(self) -> When[AnEdit, UserAdapter, Answer]:
        return BulkRenamingWithSomeoneElsesKey()

    @override
    def then(self) -> Then[AnEdit, Answer]:
        return TheSwitchFailureIsAFailure()


@dataclass(frozen=True)
class OnlyTheSuperadminMayBulkEdit(Scenario[SeedingSession, AnEdit, UserAdapter, Answer]):
    @override
    def summary(self) -> str:
        return "a-user-who-is-not-the-superadmin-may-not-bulk-edit-users"

    @override
    def describe(self) -> str:
        return (
            "도메인 스코프에서 UPDATE를 받은 사용자라도 일괄 수정을 하려 하면, "
            "전역 역할 문이 막는다"
        )

    @override
    def given(self) -> Given[SeedingSession, AnEdit]:
        return SomeoneEditingAnother(on_domain=(Permission.UPDATE,), others=2)

    @override
    def when(self) -> When[AnEdit, UserAdapter, Answer]:
        return BulkRenamingOneAndCollidingAnother()

    @override
    def then(self) -> Then[AnEdit, Answer]:
        return TheCallIsRefused(InsufficientPrivilege)


SCENARIOS: list[Scenario[SeedingSession, Any, UserAdapter, Answer]] = [
    AGrantedUserChangesOnlyTheFullName(started=datetime.now(UTC)),
    AUserGrantedNothingMayNotEditAnother(),
    ANameAnotherUserHoldsMayNotBeTaken(),
    NullProjectsLeaveTheMembership(started=datetime.now(UTC)),
    NamingADefaultKeyMovesItAfterTheEdit(started=datetime.now(UTC)),
    AGrantedUserChangesTheAllowedIp(started=datetime.now(UTC)),
    AUserGrantedNothingMayNotChangeTheAllowedIp(),
    TheSuperadminBulkEditSplitsUpdatedAndFailed(started=datetime.now(UTC)),
    AFailedKeySwitchTurnsTheUserIntoAFailure(),
    OnlyTheSuperadminMayBulkEdit(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_editing(
    scenario: Scenario[SeedingSession, Any, UserAdapter, Answer],
    adapter: UserAdapter,
    engine: ExtendedAsyncSAEngine,
) -> None:
    await run_scenario(scenario, adapter, engine)
