"""사용자 만들기 — 누가 만들 수 있고, 무엇이 만들기 전에 막는가."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

import pytest
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.domain import WAS_HERE, SomeoneOf
from bai_scenario.components.user import AGrant
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario
from bai_scenario.seeds.domain.domain import SeedDomain

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.user.request import CreateUserInput
from ai.backend.common.dto.manager.v2.user.types import UserRole as UserRoleDTO
from ai.backend.common.dto.manager.v2.user.types import UserStatus as UserStatusDTO
from ai.backend.manager.api.adapters.user.adapter import UserAdapter
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.data.domain.types import DomainData
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.data.user.types import UserData, UserStatus
from ai.backend.manager.errors.auth import InsufficientPrivilege
from ai.backend.manager.errors.base.entity import EntityNotFoundError
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.hasher.types import PasswordInfo
from ai.backend.manager.models.user.creators import UserCreator
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.user.creators import UserCreateSpec
from ai.backend.manager.services.user.actions.create_user import BulkCreateUserAction
from ai.backend.testutils.scenario_steps import Given, Scenario, Then, When

MADE = "made"
"""만들려는 사용자의 이름. 시나리오가 정한 값이다."""


@dataclass(frozen=True)
class ADomainAndACaller:
    """사용자를 만들 도메인과, 만들려는 사람."""

    domain: DomainData
    caller: UserData


@dataclass(frozen=True)
class SomeoneInADomain(Given[Any, ADomainAndACaller]):
    """도메인 하나와 그 도메인의 사용자 한 명. `granted`면 도메인 스코프에서 사용자 생성 권한을 받는다."""

    granted: bool

    @override
    def describe(self) -> str:
        if self.granted:
            return "도메인 하나와, 그 도메인 스코프에서 사용자 생성 권한을 받은 사용자 한 명"
        return "도메인 하나와, 아무 권한도 받지 않은 사용자 한 명"

    @override
    async def lay(self, seeding: Any) -> ADomainAndACaller:
        domain = await seeding.creating(SeedDomain(name_hint="home", description=WAS_HERE))
        caller = await seeding.within(SomeoneOf(domain))
        if self.granted:
            await seeding.within(AGrant.on_domain(domain, caller, Permission.CREATE))
        return ADomainAndACaller(seeding.made(domain), seeding.made(caller))


@dataclass(frozen=True)
class CreatingAUser(When[ADomainAndACaller, UserAdapter, Any]):
    """필수 항목만 주고 사용자 하나를 만든다. `domain_name`을 주면 그 이름을 도메인으로 댄다."""

    domain_name: str | None = None

    @override
    def operation(self) -> str:
        return "create_user"

    @override
    def describe(self, laid: ADomainAndACaller) -> str:
        return f"{laid.caller.username}이 {self.domain_name or laid.domain.name}에 {MADE}을 만듦"

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
        return f"{laid.caller.username}이 {laid.domain.name}에 {MADE}을 일괄 생성"

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
class AUserGrantedNothingMayNotCreateAUser(
    Scenario[SeedingSession, ADomainAndACaller, UserAdapter, Any]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-create-a-user"

    @override
    def describe(self) -> str:
        return "역할을 받지 않은 사용자가 만들려 하면, 도메인 스코프 권한 문이 막는다"

    @override
    def given(self) -> Given[SeedingSession, ADomainAndACaller]:
        return SomeoneInADomain(granted=False)

    @override
    def when(self) -> When[ADomainAndACaller, UserAdapter, Any]:
        return CreatingAUser()

    @override
    def then(self) -> Then[ADomainAndACaller, Any]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class ANameNoDomainHoldsMayNotHoldAUser(
    Scenario[SeedingSession, ADomainAndACaller, UserAdapter, Any]
):
    @override
    def summary(self) -> str:
        return "a-user-may-not-be-created-in-a-domain-name-nothing-answers-to"

    @override
    def describe(self) -> str:
        return (
            "권한 받은 사용자가 없는 도메인 이름을 주면, "
            "도메인 이름 조회 단계가 대상 없음으로 막는다"
        )

    @override
    def given(self) -> Given[SeedingSession, ADomainAndACaller]:
        return SomeoneInADomain(granted=True)

    @override
    def when(self) -> When[ADomainAndACaller, UserAdapter, Any]:
        return CreatingAUser(domain_name="no-such-domain")

    @override
    def then(self) -> Then[ADomainAndACaller, Any]:
        return TheCallIsRefused(EntityNotFoundError)


@dataclass(frozen=True)
class OnlyTheSuperadminMayBulkCreate(Scenario[SeedingSession, ADomainAndACaller, UserAdapter, Any]):
    @override
    def summary(self) -> str:
        return "a-user-who-is-not-the-superadmin-may-not-bulk-create-users"

    @override
    def describe(self) -> str:
        return (
            "도메인 스코프에서 CREATE를 받은 사용자라도 일괄 생성을 하려 하면, "
            "전역 역할 문이 막는다"
        )

    @override
    def given(self) -> Given[SeedingSession, ADomainAndACaller]:
        return SomeoneInADomain(granted=True)

    @override
    def when(self) -> When[ADomainAndACaller, UserAdapter, Any]:
        return BulkCreatingAUser(with_keypair=False)

    @override
    def then(self) -> Then[ADomainAndACaller, Any]:
        return TheCallIsRefused(InsufficientPrivilege)


@dataclass(frozen=True)
class OnlyTheSuperadminMayBulkCreateWithKeypairs(
    Scenario[SeedingSession, ADomainAndACaller, UserAdapter, Any]
):
    @override
    def summary(self) -> str:
        return "a-user-who-is-not-the-superadmin-may-not-bulk-create-users-with-keypairs"

    @override
    def describe(self) -> str:
        return "권한 받은 사용자가 이 일괄 생성을 하려 하면, 전역 역할 문이 막는다"

    @override
    def given(self) -> Given[SeedingSession, ADomainAndACaller]:
        return SomeoneInADomain(granted=True)

    @override
    def when(self) -> When[ADomainAndACaller, UserAdapter, Any]:
        return BulkCreatingAUser(with_keypair=True)

    @override
    def then(self) -> Then[ADomainAndACaller, Any]:
        return TheCallIsRefused(InsufficientPrivilege)


SCENARIOS: list[Scenario[SeedingSession, Any, UserAdapter, Any]] = [
    AUserGrantedNothingMayNotCreateAUser(),
    ANameNoDomainHoldsMayNotHoldAUser(),
    OnlyTheSuperadminMayBulkCreate(),
    OnlyTheSuperadminMayBulkCreateWithKeypairs(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_creating(
    scenario: Scenario[SeedingSession, Any, UserAdapter, Any],
    adapter: UserAdapter,
    engine: ExtendedAsyncSAEngine,
) -> None:
    await run_scenario(scenario, adapter, engine)
