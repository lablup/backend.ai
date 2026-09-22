"""남의 키페어 다루기 — 만들고, 바꾸고, 지우고, 읽고, SSH 키를 두고, 모두 훑기."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, override

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.keypair import AdminSearchKeypairsInput, KeypairNode
from ai.backend.common.dto.manager.v2.keypair.request import (
    AdminCreateKeypairInput,
    AdminRegisterSSHKeypairInput,
    AdminUpdateKeypairInput,
)
from ai.backend.common.dto.manager.v2.keypair.response import (
    AdminCreateKeypairPayload,
    AdminDeleteKeypairPayload,
    AdminGetSSHKeypairPayload,
    AdminSearchKeypairsPayload,
    AdminUpdateKeypairPayload,
)
from ai.backend.manager.api.adapters.user.adapter import UserAdapter
from ai.backend.manager.data.common.types import SearchResult
from ai.backend.manager.data.keypair.types import KeyPairData
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.data.resource.types import KeyPairResourcePolicyData
from ai.backend.manager.data.user.types import UserData
from ai.backend.manager.errors.auth import InsufficientPrivilege
from ai.backend.manager.errors.common import GenericBadRequest
from ai.backend.manager.errors.keypair import KeypairResourcePolicyNotFound
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.errors.user import KeyPairForbidden
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
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
from bai_scenario.components.domain import WAS_HERE, SomeoneOf, WrittenByThisRun
from bai_scenario.components.user import AGrant, KeypairNodeLook
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario
from bai_scenario.seeds.domain.domain import SeedDomain
from bai_scenario.seeds.resource_policy.keypair import SeedKeypairPolicy
from bai_scenario.seeds.resource_policy.project import SeedProjectPolicy
from bai_scenario.seeds.resource_policy.user import SeedUserPolicy
from bai_scenario.seeds.seeder import Laid, Seeder, SeedNest
from bai_scenario.seeds.user.fields import SeedKeypairOf
from bai_scenario.seeds.user.user import SeedUserOf

type Answer = object

NO_SUCH_POLICY = "no-such-policy"
"""어느 정책도 갖지 않은 이름. 거부를 부르는 입력이라 연결값이 아니다."""

RATE_LIMIT = 45000
"""바꿀 요청 한도."""

SERVER_RATE_LIMIT = 10000
"""요청 한도를 적지 않은 키에 데이터베이스가 넣는 값."""

CREATED_RATE_LIMIT = 30000
"""키를 만드는 요청이 요청 한도를 생략했을 때의 값."""

SSH_PUBLIC_KEY = "ssh-rsa scenario-public-key"
SSH_PRIVATE_KEY = "scenario-private-key"


# ------------------------------------------------------------------ situations


@dataclass(frozen=True)
class AKeyOwnerAndACaller:
    """키를 가진 사람과 그 키를 다룰 사람.

    `extra`는 대상에게 더 심은 기본 아닌 키, `helper`는 대상의 기본 키를 찾아 주는
    슈퍼관리자다. 기본 키는 사용자를 만들 때 매니저가 만들어 행이 답하지 않는다.
    """

    caller: UserData
    target: UserData
    policy: KeyPairResourcePolicyData
    extra: KeyPairData | None
    helper: UserData | None


@dataclass(frozen=True)
class SomeoneAndAKeyOwner(Given[Any, AKeyOwnerAndACaller]):
    """한 도메인의 대상 사용자와 부르는 사람, 그리고 부르는 사람이 대상에 받은 권한."""

    grant: tuple[Permission, ...] = ()
    extra: bool = False
    helper: bool = False

    @override
    def describe(self) -> str:
        parts = ["도메인 하나와 대상 사용자, 부르는 사용자"]
        if self.extra:
            parts.append("대상에게 기본 아닌 키 하나")
        if self.grant:
            names = ", ".join(str(one.name) for one in self.grant)
            parts.append(f"부르는 사람은 대상에 대한 사용자 {names} 권한을 받았다")
        else:
            parts.append("부르는 사람은 아무 권한도 받지 않았다")
        return ", ".join(parts)

    @override
    async def lay(self, seeding: Any) -> AKeyOwnerAndACaller:
        domain = await seeding.creating(SeedDomain(name_hint="home", description=WAS_HERE))
        target = await seeding.within(SomeoneOf(domain))
        caller = await seeding.within(SomeoneOf(domain))
        policy = await seeding.creating(SeedKeypairPolicy(name_hint="granted-policy"))
        extra = (
            await seeding.adding(SeedKeypairOf(resource_policy=seeding.made(policy).name), target)
            if self.extra
            else None
        )
        helper = (
            await seeding.within(SomeoneOf(domain, role=UserRole.SUPERADMIN))
            if self.helper
            else None
        )
        if self.grant:
            await seeding.within(AGrant.on_user(target, caller, *self.grant))
        return AKeyOwnerAndACaller(
            caller=seeding.made(caller),
            target=seeding.made(target),
            policy=seeding.made(policy),
            extra=seeding.made(extra) if extra is not None else None,
            helper=seeding.made(helper) if helper is not None else None,
        )


@dataclass(frozen=True)
class SomeoneUnderTheirOwnPolicy(SeedNest[tuple[Laid[UserData], Laid[KeyPairResourcePolicyData]]]):
    """자기만의 키페어 정책으로 만든 사용자 한 명. 정책이 기대값이 되므로 함께 답한다."""

    domain: Laid[Any]
    role: UserRole = UserRole.USER

    @override
    def kind(self) -> str:
        return "자기 키페어 정책을 가진 사용자 한 명 준비"

    @override
    def lay(self, seed: Seeder) -> tuple[Laid[UserData], Laid[KeyPairResourcePolicyData]]:
        seed.once(SeedProjectPolicy())
        policy = seed.creating(SeedUserPolicy())
        key_policy = seed.creating(SeedKeypairPolicy())
        user = seed.provisioning(SeedUserOf(role=self.role), self.domain, policy, key_policy)
        return user, key_policy


@dataclass(frozen=True)
class KeysOfEveryone:
    """훑는 사람과, 키를 가진 사람마다 그 키의 정책. 훑는 사람도 키를 가졌다."""

    caller: UserData
    owners: tuple[tuple[UserData, KeyPairResourcePolicyData], ...]


@dataclass(frozen=True)
class ASuperadminAndTwoUsers(Given[Any, KeysOfEveryone]):
    """한 도메인의 사용자 둘과 슈퍼관리자 한 명, 저마다 자기 키페어 정책을 가졌다."""

    @override
    def describe(self) -> str:
        return "도메인 하나와 사용자 둘, 슈퍼관리자 한 명, 저마다 다른 키페어 정책"

    @override
    async def lay(self, seeding: Any) -> KeysOfEveryone:
        domain = await seeding.creating(SeedDomain(name_hint="home", description=WAS_HERE))
        first = await seeding.within(SomeoneUnderTheirOwnPolicy(domain))
        second = await seeding.within(SomeoneUnderTheirOwnPolicy(domain))
        caller = await seeding.within(SomeoneUnderTheirOwnPolicy(domain, role=UserRole.SUPERADMIN))
        return KeysOfEveryone(
            caller=seeding.made(caller[0]),
            owners=tuple(
                (seeding.made(user), seeding.made(policy))
                for user, policy in (first, second, caller)
            ),
        )


@dataclass(frozen=True)
class SomeoneReadingTheDomain(Given[Any, KeysOfEveryone]):
    """도메인 스코프에서 사용자 읽기 권한을 받은 사용자 한 명."""

    @override
    def describe(self) -> str:
        return "도메인 하나와, 그 도메인 스코프에서 사용자 READ 권한을 받은 사용자 한 명"

    @override
    async def lay(self, seeding: Any) -> KeysOfEveryone:
        domain = await seeding.creating(SeedDomain(name_hint="home", description=WAS_HERE))
        caller = await seeding.within(SomeoneOf(domain))
        await seeding.within(AGrant.on_domain(domain, caller, Permission.READ))
        return KeysOfEveryone(caller=seeding.made(caller), owners=())


# ------------------------------------------------------------------ calls


async def _default_key_of(adapter: UserAdapter, laid: AKeyOwnerAndACaller) -> str:
    """대상의 기본 키. 슈퍼관리자가 대상을 읽어 얻는다."""
    if laid.helper is None:
        raise AssertionError("the situation laid no superadmin to look the key up")
    with ActingAs(laid.helper):
        payload = await adapter.get(laid.target.id)
    key = payload.user.organization.main_access_key
    if key is None:
        raise AssertionError("the target has no default key")
    return str(key)


def _extra_of(laid: AKeyOwnerAndACaller) -> KeyPairData:
    if laid.extra is None:
        raise AssertionError("the situation laid no extra key")
    return laid.extra


@dataclass(frozen=True)
class SSHAfterwards:
    """SSH 키를 다룬 답과, 뒤이어 읽은 공개키."""

    answered: str
    default_key: str
    public_key: str | None


@dataclass(frozen=True)
class SSHRead:
    """읽은 SSH 키와, 대상의 기본 키."""

    payload: AdminGetSSHKeypairPayload
    default_key: str


@dataclass(frozen=True)
class MakingAKeyForTheTarget(When[AKeyOwnerAndACaller, UserAdapter, Answer]):
    """대상에게 키를 만들어 준다. 정책은 심은 것이거나 없는 이름이다."""

    missing_policy: bool = False

    @override
    def operation(self) -> str:
        return "admin_create_keypair"

    @override
    def describe(self, laid: AKeyOwnerAndACaller) -> str:
        policy = "없는 정책" if self.missing_policy else laid.policy.name
        return f"{laid.caller.username}이 {laid.target.username}에게 {policy}으로 키를 만듦"

    @override
    async def call(self, adapter: UserAdapter, laid: AKeyOwnerAndACaller) -> Answer:
        with ActingAs(laid.caller):
            return await adapter.admin_create_keypair(
                AdminCreateKeypairInput(
                    user_id=laid.target.id,
                    resource_policy=NO_SUCH_POLICY if self.missing_policy else laid.policy.name,
                )
            )


@dataclass(frozen=True)
class ChangingTheExtraKey(When[AKeyOwnerAndACaller, UserAdapter, Answer]):
    """대상의 기본 아닌 키의 요청 한도를 바꾼다. 없는 정책도 함께 줄 수 있다."""

    missing_policy: bool = False

    @override
    def operation(self) -> str:
        return "admin_update_keypair"

    @override
    def describe(self, laid: AKeyOwnerAndACaller) -> str:
        extra = "와 없는 정책" if self.missing_policy else ""
        return f"{laid.caller.username}이 {laid.target.username}의 키에 요청 한도{extra}를 줌"

    @override
    async def call(self, adapter: UserAdapter, laid: AKeyOwnerAndACaller) -> Answer:
        with ActingAs(laid.caller):
            return await adapter.admin_update_keypair(
                AdminUpdateKeypairInput(
                    access_key=str(_extra_of(laid).access_key),
                    rate_limit=RATE_LIMIT,
                    resource_policy=NO_SUCH_POLICY if self.missing_policy else None,
                )
            )


@dataclass(frozen=True)
class DeletingTheExtraKey(When[AKeyOwnerAndACaller, UserAdapter, Answer]):
    """대상의 기본 아닌 키를 지운다."""

    @override
    def operation(self) -> str:
        return "admin_delete_keypair"

    @override
    def describe(self, laid: AKeyOwnerAndACaller) -> str:
        return f"{laid.caller.username}이 {laid.target.username}의 기본 아닌 키를 지움"

    @override
    async def call(self, adapter: UserAdapter, laid: AKeyOwnerAndACaller) -> Answer:
        with ActingAs(laid.caller):
            return await adapter.admin_delete_keypair(str(_extra_of(laid).access_key))


@dataclass(frozen=True)
class DeletingTheDefaultKey(When[AKeyOwnerAndACaller, UserAdapter, Answer]):
    """대상의 기본 키를 지운다."""

    @override
    def operation(self) -> str:
        return "admin_delete_keypair"

    @override
    def describe(self, laid: AKeyOwnerAndACaller) -> str:
        return f"{laid.caller.username}이 {laid.target.username}의 기본 키를 지움"

    @override
    async def call(self, adapter: UserAdapter, laid: AKeyOwnerAndACaller) -> Answer:
        key = await _default_key_of(adapter, laid)
        with ActingAs(laid.caller):
            return await adapter.admin_delete_keypair(key)


@dataclass(frozen=True)
class ReadingTheExtraKey(When[AKeyOwnerAndACaller, UserAdapter, Answer]):
    """대상의 기본 아닌 키를 access key로 읽는다."""

    @override
    def operation(self) -> str:
        return "admin_get_keypair"

    @override
    def describe(self, laid: AKeyOwnerAndACaller) -> str:
        return f"{laid.caller.username}이 {laid.target.username}의 키를 access key로 읽음"

    @override
    async def call(self, adapter: UserAdapter, laid: AKeyOwnerAndACaller) -> Answer:
        with ActingAs(laid.caller):
            return await adapter.admin_get_keypair(str(_extra_of(laid).access_key))


@dataclass(frozen=True)
class RegisteringAnSSHKey(When[AKeyOwnerAndACaller, UserAdapter, Answer]):
    """대상의 기본 키에 SSH 키를 등록하고, 등록됐는지 뒤이어 읽는다."""

    @override
    def operation(self) -> str:
        return "admin_register_ssh_keypair"

    @override
    def describe(self, laid: AKeyOwnerAndACaller) -> str:
        return f"{laid.caller.username}이 {laid.target.username}의 기본 키에 SSH 키를 등록하고 읽음"

    @override
    async def call(self, adapter: UserAdapter, laid: AKeyOwnerAndACaller) -> Answer:
        key = await _default_key_of(adapter, laid)
        with ActingAs(laid.caller):
            payload = await adapter.admin_register_ssh_keypair(
                AdminRegisterSSHKeypairInput(
                    access_key=key,
                    ssh_public_key=SSH_PUBLIC_KEY,
                    ssh_private_key=SSH_PRIVATE_KEY,
                )
            )
            after = await adapter.admin_get_ssh_keypair(key)
        return SSHAfterwards(payload.access_key, key, after.keypair.ssh_public_key)


@dataclass(frozen=True)
class ClearingTheSSHKey(When[AKeyOwnerAndACaller, UserAdapter, Answer]):
    """대상의 기본 키에서 SSH 키를 지우고, 비었는지 뒤이어 읽는다."""

    @override
    def operation(self) -> str:
        return "admin_delete_ssh_keypair"

    @override
    def describe(self, laid: AKeyOwnerAndACaller) -> str:
        return f"{laid.caller.username}이 {laid.target.username}의 기본 키에서 SSH 키를 지우고 읽음"

    @override
    async def call(self, adapter: UserAdapter, laid: AKeyOwnerAndACaller) -> Answer:
        key = await _default_key_of(adapter, laid)
        with ActingAs(laid.caller):
            payload = await adapter.admin_delete_ssh_keypair(key)
            after = await adapter.admin_get_ssh_keypair(key)
        return SSHAfterwards(payload.access_key, key, after.keypair.ssh_public_key)


@dataclass(frozen=True)
class ReadingTheSSHKey(When[AKeyOwnerAndACaller, UserAdapter, Answer]):
    """대상의 기본 키에 걸린 SSH 공개키를 읽는다."""

    @override
    def operation(self) -> str:
        return "admin_get_ssh_keypair"

    @override
    def describe(self, laid: AKeyOwnerAndACaller) -> str:
        return f"{laid.caller.username}이 {laid.target.username}의 SSH 공개키를 읽음"

    @override
    async def call(self, adapter: UserAdapter, laid: AKeyOwnerAndACaller) -> Answer:
        key = await _default_key_of(adapter, laid)
        with ActingAs(laid.caller):
            payload = await adapter.admin_get_ssh_keypair(key)
        return SSHRead(payload, key)


@dataclass(frozen=True)
class SearchingEveryKey(When[KeysOfEveryone, UserAdapter, Answer]):
    """페이지 인자 없이 모든 키를 훑는다."""

    @override
    def operation(self) -> str:
        return "admin_search_keypairs"

    @override
    def describe(self, laid: KeysOfEveryone) -> str:
        return f"{laid.caller.username}이 페이지 인자 없이 모든 키를 훑음"

    @override
    async def call(self, adapter: UserAdapter, laid: KeysOfEveryone) -> Answer:
        with ActingAs(laid.caller):
            return await adapter.admin_search_keypairs(AdminSearchKeypairsInput())


@dataclass(frozen=True)
class SearchingKeysOverGQL(When[KeysOfEveryone, UserAdapter, Answer]):
    """GQL 키 검색. `by_first_policy`면 첫 사용자의 정책 이름으로 건다."""

    by_first_policy: bool = False

    @override
    def operation(self) -> str:
        return "gql_admin_search_keypairs"

    @override
    def describe(self, laid: KeysOfEveryone) -> str:
        if self.by_first_policy:
            return f"{laid.caller.username}이 {laid.owners[0][1].name}으로 걸러 GQL 키 검색"
        return f"{laid.caller.username}이 GQL로 모든 키를 훑음"

    @override
    async def call(self, adapter: UserAdapter, laid: KeysOfEveryone) -> Answer:
        with ActingAs(laid.caller):
            return await adapter.gql_admin_search_keypairs(
                AdminSearchKeypairsInput(),
                resource_policy_name=laid.owners[0][1].name if self.by_first_policy else None,
            )


# ------------------------------------------------------------------ answers


@dataclass(frozen=True)
class SeededKeyLook:
    """시드가 심은 키 하나를 통째로 본다.

    요청 한도와 시각은 데이터베이스가 채우므로 심은 행의 데이터가 아니라 값과 조건으로 본다.
    """

    started: datetime

    def extra_key(
        self, node: KeypairNode, laid: AKeyOwnerAndACaller, rate_limit: int
    ) -> list[Verdict]:
        extra = _extra_of(laid)
        written = WrittenByThisRun(self.started)
        return [
            Held("id", node.id, SameAs(str(extra.access_key), "심은 키")),
            Held("access_key", node.access_key, SameAs(str(extra.access_key), "심은 키")),
            Same("is_active", node.is_active, True),
            Same("is_admin", node.is_admin, False),
            Same("is_default", node.is_default, False),
            Same("rate_limit", node.rate_limit, rate_limit),
            Same("resource_policy", node.resource_policy, laid.policy.name),
            Same("ssh_public_key", node.ssh_public_key, ""),
            Same("num_queries", node.num_queries, 0),
            Same("last_used", node.last_used, None),
            Held("user_id", node.user_id, SameAs(laid.target.id, "키의 주인")),
            Held("created_at", node.created_at, written),
            Held("modified_at", node.modified_at, written),
        ]

    def default_key(
        self,
        node: KeypairNode,
        owner: UserData,
        policy: KeyPairResourcePolicyData,
        at: str,
    ) -> list[Verdict]:
        written = WrittenByThisRun(self.started)
        return [
            Skipped(f"{at}id", "시드가 만든 난수 키다"),
            Skipped(f"{at}access_key", "시드가 만든 난수 키다"),
            Same(f"{at}is_active", node.is_active, True),
            Same(
                f"{at}is_admin",
                node.is_admin,
                owner.role in (UserRole.SUPERADMIN, UserRole.ADMIN),
            ),
            Same(f"{at}is_default", node.is_default, True),
            Same(f"{at}rate_limit", node.rate_limit, SERVER_RATE_LIMIT),
            Same(f"{at}resource_policy", node.resource_policy, policy.name),
            Same(f"{at}ssh_public_key", node.ssh_public_key, ""),
            Same(f"{at}num_queries", node.num_queries, 0),
            Same(f"{at}last_used", node.last_used, None),
            Held(f"{at}user_id", node.user_id, SameAs(owner.id, "키의 주인")),
            Held(f"{at}created_at", node.created_at, written),
            Held(f"{at}modified_at", node.modified_at, written),
        ]


@dataclass(frozen=True)
class TheNewKey(Then[AKeyOwnerAndACaller, Answer]):
    """만든 키가 기본 아닌 키로 통째로 오고, secret이 함께 온다."""

    started: datetime

    @override
    def says(self) -> str:
        return "만든 키 전체와 secret이 온다"

    @override
    def look(self, laid: AKeyOwnerAndACaller, answered: Answered[Answer]) -> list[Verdict]:
        payload = answered.response
        if not isinstance(payload, AdminCreateKeypairPayload):
            return [Refused(NotEnoughPermission, answered.raised)]
        return [
            *KeypairNodeLook(self.started).generated(
                payload.keypair,
                laid.target,
                is_active=True,
                is_admin=False,
                is_default=False,
                rate_limit=CREATED_RATE_LIMIT,
                resource_policy=laid.policy.name,
            ),
            Skipped("secret_key", "매니저가 만든다"),
        ]


@dataclass(frozen=True)
class TheChangedKey(Then[AKeyOwnerAndACaller, Answer]):
    """요청 한도만 바뀐 키가 통째로 온다."""

    started: datetime

    @override
    def says(self) -> str:
        return "요청 한도만 바뀐 키 전체가 온다"

    @override
    def look(self, laid: AKeyOwnerAndACaller, answered: Answered[Answer]) -> list[Verdict]:
        payload = answered.response
        if not isinstance(payload, AdminUpdateKeypairPayload):
            return [Refused(NotEnoughPermission, answered.raised)]
        return SeededKeyLook(self.started).extra_key(payload.keypair, laid, RATE_LIMIT)


@dataclass(frozen=True)
class TheReadKey(Then[AKeyOwnerAndACaller, Answer]):
    """읽은 키가 통째로 온다."""

    started: datetime

    @override
    def says(self) -> str:
        return "심은 키 전체가 온다"

    @override
    def look(self, laid: AKeyOwnerAndACaller, answered: Answered[Answer]) -> list[Verdict]:
        node = answered.response
        if not isinstance(node, KeypairNode):
            return [Refused(GenericBadRequest, answered.raised)]
        return SeededKeyLook(self.started).extra_key(node, laid, SERVER_RATE_LIMIT)


@dataclass(frozen=True)
class TheDeletedKey(Then[AKeyOwnerAndACaller, Answer]):
    """지운 키의 access key가 온다."""

    @override
    def says(self) -> str:
        return "지운 키의 access key가 온다"

    @override
    def look(self, laid: AKeyOwnerAndACaller, answered: Answered[Answer]) -> list[Verdict]:
        payload = answered.response
        if not isinstance(payload, AdminDeleteKeypairPayload):
            return [Refused(GenericBadRequest, answered.raised)]
        return [
            Held(
                "access_key",
                payload.access_key,
                SameAs(str(_extra_of(laid).access_key), "심은 키"),
            )
        ]


@dataclass(frozen=True)
class TheSSHKeyAfterwards(Then[AKeyOwnerAndACaller, Answer]):
    """대상 기본 키의 access key가 오고, 뒤이어 읽은 공개키가 기대한 값이다."""

    public_key: str | None

    @override
    def says(self) -> str:
        return "대상 기본 키가 오고, 뒤이은 읽기에서 공개키가 바뀌어 있다"

    @override
    def look(self, laid: AKeyOwnerAndACaller, answered: Answered[Answer]) -> list[Verdict]:
        after = answered.response
        if not isinstance(after, SSHAfterwards):
            return [Refused(GenericBadRequest, answered.raised)]
        return [
            Held("access_key", after.answered, SameAs(after.default_key, "대상의 기본 키")),
            Same("뒤이은 읽기의 ssh_public_key", after.public_key, self.public_key),
        ]


@dataclass(frozen=True)
class TheSSHPublicKey(Then[AKeyOwnerAndACaller, Answer]):
    """대상 기본 키의 access key와 공개키만 온다."""

    @override
    def says(self) -> str:
        return "access key와 공개키만 온다"

    @override
    def look(self, laid: AKeyOwnerAndACaller, answered: Answered[Answer]) -> list[Verdict]:
        read = answered.response
        if not isinstance(read, SSHRead):
            return [Refused(GenericBadRequest, answered.raised)]
        return [
            Held(
                "keypair.access_key",
                read.payload.keypair.access_key,
                SameAs(read.default_key, "대상의 기본 키"),
            ),
            Same("keypair.ssh_public_key", read.payload.keypair.ssh_public_key, ""),
        ]


def _by_owner(nodes: list[KeypairNode]) -> list[KeypairNode]:
    return sorted(nodes, key=lambda one: str(one.user_id))


def _owners_in_order(
    owners: tuple[tuple[UserData, KeyPairResourcePolicyData], ...],
) -> list[tuple[UserData, KeyPairResourcePolicyData]]:
    return sorted(owners, key=lambda one: str(one[0].id))


@dataclass(frozen=True)
class EveryKeyComes(Then[KeysOfEveryone, Answer]):
    """모든 사용자의 기본 키가 오고, limit 자리는 비어서 온다."""

    started: datetime

    @override
    def says(self) -> str:
        return "모든 사용자의 키가 주인 순으로 온다"

    @override
    def look(self, laid: KeysOfEveryone, answered: Answered[Answer]) -> list[Verdict]:
        payload = answered.response
        if not isinstance(payload, AdminSearchKeypairsPayload):
            return [Refused(InsufficientPrivilege, answered.raised)]
        nodes = _by_owner(payload.items)
        seen: list[Verdict] = [Same("items.length", len(nodes), len(laid.owners))]
        look = SeededKeyLook(self.started)
        for index, (node, (owner, policy)) in enumerate(
            zip(nodes, _owners_in_order(laid.owners), strict=False)
        ):
            seen.extend(look.default_key(node, owner, policy, at=f"items[{index}]."))
        seen.extend([
            Same("pagination.total", payload.pagination.total, len(laid.owners)),
            Same("pagination.offset", payload.pagination.offset, 0),
            Same("pagination.limit", payload.pagination.limit, None),
        ])
        return seen


@dataclass(frozen=True)
class TheFirstPolicysKeyOnly(Then[KeysOfEveryone, Answer]):
    """첫 사용자의 정책을 쓰는 키 하나만 온다."""

    started: datetime

    @override
    def says(self) -> str:
        return "그 정책을 쓰는 키 하나만 온다"

    @override
    def look(self, laid: KeysOfEveryone, answered: Answered[Answer]) -> list[Verdict]:
        result = answered.response
        if not isinstance(result, SearchResult):
            return [Refused(InsufficientPrivilege, answered.raised)]
        owner, policy = laid.owners[0]
        seen: list[Verdict] = [Same("items.length", len(result.items), 1)]
        if result.items:
            seen.extend(
                SeededKeyLook(self.started).default_key(
                    result.items[0], owner, policy, at="items[0]."
                )
            )
        seen.extend([
            Same("total_count", result.total_count, 1),
            Same("has_next_page", result.has_next_page, False),
            Same("has_previous_page", result.has_previous_page, False),
        ])
        return seen


# ------------------------------------------------------------------ scenarios


@dataclass(frozen=True)
class AUserGrantedUpdateMakesAKeyForAnother(
    Scenario[SeedingSession, AKeyOwnerAndACaller, UserAdapter, Answer]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-user-granted-update-on-another-makes-them-a-key-of-the-given-policy"

    @override
    def describe(self) -> str:
        return (
            "슈퍼관리자가 아니어도 대상 사용자 스코프에서 UPDATE를 받은 사용자가 정책을 주고 키를 "
            "만들면, 기본 아닌 새 키와 secret이 온다"
        )

    @override
    def given(self) -> Given[SeedingSession, AKeyOwnerAndACaller]:
        return SomeoneAndAKeyOwner(grant=(Permission.UPDATE,))

    @override
    def when(self) -> When[AKeyOwnerAndACaller, UserAdapter, Answer]:
        return MakingAKeyForTheTarget()

    @override
    def then(self) -> Then[AKeyOwnerAndACaller, Answer]:
        return TheNewKey(started=self.started)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotMakeAKeyForAnother(
    Scenario[SeedingSession, AKeyOwnerAndACaller, UserAdapter, Answer]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-make-a-key-for-another"

    @override
    def describe(self) -> str:
        return "역할 없이 키를 만들려 하면, 엔티티 권한 문이 막는다"

    @override
    def given(self) -> Given[SeedingSession, AKeyOwnerAndACaller]:
        return SomeoneAndAKeyOwner()

    @override
    def when(self) -> When[AKeyOwnerAndACaller, UserAdapter, Answer]:
        return MakingAKeyForTheTarget()

    @override
    def then(self) -> Then[AKeyOwnerAndACaller, Answer]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class AKeyMayNotBeMadeUnderAMissingPolicy(
    Scenario[SeedingSession, AKeyOwnerAndACaller, UserAdapter, Answer]
):
    @override
    def summary(self) -> str:
        return "a-key-may-not-be-made-under-a-policy-that-does-not-exist"

    @override
    def describe(self) -> str:
        return "권한 받은 사용자가 없는 정책 이름을 주면, 입력 검증이 막는다"

    @override
    def given(self) -> Given[SeedingSession, AKeyOwnerAndACaller]:
        return SomeoneAndAKeyOwner(grant=(Permission.UPDATE,))

    @override
    def when(self) -> When[AKeyOwnerAndACaller, UserAdapter, Answer]:
        return MakingAKeyForTheTarget(missing_policy=True)

    @override
    def then(self) -> Then[AKeyOwnerAndACaller, Answer]:
        return TheCallIsRefused(KeypairResourcePolicyNotFound)


@dataclass(frozen=True)
class AGrantedUserChangesOnlyTheRateLimit(
    Scenario[SeedingSession, AKeyOwnerAndACaller, UserAdapter, Answer]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-granted-user-changing-another-users-rate-limit-changes-only-that"

    @override
    def describe(self) -> str:
        return (
            "대상 스코프에서 READ와 UPDATE를 받은 사용자가 요청 한도만 주면, 나머지는 그대로이고 "
            "한도만 바뀐 키 노드가 온다"
        )

    @override
    def given(self) -> Given[SeedingSession, AKeyOwnerAndACaller]:
        return SomeoneAndAKeyOwner(grant=(Permission.READ, Permission.UPDATE), extra=True)

    @override
    def when(self) -> When[AKeyOwnerAndACaller, UserAdapter, Answer]:
        return ChangingTheExtraKey()

    @override
    def then(self) -> Then[AKeyOwnerAndACaller, Answer]:
        return TheChangedKey(started=self.started)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotChangeAnothersKey(
    Scenario[SeedingSession, AKeyOwnerAndACaller, UserAdapter, Answer]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-change-another-users-key"

    @override
    def describe(self) -> str:
        return "역할 없이 바꾸려 하면, 소유자 조회 단계가 막는다"

    @override
    def given(self) -> Given[SeedingSession, AKeyOwnerAndACaller]:
        return SomeoneAndAKeyOwner(extra=True)

    @override
    def when(self) -> When[AKeyOwnerAndACaller, UserAdapter, Answer]:
        return ChangingTheExtraKey()

    @override
    def then(self) -> Then[AKeyOwnerAndACaller, Answer]:
        return TheCallIsRefused(GenericBadRequest)


@dataclass(frozen=True)
class AReaderMayNotChangeAnothersKey(
    Scenario[SeedingSession, AKeyOwnerAndACaller, UserAdapter, Answer]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-only-read-may-not-change-another-users-key"

    @override
    def describe(self) -> str:
        return "READ만 받고 바꾸려 하면, 엔티티 권한 문이 막는다"

    @override
    def given(self) -> Given[SeedingSession, AKeyOwnerAndACaller]:
        return SomeoneAndAKeyOwner(grant=(Permission.READ,), extra=True)

    @override
    def when(self) -> When[AKeyOwnerAndACaller, UserAdapter, Answer]:
        return ChangingTheExtraKey()

    @override
    def then(self) -> Then[AKeyOwnerAndACaller, Answer]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class AKeyMayNotBeMovedToAMissingPolicy(
    Scenario[SeedingSession, AKeyOwnerAndACaller, UserAdapter, Answer]
):
    @override
    def summary(self) -> str:
        return "another-users-key-may-not-be-moved-to-a-policy-that-does-not-exist"

    @override
    def describe(self) -> str:
        return "권한 받은 사용자가 없는 정책 이름을 주면, 입력 검증이 막는다"

    @override
    def given(self) -> Given[SeedingSession, AKeyOwnerAndACaller]:
        return SomeoneAndAKeyOwner(grant=(Permission.READ, Permission.UPDATE), extra=True)

    @override
    def when(self) -> When[AKeyOwnerAndACaller, UserAdapter, Answer]:
        return ChangingTheExtraKey(missing_policy=True)

    @override
    def then(self) -> Then[AKeyOwnerAndACaller, Answer]:
        return TheCallIsRefused(KeypairResourcePolicyNotFound)


@dataclass(frozen=True)
class AGrantedUserDeletesAnothersExtraKey(
    Scenario[SeedingSession, AKeyOwnerAndACaller, UserAdapter, Answer]
):
    @override
    def summary(self) -> str:
        return "a-granted-user-deleting-another-users-extra-key-gets-its-access-key"

    @override
    def describe(self) -> str:
        return "대상 스코프에서 READ와 UPDATE를 받은 사용자가 지우면, 지운 키의 access key가 답으로 온다"

    @override
    def given(self) -> Given[SeedingSession, AKeyOwnerAndACaller]:
        return SomeoneAndAKeyOwner(grant=(Permission.READ, Permission.UPDATE), extra=True)

    @override
    def when(self) -> When[AKeyOwnerAndACaller, UserAdapter, Answer]:
        return DeletingTheExtraKey()

    @override
    def then(self) -> Then[AKeyOwnerAndACaller, Answer]:
        return TheDeletedKey()


@dataclass(frozen=True)
class AUserGrantedNothingMayNotDeleteAnothersKey(
    Scenario[SeedingSession, AKeyOwnerAndACaller, UserAdapter, Answer]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-delete-another-users-key"

    @override
    def describe(self) -> str:
        return "역할 없이 지우려 하면, 소유자 조회 단계가 막는다"

    @override
    def given(self) -> Given[SeedingSession, AKeyOwnerAndACaller]:
        return SomeoneAndAKeyOwner(extra=True)

    @override
    def when(self) -> When[AKeyOwnerAndACaller, UserAdapter, Answer]:
        return DeletingTheExtraKey()

    @override
    def then(self) -> Then[AKeyOwnerAndACaller, Answer]:
        return TheCallIsRefused(GenericBadRequest)


@dataclass(frozen=True)
class AReaderMayNotDeleteAnothersKey(
    Scenario[SeedingSession, AKeyOwnerAndACaller, UserAdapter, Answer]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-only-read-may-not-delete-another-users-key"

    @override
    def describe(self) -> str:
        return "READ만 받고 지우려 하면, 엔티티 권한 문이 막는다"

    @override
    def given(self) -> Given[SeedingSession, AKeyOwnerAndACaller]:
        return SomeoneAndAKeyOwner(grant=(Permission.READ,), extra=True)

    @override
    def when(self) -> When[AKeyOwnerAndACaller, UserAdapter, Answer]:
        return DeletingTheExtraKey()

    @override
    def then(self) -> Then[AKeyOwnerAndACaller, Answer]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class AnothersDefaultKeyMayNotBeDeleted(
    Scenario[SeedingSession, AKeyOwnerAndACaller, UserAdapter, Answer]
):
    @override
    def summary(self) -> str:
        return "another-users-default-key-may-not-be-deleted"

    @override
    def describe(self) -> str:
        return "권한 받은 사용자가 대상의 기본 키를 지우려 하면, 입력 검증이 막는다"

    @override
    def given(self) -> Given[SeedingSession, AKeyOwnerAndACaller]:
        return SomeoneAndAKeyOwner(grant=(Permission.READ, Permission.UPDATE), helper=True)

    @override
    def when(self) -> When[AKeyOwnerAndACaller, UserAdapter, Answer]:
        return DeletingTheDefaultKey()

    @override
    def then(self) -> Then[AKeyOwnerAndACaller, Answer]:
        return TheCallIsRefused(KeyPairForbidden)


@dataclass(frozen=True)
class AGrantedUserReadsAnothersKey(
    Scenario[SeedingSession, AKeyOwnerAndACaller, UserAdapter, Answer]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-granted-user-reads-another-users-key-by-access-key"

    @override
    def describe(self) -> str:
        return "대상 스코프에서 READ를 받은 사용자가 읽으면, 그 키 노드 전체가 온다"

    @override
    def given(self) -> Given[SeedingSession, AKeyOwnerAndACaller]:
        return SomeoneAndAKeyOwner(grant=(Permission.READ,), extra=True)

    @override
    def when(self) -> When[AKeyOwnerAndACaller, UserAdapter, Answer]:
        return ReadingTheExtraKey()

    @override
    def then(self) -> Then[AKeyOwnerAndACaller, Answer]:
        return TheReadKey(started=self.started)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotReadAnothersKey(
    Scenario[SeedingSession, AKeyOwnerAndACaller, UserAdapter, Answer]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-read-another-users-key"

    @override
    def describe(self) -> str:
        return "역할 없이 읽으려 하면, 소유자 조회 단계가 막는다"

    @override
    def given(self) -> Given[SeedingSession, AKeyOwnerAndACaller]:
        return SomeoneAndAKeyOwner(extra=True)

    @override
    def when(self) -> When[AKeyOwnerAndACaller, UserAdapter, Answer]:
        return ReadingTheExtraKey()

    @override
    def then(self) -> Then[AKeyOwnerAndACaller, Answer]:
        return TheCallIsRefused(GenericBadRequest)


@dataclass(frozen=True)
class AGrantedUserRegistersAnothersSSHKey(
    Scenario[SeedingSession, AKeyOwnerAndACaller, UserAdapter, Answer]
):
    @override
    def summary(self) -> str:
        return "a-granted-user-registering-another-users-ssh-key-gets-the-access-key"

    @override
    def describe(self) -> str:
        return (
            "대상 스코프에서 READ와 UPDATE를 받은 사용자가 공개키와 개인키를 주면, 형식 검사 없이 "
            "덮어쓰고 access key가 답으로 온다"
        )

    @override
    def given(self) -> Given[SeedingSession, AKeyOwnerAndACaller]:
        return SomeoneAndAKeyOwner(grant=(Permission.READ, Permission.UPDATE), helper=True)

    @override
    def when(self) -> When[AKeyOwnerAndACaller, UserAdapter, Answer]:
        return RegisteringAnSSHKey()

    @override
    def then(self) -> Then[AKeyOwnerAndACaller, Answer]:
        return TheSSHKeyAfterwards(public_key=SSH_PUBLIC_KEY)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotRegisterAnothersSSHKey(
    Scenario[SeedingSession, AKeyOwnerAndACaller, UserAdapter, Answer]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-register-another-users-ssh-key"

    @override
    def describe(self) -> str:
        return "역할 없이 등록하려 하면, 소유자 조회 단계가 막는다"

    @override
    def given(self) -> Given[SeedingSession, AKeyOwnerAndACaller]:
        return SomeoneAndAKeyOwner(helper=True)

    @override
    def when(self) -> When[AKeyOwnerAndACaller, UserAdapter, Answer]:
        return RegisteringAnSSHKey()

    @override
    def then(self) -> Then[AKeyOwnerAndACaller, Answer]:
        return TheCallIsRefused(GenericBadRequest)


@dataclass(frozen=True)
class AReaderMayNotRegisterAnothersSSHKey(
    Scenario[SeedingSession, AKeyOwnerAndACaller, UserAdapter, Answer]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-only-read-may-not-register-another-users-ssh-key"

    @override
    def describe(self) -> str:
        return "READ만 받고 등록하려 하면, 엔티티 권한 문이 막는다"

    @override
    def given(self) -> Given[SeedingSession, AKeyOwnerAndACaller]:
        return SomeoneAndAKeyOwner(grant=(Permission.READ,), helper=True)

    @override
    def when(self) -> When[AKeyOwnerAndACaller, UserAdapter, Answer]:
        return RegisteringAnSSHKey()

    @override
    def then(self) -> Then[AKeyOwnerAndACaller, Answer]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class AGrantedUserClearsAnothersSSHKey(
    Scenario[SeedingSession, AKeyOwnerAndACaller, UserAdapter, Answer]
):
    @override
    def summary(self) -> str:
        return "a-granted-user-clearing-another-users-ssh-key-empties-the-public-key"

    @override
    def describe(self) -> str:
        return "대상 스코프에서 READ와 UPDATE를 받은 사용자가 지우면, access key가 오고 공개키가 비워진다"

    @override
    def given(self) -> Given[SeedingSession, AKeyOwnerAndACaller]:
        return SomeoneAndAKeyOwner(grant=(Permission.READ, Permission.UPDATE), helper=True)

    @override
    def when(self) -> When[AKeyOwnerAndACaller, UserAdapter, Answer]:
        return ClearingTheSSHKey()

    @override
    def then(self) -> Then[AKeyOwnerAndACaller, Answer]:
        return TheSSHKeyAfterwards(public_key=None)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotClearAnothersSSHKey(
    Scenario[SeedingSession, AKeyOwnerAndACaller, UserAdapter, Answer]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-clear-another-users-ssh-key"

    @override
    def describe(self) -> str:
        return "역할 없이 지우려 하면, 소유자 조회 단계가 막는다"

    @override
    def given(self) -> Given[SeedingSession, AKeyOwnerAndACaller]:
        return SomeoneAndAKeyOwner(helper=True)

    @override
    def when(self) -> When[AKeyOwnerAndACaller, UserAdapter, Answer]:
        return ClearingTheSSHKey()

    @override
    def then(self) -> Then[AKeyOwnerAndACaller, Answer]:
        return TheCallIsRefused(GenericBadRequest)


@dataclass(frozen=True)
class AReaderMayNotClearAnothersSSHKey(
    Scenario[SeedingSession, AKeyOwnerAndACaller, UserAdapter, Answer]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-only-read-may-not-clear-another-users-ssh-key"

    @override
    def describe(self) -> str:
        return "READ만 받고 지우려 하면, 엔티티 권한 문이 막는다"

    @override
    def given(self) -> Given[SeedingSession, AKeyOwnerAndACaller]:
        return SomeoneAndAKeyOwner(grant=(Permission.READ,), helper=True)

    @override
    def when(self) -> When[AKeyOwnerAndACaller, UserAdapter, Answer]:
        return ClearingTheSSHKey()

    @override
    def then(self) -> Then[AKeyOwnerAndACaller, Answer]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class AGrantedUserReadsAnothersSSHPublicKey(
    Scenario[SeedingSession, AKeyOwnerAndACaller, UserAdapter, Answer]
):
    @override
    def summary(self) -> str:
        return "a-granted-user-reads-another-users-ssh-public-key-only"

    @override
    def describe(self) -> str:
        return (
            "대상 스코프에서 READ를 받은 사용자가 읽으면, access key와 공개키만 오고 개인키는 "
            "오지 않는다"
        )

    @override
    def given(self) -> Given[SeedingSession, AKeyOwnerAndACaller]:
        return SomeoneAndAKeyOwner(grant=(Permission.READ,), helper=True)

    @override
    def when(self) -> When[AKeyOwnerAndACaller, UserAdapter, Answer]:
        return ReadingTheSSHKey()

    @override
    def then(self) -> Then[AKeyOwnerAndACaller, Answer]:
        return TheSSHPublicKey()


@dataclass(frozen=True)
class AUserGrantedNothingMayNotReadAnothersSSHPublicKey(
    Scenario[SeedingSession, AKeyOwnerAndACaller, UserAdapter, Answer]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-read-another-users-ssh-public-key"

    @override
    def describe(self) -> str:
        return "역할 없이 읽으려 하면, 소유자 조회 단계가 막는다"

    @override
    def given(self) -> Given[SeedingSession, AKeyOwnerAndACaller]:
        return SomeoneAndAKeyOwner(helper=True)

    @override
    def when(self) -> When[AKeyOwnerAndACaller, UserAdapter, Answer]:
        return ReadingTheSSHKey()

    @override
    def then(self) -> Then[AKeyOwnerAndACaller, Answer]:
        return TheCallIsRefused(GenericBadRequest)


@dataclass(frozen=True)
class TheSuperadminSearchesEveryKey(Scenario[SeedingSession, KeysOfEveryone, UserAdapter, Answer]):
    started: datetime

    @override
    def summary(self) -> str:
        return "the-superadmin-searching-every-key-gets-every-users-key"

    @override
    def describe(self) -> str:
        return (
            "전역 역할이 문인 키 검색에서 슈퍼관리자가 페이지 인자 없이 훑으면, 모든 사용자의 키가 "
            "오고 limit 자리는 비어서 온다"
        )

    @override
    def given(self) -> Given[SeedingSession, KeysOfEveryone]:
        return ASuperadminAndTwoUsers()

    @override
    def when(self) -> When[KeysOfEveryone, UserAdapter, Answer]:
        return SearchingEveryKey()

    @override
    def then(self) -> Then[KeysOfEveryone, Answer]:
        return EveryKeyComes(started=self.started)


@dataclass(frozen=True)
class OnlyTheSuperadminMaySearchEveryKey(
    Scenario[SeedingSession, KeysOfEveryone, UserAdapter, Answer]
):
    @override
    def summary(self) -> str:
        return "a-user-who-is-not-the-superadmin-may-not-search-every-key"

    @override
    def describe(self) -> str:
        return "권한 받은 사용자가 키 전체 검색을 하려 하면, 전역 역할 문이 막는다"

    @override
    def given(self) -> Given[SeedingSession, KeysOfEveryone]:
        return SomeoneReadingTheDomain()

    @override
    def when(self) -> When[KeysOfEveryone, UserAdapter, Answer]:
        return SearchingEveryKey()

    @override
    def then(self) -> Then[KeysOfEveryone, Answer]:
        return TheCallIsRefused(InsufficientPrivilege)


@dataclass(frozen=True)
class TheSuperadminSearchesKeysOfOnePolicy(
    Scenario[SeedingSession, KeysOfEveryone, UserAdapter, Answer]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "the-superadmin-gql-key-search-by-policy-name-gets-that-policys-keys-only"

    @override
    def describe(self) -> str:
        return "전역 역할이 문인 GQL 키 검색에서 슈퍼관리자가 정책 이름을 주면, 그 정책을 쓰는 키만 온다"

    @override
    def given(self) -> Given[SeedingSession, KeysOfEveryone]:
        return ASuperadminAndTwoUsers()

    @override
    def when(self) -> When[KeysOfEveryone, UserAdapter, Answer]:
        return SearchingKeysOverGQL(by_first_policy=True)

    @override
    def then(self) -> Then[KeysOfEveryone, Answer]:
        return TheFirstPolicysKeyOnly(started=self.started)


@dataclass(frozen=True)
class OnlyTheSuperadminMaySearchKeysOverGQL(
    Scenario[SeedingSession, KeysOfEveryone, UserAdapter, Answer]
):
    @override
    def summary(self) -> str:
        return "a-user-who-is-not-the-superadmin-may-not-search-every-key-over-gql"

    @override
    def describe(self) -> str:
        return "권한 받은 사용자가 GQL 키 검색을 하려 하면, 전역 역할 문이 막는다"

    @override
    def given(self) -> Given[SeedingSession, KeysOfEveryone]:
        return SomeoneReadingTheDomain()

    @override
    def when(self) -> When[KeysOfEveryone, UserAdapter, Answer]:
        return SearchingKeysOverGQL()

    @override
    def then(self) -> Then[KeysOfEveryone, Answer]:
        return TheCallIsRefused(InsufficientPrivilege)


SCENARIOS: list[Scenario[SeedingSession, Any, UserAdapter, Answer]] = [
    AUserGrantedUpdateMakesAKeyForAnother(started=datetime.now(UTC)),
    AUserGrantedNothingMayNotMakeAKeyForAnother(),
    AKeyMayNotBeMadeUnderAMissingPolicy(),
    AGrantedUserChangesOnlyTheRateLimit(started=datetime.now(UTC)),
    AUserGrantedNothingMayNotChangeAnothersKey(),
    AReaderMayNotChangeAnothersKey(),
    AKeyMayNotBeMovedToAMissingPolicy(),
    AGrantedUserDeletesAnothersExtraKey(),
    AUserGrantedNothingMayNotDeleteAnothersKey(),
    AReaderMayNotDeleteAnothersKey(),
    AnothersDefaultKeyMayNotBeDeleted(),
    AGrantedUserReadsAnothersKey(started=datetime.now(UTC)),
    AUserGrantedNothingMayNotReadAnothersKey(),
    AGrantedUserRegistersAnothersSSHKey(),
    AUserGrantedNothingMayNotRegisterAnothersSSHKey(),
    AReaderMayNotRegisterAnothersSSHKey(),
    AGrantedUserClearsAnothersSSHKey(),
    AUserGrantedNothingMayNotClearAnothersSSHKey(),
    AReaderMayNotClearAnothersSSHKey(),
    AGrantedUserReadsAnothersSSHPublicKey(),
    AUserGrantedNothingMayNotReadAnothersSSHPublicKey(),
    TheSuperadminSearchesEveryKey(started=datetime.now(UTC)),
    OnlyTheSuperadminMaySearchEveryKey(),
    TheSuperadminSearchesKeysOfOnePolicy(started=datetime.now(UTC)),
    OnlyTheSuperadminMaySearchKeysOverGQL(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_managing_keypairs(
    scenario: Scenario[SeedingSession, Any, UserAdapter, Answer],
    adapter: UserAdapter,
    engine: ExtendedAsyncSAEngine,
) -> None:
    await run_scenario(scenario, adapter, engine)
