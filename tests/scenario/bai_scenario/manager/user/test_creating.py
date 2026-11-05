"""사용자 만들기 — 누가 만들 수 있고, 무엇이 만들기 전에 막는가."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, override

import pytest

from ai.backend.common.auth.password import PasswordHashAlgorithm, PasswordInfo
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.keypair.response import CreateKeypairPayload
from ai.backend.common.dto.manager.v2.user.request import CreateUserInput
from ai.backend.common.dto.manager.v2.user.response import (
    BulkCreateUsersPayload,
    BulkCreateUsersWithKeypairPayload,
    CreateUserPayload,
    UserNode,
)
from ai.backend.common.dto.manager.v2.user.types import UserRole as UserRoleDTO
from ai.backend.common.dto.manager.v2.user.types import UserStatus as UserStatusDTO
from ai.backend.manager.api.adapters.user.adapter import UserAdapter
from ai.backend.manager.data.domain.types import DomainData
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.data.user.types import UserData, UserStatus
from ai.backend.manager.errors.auth import InsufficientPrivilege
from ai.backend.manager.errors.base.entity import EntityNotFoundError
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.user.creators import UserCreator
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.user.creators import UserCreateSpec
from ai.backend.manager.services.user.actions.create_user import BulkCreateUserAction
from ai.backend.testutils.scenario_steps import (
    Answered,
    Condition,
    Given,
    Held,
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
from bai_scenario.components.domain import WAS_HERE, SomeoneOf, WrittenByThisRun
from bai_scenario.components.user import AGrant, AKeyIsThere
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario
from bai_scenario.seeds.domain.domain import TestSeedDomain
from bai_scenario.seeds.resource_policy.keypair import TestSeedDefaultKeypairPolicy
from bai_scenario.seeds.resource_policy.user import TestSeedUserPolicy

MADE = "made"
"""만들려는 사용자의 이름. 시나리오가 정한 값이다."""

RATE_LIMIT = 10000
"""요청 한도를 적지 않은 키에 데이터베이스가 넣는 값."""


@dataclass(frozen=True)
class ADomainAndACaller:
    """사용자를 만들 도메인과, 만들려는 사람."""

    domain: DomainData
    caller: UserData


@dataclass(frozen=True)
class ADomainACallerAndThePolicies:
    """사용자를 만들 도메인, 만들려는 사람, 새 사용자와 새 키가 받을 정책 이름."""

    domain: DomainData
    caller: UserData
    user_policy: str
    keypair_policy: str


@dataclass(frozen=True)
class SomeoneInADomain(Given[Any, ADomainAndACaller]):
    """도메인 하나와 그 도메인의 사용자 한 명. `granted`면 도메인 스코프에서 사용자 생성 권한을 받는다."""

    granted: bool

    @override
    def describe(self) -> str:
        if self.granted:
            return Says(
                "도메인 하나와, 그 도메인 스코프에서 사용자 생성 권한을 받은 사용자 한 명",
                english=(
                    "one domain and one user granted the user create permission in the domain scope"
                ),
            )
        return Says(
            "도메인 하나와, 아무 권한도 받지 않은 사용자 한 명",
            english="one domain and one user granted no permission",
        )

    @override
    async def lay(self, seeding: Any) -> ADomainAndACaller:
        domain = await seeding.creating(TestSeedDomain(name_hint="home", description=WAS_HERE))
        caller = await seeding.within(SomeoneOf(domain))
        if self.granted:
            await seeding.within(AGrant.on_domain(domain, caller, Permission.CREATE))
        return ADomainAndACaller(seeding.made(domain), seeding.made(caller))


@dataclass(frozen=True)
class SomeoneWithThePolicies(Given[Any, ADomainACallerAndThePolicies]):
    """도메인 하나, 그 도메인의 사용자 한 명, 그리고 새 사용자와 새 키가 받을 정책들.

    ``granted``면 호출자가 도메인 스코프에서 사용자 생성 권한을 받는다. 키페어가 정책을
    대지 않으면 받는 기본 정책도 함께 세운다. 사용자를 만드는 경로가 그 정책을 읽는다.
    """

    granted: bool = True
    role: UserRole = UserRole.USER

    @override
    def describe(self) -> str:
        role = self.role.value
        if self.granted:
            return Says(
                f"도메인 하나와 {role} 한 명, 호출자는 도메인 스코프에서 사용자 생성 권한을 "
                "받았습니다",
                english=(
                    f"one domain and one {role}, and the caller holds the user create permission "
                    "in the domain scope"
                ),
            )
        return Says(
            f"도메인 하나와 {role} 한 명, 호출자는 아무 권한도 받지 않았습니다",
            english=f"one domain and one {role}, and the caller holds no permission",
        )

    @override
    async def lay(self, seeding: Any) -> ADomainACallerAndThePolicies:
        domain = await seeding.creating(TestSeedDomain(name_hint="home", description=WAS_HERE))
        user_policy = await seeding.creating(TestSeedUserPolicy())
        keypair_policy = await seeding.creating(TestSeedDefaultKeypairPolicy())
        caller = await seeding.within(SomeoneOf(domain, role=self.role))
        if self.granted:
            await seeding.within(AGrant.on_domain(domain, caller, Permission.CREATE))
        return ADomainACallerAndThePolicies(
            seeding.made(domain),
            seeding.made(caller),
            seeding.made(user_policy).name,
            seeding.made(keypair_policy).name,
        )


@dataclass(frozen=True)
class CreatingAUser(When[ADomainAndACaller, UserAdapter, Any]):
    """필수 항목만 주고 사용자 하나를 만든다. `domain_name`을 주면 그 이름을 도메인으로 댄다."""

    domain_name: str | None = None

    @override
    def operation(self) -> str:
        return "create_user"

    @override
    def describe(self, laid: ADomainAndACaller) -> str:
        domain_name = self.domain_name or laid.domain.name
        return Says(
            f"{laid.caller.username}이 {domain_name}에 {MADE}을 생성합니다",
            english=f"{laid.caller.username} creates {MADE} in {domain_name}",
        )

    @override
    async def call(self, adapter: UserAdapter, laid: ADomainAndACaller) -> Any:
        with ActingAs(laid.caller):
            return await adapter.create_user(
                CreateUserInput(
                    email=f"{MADE}@scenario.local",
                    username=MADE,
                    password="scenario-password",
                    domain_name=self.domain_name or laid.domain.name,
                    status=UserStatusDTO.ACTIVE,
                    role=UserRoleDTO.USER,
                )
            )


@dataclass(frozen=True)
class BulkCreatingAUser(When[ADomainAndACaller, UserAdapter, Any]):
    """사용자 하나를 일괄 생성으로 만든다. `with_keypair`면 키를 함께 받는 쪽을 부른다."""

    with_keypair: bool

    @override
    def operation(self) -> str:
        return "bulk_create_users_with_keypair" if self.with_keypair else "bulk_create_users"

    @override
    def describe(self, laid: ADomainAndACaller) -> str:
        return Says(
            f"{laid.caller.username}이 {laid.domain.name}에 {MADE}을 일괄 생성합니다",
            english=f"{laid.caller.username} bulk creates {MADE} in {laid.domain.name}",
        )

    @override
    async def call(self, adapter: UserAdapter, laid: ADomainAndACaller) -> Any:
        action = BulkCreateUserAction(
            items=[
                UserCreateSpec(
                    creator=UserCreator(
                        email=f"{MADE}@scenario.local",
                        username=MADE,
                        password=PasswordInfo(
                            password="scenario-password",
                            algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
                            rounds=1000,
                            salt_size=16,
                        ),
                        need_password_change=False,
                        domain_id=laid.domain.id,
                        status=UserStatus.ACTIVE,
                        role=UserRole.USER,
                    )
                )
            ]
        )
        with ActingAs(laid.caller):
            if self.with_keypair:
                return await adapter.bulk_create_users_with_keypair(action)
            return await adapter.bulk_create_users(action)


@dataclass(frozen=True)
class CreatingAUserUnderThePolicies(When[ADomainACallerAndThePolicies, UserAdapter, Any]):
    """심어 둔 사용자 정책을 대며 사용자 하나를 만든다."""

    @override
    def operation(self) -> str:
        return "create_user"

    @override
    def describe(self, laid: ADomainACallerAndThePolicies) -> str:
        return Says(
            f"{laid.caller.username}이 {laid.domain.name}에 {MADE}을 생성합니다",
            english=f"{laid.caller.username} creates {MADE} in {laid.domain.name}",
        )

    @override
    async def call(self, adapter: UserAdapter, laid: ADomainACallerAndThePolicies) -> Any:
        with ActingAs(laid.caller):
            return await adapter.create_user(
                CreateUserInput(
                    email=f"{MADE}@scenario.local",
                    username=MADE,
                    password="scenario-password",
                    domain_name=laid.domain.name,
                    status=UserStatusDTO.ACTIVE,
                    role=UserRoleDTO.USER,
                    resource_policy=laid.user_policy,
                )
            )


@dataclass(frozen=True)
class BulkCreatingAUserUnderThePolicies(When[ADomainACallerAndThePolicies, UserAdapter, Any]):
    """심어 둔 사용자 정책을 대며 사용자 하나를 일괄 생성한다."""

    with_keypair: bool

    @override
    def operation(self) -> str:
        return "bulk_create_users_with_keypair" if self.with_keypair else "bulk_create_users"

    @override
    def describe(self, laid: ADomainACallerAndThePolicies) -> str:
        return Says(
            f"{laid.caller.username}이 {laid.domain.name}에 {MADE}을 일괄 생성합니다",
            english=f"{laid.caller.username} bulk creates {MADE} in {laid.domain.name}",
        )

    @override
    async def call(self, adapter: UserAdapter, laid: ADomainACallerAndThePolicies) -> Any:
        action = BulkCreateUserAction(
            items=[
                UserCreateSpec(
                    creator=UserCreator(
                        email=f"{MADE}@scenario.local",
                        username=MADE,
                        password=PasswordInfo(
                            password="scenario-password",
                            algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
                            rounds=1000,
                            salt_size=16,
                        ),
                        need_password_change=False,
                        domain_id=laid.domain.id,
                        status=UserStatus.ACTIVE,
                        role=UserRole.USER,
                        resource_policy=laid.user_policy,
                    )
                )
            ]
        )
        with ActingAs(laid.caller):
            if self.with_keypair:
                return await adapter.bulk_create_users_with_keypair(action)
            return await adapter.bulk_create_users(action)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotCreateAUser(
    Scenario[TestSeedingSession, ADomainAndACaller, UserAdapter, Any]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-create-a-user"

    @override
    def describe(self) -> str:
        return Says(
            "역할을 받지 않은 사용자가 생성하려 하면, 도메인 스코프 권한 문이 막습니다",
            english=(
                "a user holding no role who tries to create a user is rejected by the "
                "domain scope permission gate"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ADomainAndACaller]:
        return SomeoneInADomain(granted=False)

    @override
    def when(self) -> When[ADomainAndACaller, UserAdapter, Any]:
        return CreatingAUser()

    @override
    def then(self) -> Then[ADomainAndACaller, Any]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class ANameNoDomainHoldsMayNotHoldAUser(
    Scenario[TestSeedingSession, ADomainAndACaller, UserAdapter, Any]
):
    @override
    def summary(self) -> str:
        return "a-user-may-not-be-created-in-a-domain-name-nothing-answers-to"

    @override
    def describe(self) -> str:
        return Says(
            "권한 받은 사용자가 어떤 도메인도 아닌 이름을 주면, "
            "도메인 이름 조회 단계가 대상 없음으로 막습니다",
            english=(
                "when a user holding the permission gives a domain name nothing answers to, "
                "the domain name lookup step rejects it as not found"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ADomainAndACaller]:
        return SomeoneInADomain(granted=True)

    @override
    def when(self) -> When[ADomainAndACaller, UserAdapter, Any]:
        return CreatingAUser(domain_name="no-such-domain")

    @override
    def then(self) -> Then[ADomainAndACaller, Any]:
        return TheCallIsRefused(EntityNotFoundError)


@dataclass(frozen=True)
class OnlyTheSuperadminMayBulkCreate(
    Scenario[TestSeedingSession, ADomainAndACaller, UserAdapter, Any]
):
    @override
    def summary(self) -> str:
        return "a-user-who-is-not-the-superadmin-may-not-bulk-create-users"

    @override
    def describe(self) -> str:
        return Says(
            "도메인 스코프에서 CREATE 를 받은 사용자라도 일괄 생성하려 하면, "
            "전역 역할 문이 막습니다",
            english=(
                "even a user granted CREATE in the domain scope is rejected by the global "
                "role gate when bulk creating users"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ADomainAndACaller]:
        return SomeoneInADomain(granted=True)

    @override
    def when(self) -> When[ADomainAndACaller, UserAdapter, Any]:
        return BulkCreatingAUser(with_keypair=False)

    @override
    def then(self) -> Then[ADomainAndACaller, Any]:
        return TheCallIsRefused(InsufficientPrivilege)


@dataclass(frozen=True)
class OnlyTheSuperadminMayBulkCreateWithKeypairs(
    Scenario[TestSeedingSession, ADomainAndACaller, UserAdapter, Any]
):
    @override
    def summary(self) -> str:
        return "a-user-who-is-not-the-superadmin-may-not-bulk-create-users-with-keypairs"

    @override
    def describe(self) -> str:
        return Says(
            "권한 받은 사용자가 이 일괄 생성을 하려 하면, 전역 역할 문이 막습니다",
            english=(
                "a user holding the permission is rejected by the global role gate when "
                "calling this bulk create"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ADomainAndACaller]:
        return SomeoneInADomain(granted=True)

    @override
    def when(self) -> When[ADomainAndACaller, UserAdapter, Any]:
        return BulkCreatingAUser(with_keypair=True)

    @override
    def then(self) -> Then[ADomainAndACaller, Any]:
        return TheCallIsRefused(InsufficientPrivilege)


@dataclass(frozen=True)
class ASecretIsFilled(Condition[str]):
    """비밀 키가 빈 값이 아니다. 값은 실행마다 새로 만들어진다."""

    @override
    def says(self) -> str:
        return Says(
            "매니저가 만든 비밀 키가 채워져 있습니다",
            english="the secret key the manager made is filled",
        )

    @override
    def holds(self, got: str) -> bool:
        return bool(got)


def _created_user_verdicts(
    started: datetime,
    laid: ADomainACallerAndThePolicies,
    node: UserNode,
    main_access_key: Condition[str | None] | None,
) -> list[Verdict]:
    written = WrittenByThisRun(started)
    key: Verdict = (
        Held(
            "user.organization.main_access_key", node.organization.main_access_key, main_access_key
        )
        if main_access_key is not None
        else Held(
            "user.organization.main_access_key", node.organization.main_access_key, AKeyIsThere()
        )
    )
    return [
        Skipped("user.id", Says("데이터베이스가 생성합니다", english="the database generates it")),
        Held(
            "user.entity_id",
            node.entity_id,
            SameAs(node.id, Says("그 사용자의 id", english="the user's own id")),
        ),
        Same("user.basic_info.username", node.basic_info.username, MADE),
        Same("user.basic_info.email", node.basic_info.email, f"{MADE}@scenario.local"),
        Same("user.basic_info.full_name", node.basic_info.full_name, None),
        Same("user.basic_info.description", node.basic_info.description, None),
        Same("user.basic_info.integration_name", node.basic_info.integration_name, None),
        Same("user.status.status", str(node.status.status), "active"),
        Same("user.status.status_info", node.status.status_info, None),
        Same("user.status.need_password_change", node.status.need_password_change, False),
        Same("user.organization.domain_name", node.organization.domain_name, laid.domain.name),
        Held(
            "user.organization.domain_id",
            node.organization.domain_id,
            SameAs(
                laid.domain.id,
                Says("미리 저장한 도메인의 id", english="the id of the domain seeded in advance"),
            ),
        ),
        Same("user.organization.role", str(node.organization.role), "user"),
        Same(
            "user.organization.resource_policy", node.organization.resource_policy, laid.user_policy
        ),
        key,
        Same("user.security.allowed_client_ip", node.security.allowed_client_ip, None),
        Same("user.security.totp_activated", node.security.totp_activated, False),
        Same("user.security.totp_activated_at", node.security.totp_activated_at, None),
        Same("user.security.sudo_session_enabled", node.security.sudo_session_enabled, False),
        Same("user.container.container_uid", node.container.container_uid, None),
        Same("user.container.container_main_gid", node.container.container_main_gid, None),
        Same("user.container.container_gids", node.container.container_gids, None),
        Held("user.timestamps.created_at", node.timestamps.created_at, written),
        Held("user.timestamps.modified_at", node.timestamps.modified_at, written),
    ]


def _created_keypair_verdicts(
    started: datetime,
    laid: ADomainACallerAndThePolicies,
    payload: CreateKeypairPayload,
    owner: UserNode,
    at: str,
) -> list[Verdict]:
    node = payload.keypair
    written = WrittenByThisRun(started)
    return [
        Skipped(
            f"{at}keypair.id",
            Says(
                "매니저가 만든 access key 입니다", english="it is the access key the manager made"
            ),
        ),
        Skipped(
            f"{at}keypair.field_id",
            Says("데이터베이스가 생성합니다", english="the database generates it"),
        ),
        Skipped(
            f"{at}keypair.access_key",
            Says("매니저가 만듭니다", english="the manager creates it"),
        ),
        Same(f"{at}keypair.is_active", node.is_active, True),
        Same(f"{at}keypair.is_admin", node.is_admin, False),
        Same(f"{at}keypair.is_default", node.is_default, True),
        Same(f"{at}keypair.rate_limit", node.rate_limit, RATE_LIMIT),
        Same(f"{at}keypair.resource_policy", node.resource_policy, laid.keypair_policy),
        Skipped(
            f"{at}keypair.ssh_public_key",
            Says("매니저가 만든 RSA 키입니다", english="it is the RSA key the manager made"),
        ),
        Same(f"{at}keypair.num_queries", node.num_queries, 0),
        Same(f"{at}keypair.last_used", node.last_used, None),
        Held(
            f"{at}keypair.user_id",
            node.user_id,
            SameAs(owner.id, Says("방금 만든 사용자", english="the user just created")),
        ),
        Held(f"{at}keypair.created_at", node.created_at, written),
        Held(f"{at}keypair.modified_at", node.modified_at, written),
        Held(f"{at}secret_key", payload.secret_key, ASecretIsFilled()),
    ]


@dataclass(frozen=True)
class TheCreatedUserAndItsKeypair(Then[ADomainACallerAndThePolicies, Any]):
    """만든 사용자와 그 사용자의 기본 키가 통째로 온다."""

    started: datetime

    @override
    def says(self) -> str:
        return Says(
            "만든 사용자 전체와, 그 사용자의 기본 키가 비밀 키와 함께 응답으로 옵니다",
            english=(
                "the whole user just created and its default keypair with the secret key come back"
            ),
        )

    @override
    def look(self, laid: ADomainACallerAndThePolicies, answered: Answered[Any]) -> list[Verdict]:
        payload = answered.response
        if not isinstance(payload, CreateUserPayload):
            return [Same("raised", type(answered.raised).__name__, None)]
        return [
            *_created_user_verdicts(
                self.started,
                laid,
                payload.user,
                SameAs(
                    payload.keypair.keypair.access_key,
                    Says("이 호출이 만든 키", english="the keypair this call made"),
                ),
            ),
            *_created_keypair_verdicts(self.started, laid, payload.keypair, payload.user, ""),
        ]


@dataclass(frozen=True)
class TheBulkCreatedUser(Then[ADomainACallerAndThePolicies, Any]):
    """일괄 생성이 만든 사용자 하나가 온다. 실패 목록은 비어 있다."""

    started: datetime

    @override
    def says(self) -> str:
        return Says(
            "만든 사용자 하나가 응답으로 오고, 실패한 것은 없습니다",
            english="the user just created comes back and none failed",
        )

    @override
    def look(self, laid: ADomainACallerAndThePolicies, answered: Answered[Any]) -> list[Verdict]:
        payload = answered.response
        if not isinstance(payload, BulkCreateUsersPayload):
            return [Same("raised", type(answered.raised).__name__, None)]
        verdicts: list[Verdict] = [
            Same("created_users.length", len(payload.created_users), 1),
            Same("failed", payload.failed, []),
        ]
        for node in payload.created_users:
            verdicts.extend(_created_user_verdicts(self.started, laid, node, None))
        return verdicts


@dataclass(frozen=True)
class TheBulkCreatedUserWithItsKeypair(Then[ADomainACallerAndThePolicies, Any]):
    """일괄 생성이 만든 사용자와 키가 함께 온다."""

    started: datetime

    @override
    def says(self) -> str:
        return Says(
            "만든 사용자와 그 기본 키가 비밀 키와 함께 응답으로 오고, 실패한 것은 없습니다",
            english=(
                "the user just created and its default keypair with the secret key come back "
                "and none failed"
            ),
        )

    @override
    def look(self, laid: ADomainACallerAndThePolicies, answered: Answered[Any]) -> list[Verdict]:
        payload = answered.response
        if not isinstance(payload, BulkCreateUsersWithKeypairPayload):
            return [Same("raised", type(answered.raised).__name__, None)]
        verdicts: list[Verdict] = [
            Same("created.length", len(payload.created), 1),
            Same("failed", payload.failed, []),
        ]
        for item in payload.created:
            verdicts.extend(
                _created_user_verdicts(
                    self.started,
                    laid,
                    item.user,
                    SameAs(
                        item.keypair.keypair.access_key,
                        Says("이 호출이 만든 키", english="the keypair this call made"),
                    ),
                )
            )
            verdicts.extend(
                _created_keypair_verdicts(
                    self.started, laid, item.keypair, item.user, "created[0]."
                )
            )
        return verdicts


@dataclass(frozen=True)
class AGrantedCreatorMakesAUser(
    Scenario[TestSeedingSession, ADomainACallerAndThePolicies, UserAdapter, Any]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-user-granted-create-on-a-domain-makes-a-user-in-it"

    @override
    def describe(self) -> str:
        return Says(
            "도메인 스코프에서 사용자 생성 권한을 받은 사용자가 그 도메인에 사용자를 만들면, "
            "만든 사용자 전체와 기본 키가 비밀 키와 함께 옵니다",
            english=(
                "when a user granted the user create permission in the domain scope creates a "
                "user in that domain, the whole user just created and its default keypair "
                "with the secret key come back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ADomainACallerAndThePolicies]:
        return SomeoneWithThePolicies(granted=True)

    @override
    def when(self) -> When[ADomainACallerAndThePolicies, UserAdapter, Any]:
        return CreatingAUserUnderThePolicies()

    @override
    def then(self) -> Then[ADomainACallerAndThePolicies, Any]:
        return TheCreatedUserAndItsKeypair(started=self.started)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotCreateAUserWithThePolicies(
    Scenario[TestSeedingSession, ADomainACallerAndThePolicies, UserAdapter, Any]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-create-a-user-even-with-the-policies-laid"

    @override
    def describe(self) -> str:
        return Says(
            "권한을 받지 않은 사용자가 사용자를 만들려 하면, 도메인 스코프 권한 문이 막습니다",
            english=(
                "a user holding no permission who tries to create a user is rejected by the "
                "domain scope permission gate"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ADomainACallerAndThePolicies]:
        return SomeoneWithThePolicies(granted=False)

    @override
    def when(self) -> When[ADomainACallerAndThePolicies, UserAdapter, Any]:
        return CreatingAUserUnderThePolicies()

    @override
    def then(self) -> Then[ADomainACallerAndThePolicies, Any]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class TheSuperadminBulkCreatesAUser(
    Scenario[TestSeedingSession, ADomainACallerAndThePolicies, UserAdapter, Any]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "the-superadmin-bulk-creates-a-user"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 사용자 하나를 일괄 생성하면, 만든 사용자 하나가 오고 실패한 것은 "
            "없습니다",
            english=(
                "when the superadmin bulk creates one user, the user just created comes back "
                "and none failed"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ADomainACallerAndThePolicies]:
        return SomeoneWithThePolicies(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ADomainACallerAndThePolicies, UserAdapter, Any]:
        return BulkCreatingAUserUnderThePolicies(with_keypair=False)

    @override
    def then(self) -> Then[ADomainACallerAndThePolicies, Any]:
        return TheBulkCreatedUser(started=self.started)


@dataclass(frozen=True)
class TheSuperadminBulkCreatesAUserWithItsKeypair(
    Scenario[TestSeedingSession, ADomainACallerAndThePolicies, UserAdapter, Any]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "the-superadmin-bulk-creates-a-user-and-gets-its-keypair"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 키를 함께 받는 일괄 생성으로 사용자 하나를 만들면, 만든 사용자와 "
            "그 기본 키가 비밀 키와 함께 오고 실패한 것은 없습니다",
            english=(
                "when the superadmin bulk creates one user through the keypair-returning call, "
                "the user just created and its default keypair with the secret key come back "
                "and none failed"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ADomainACallerAndThePolicies]:
        return SomeoneWithThePolicies(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ADomainACallerAndThePolicies, UserAdapter, Any]:
        return BulkCreatingAUserUnderThePolicies(with_keypair=True)

    @override
    def then(self) -> Then[ADomainACallerAndThePolicies, Any]:
        return TheBulkCreatedUserWithItsKeypair(started=self.started)


SCENARIOS: list[Scenario[TestSeedingSession, Any, UserAdapter, Any]] = [
    AUserGrantedNothingMayNotCreateAUser(),
    ANameNoDomainHoldsMayNotHoldAUser(),
    OnlyTheSuperadminMayBulkCreate(),
    OnlyTheSuperadminMayBulkCreateWithKeypairs(),
    AGrantedCreatorMakesAUser(started=datetime.now(UTC)),
    AUserGrantedNothingMayNotCreateAUserWithThePolicies(),
    TheSuperadminBulkCreatesAUser(started=datetime.now(UTC)),
    TheSuperadminBulkCreatesAUserWithItsKeypair(started=datetime.now(UTC)),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_creating(
    scenario: Scenario[TestSeedingSession, Any, UserAdapter, Any],
    adapter: UserAdapter,
    engine: ExtendedAsyncSAEngine,
) -> None:
    await run_scenario(scenario, adapter, engine)
