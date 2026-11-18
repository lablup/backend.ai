"""내가 가진 권한과, 역할 편집기에 보이는 권한 카탈로그."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override
from uuid import UUID

import pytest

from ai.backend.common.data.entity.session import SessionEntityType
from ai.backend.common.data.entity.user import UserEntityType
from ai.backend.common.data.permission.types import Permission
from ai.backend.common.dto.manager.v2.rbac.request import (
    MyAtomicBulkScopePermissionsInput,
    MyScopePermissionsInput,
    PermissionTarget,
)
from ai.backend.common.dto.manager.v2.rbac.response import (
    EntityOperationCombinationInfo,
    MyAtomicBulkScopePermissionsPayload,
    MyScopePermissionsPayload,
    ScopeEntityCombinationInfo,
    ScopeEntityOperationCombinationInfo,
)
from ai.backend.common.dto.manager.v2.rbac.types import PermissionBitDTO
from ai.backend.manager.api.adapters.rbac.adapter import RBACAdapter
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
    Then,
    Verdict,
    When,
)
from bai_scenario.components.answers import MissingResponse
from bai_scenario.components.domain import TheCallIsRefused
from bai_scenario.components.rbac import (
    RolesAndACaller,
    RolesAndSomeone,
    TheEntityOperations,
    ThePermissionMatrix,
    TheScopeEntities,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type HeldStep = Scenario[TestSeedingSession, RolesAndACaller, RBACAdapter, Any]

MY_SCOPE = Says("호출자의 id", english="the id of the caller")


@dataclass(frozen=True)
class AskingMyScopePermissions(When[RolesAndACaller, RBACAdapter, MyScopePermissionsPayload]):
    @override
    def operation(self) -> str:
        return "my_scope_permissions"

    @override
    def describe(self, laid: RolesAndACaller) -> str:
        return Says(
            f"{laid.caller.username}이 자기 스코프에서 역할에 대해 가진 권한을 묻습니다",
            english=(
                f"{laid.caller.username} asks what permissions they hold on roles in their own "
                "scope"
            ),
        )

    @override
    async def call(self, adapter: RBACAdapter, laid: RolesAndACaller) -> MyScopePermissionsPayload:
        with ActingAs(laid.caller):
            return await adapter.my_scope_permissions(
                MyScopePermissionsInput(
                    target=PermissionTarget(
                        scope_type=UserEntityType.name(),
                        scope_id=laid.caller.id,
                        entity_type="role",
                    )
                )
            )


@dataclass(frozen=True)
class AskingSeveralScopes(When[RolesAndACaller, RBACAdapter, MyAtomicBulkScopePermissionsPayload]):
    @override
    def operation(self) -> str:
        return "my_atomic_bulk_scope_permissions"

    @override
    def describe(self, laid: RolesAndACaller) -> str:
        return Says(
            f"{laid.caller.username}이 자기 스코프의 역할과 도메인 {laid.domain.name} 의 세션에 "
            "대해 가진 권한을 한 번에 묻습니다",
            english=(
                f"{laid.caller.username} asks in one call what permissions they hold on roles in "
                f"their own scope and on sessions in domain {laid.domain.name}"
            ),
        )

    @override
    async def call(
        self, adapter: RBACAdapter, laid: RolesAndACaller
    ) -> MyAtomicBulkScopePermissionsPayload:
        with ActingAs(laid.caller):
            return await adapter.my_atomic_bulk_scope_permissions(
                MyAtomicBulkScopePermissionsInput(
                    targets=[
                        PermissionTarget(
                            scope_type=UserEntityType.name(),
                            scope_id=laid.caller.id,
                            entity_type="role",
                        ),
                        PermissionTarget(
                            scope_type="domain",
                            scope_id=laid.domain.id,
                            entity_type=SessionEntityType.name(),
                        ),
                    ]
                )
            )


@dataclass(frozen=True)
class ReadingThePermissionMatrix(
    When[RolesAndACaller, RBACAdapter, list[ScopeEntityOperationCombinationInfo]]
):
    @override
    def operation(self) -> str:
        return "get_permission_matrix"

    @override
    def describe(self, laid: RolesAndACaller) -> str:
        return Says(
            f"{laid.caller.username}이 역할 편집기의 권한 표를 읽습니다",
            english=f"{laid.caller.username} reads the permission matrix of the role editor",
        )

    @override
    async def call(
        self, adapter: RBACAdapter, laid: RolesAndACaller
    ) -> list[ScopeEntityOperationCombinationInfo]:
        with ActingAs(laid.caller):
            return await adapter.get_permission_matrix()


@dataclass(frozen=True)
class ReadingTheEntityOperations(
    When[RolesAndACaller, RBACAdapter, list[EntityOperationCombinationInfo]]
):
    @override
    def operation(self) -> str:
        return "get_entity_operation_combinations"

    @override
    def describe(self, laid: RolesAndACaller) -> str:
        return Says(
            f"{laid.caller.username}이 역할이 허용할 수 있는 엔티티와 연산을 읽습니다",
            english=(f"{laid.caller.username} reads the entities and operations a role may permit"),
        )

    @override
    async def call(
        self, adapter: RBACAdapter, laid: RolesAndACaller
    ) -> list[EntityOperationCombinationInfo]:
        with ActingAs(laid.caller):
            return await adapter.get_entity_operation_combinations()


@dataclass(frozen=True)
class ReadingTheScopeEntities(When[RolesAndACaller, RBACAdapter, list[ScopeEntityCombinationInfo]]):
    @override
    def operation(self) -> str:
        return "get_scope_entity_combinations"

    @override
    def describe(self, laid: RolesAndACaller) -> str:
        return Says(
            f"{laid.caller.username}이 스코프마다 권한이 지목할 수 있는 엔티티를 읽습니다",
            english=(
                f"{laid.caller.username} reads the entities a permission may name in each scope"
            ),
        )

    @override
    async def call(
        self, adapter: RBACAdapter, laid: RolesAndACaller
    ) -> list[ScopeEntityCombinationInfo]:
        with ActingAs(laid.caller):
            return await adapter.get_scope_entity_combinations()


@dataclass(frozen=True)
class TheBitsIHold(Then[RolesAndACaller, MyScopePermissionsPayload]):
    """묻는 대상의 자리와, 호출자가 그 자리에서 가진 비트."""

    @override
    def says(self) -> str:
        return Says(
            "묻는 대상과 호출자가 가진 비트가 옵니다",
            english="the target asked about and the bits the caller holds come back",
        )

    @override
    def look(
        self, laid: RolesAndACaller, answered: Answered[MyScopePermissionsPayload]
    ) -> list[Verdict]:
        payload = answered.response
        if not isinstance(payload, MyScopePermissionsPayload):
            return [Refused(NotEnoughPermission, answered.raised)]
        item = payload.item
        return [
            Same("scope_type", item.scope_type, UserEntityType.name()),
            Held[UUID]("scope_id", item.scope_id, SameAs(laid.caller.id, MY_SCOPE)),
            Same("entity_type", item.entity_type, "role"),
            Same("permissions", item.permissions, [PermissionBitDTO.READ]),
        ]


@dataclass(frozen=True)
class TheBitsPerTarget(Then[RolesAndACaller, MyAtomicBulkScopePermissionsPayload]):
    """대상마다 자리와 호출자가 그 자리에서 가진 비트."""

    @override
    def says(self) -> str:
        return Says(
            "대상마다 자리와 호출자가 가진 비트가 옵니다",
            english="each target comes back with the bits the caller holds there",
        )

    @override
    def look(
        self, laid: RolesAndACaller, answered: Answered[MyAtomicBulkScopePermissionsPayload]
    ) -> list[Verdict]:
        payload = answered.response
        if not isinstance(payload, MyAtomicBulkScopePermissionsPayload):
            return [Refused(NotEnoughPermission, answered.raised)]
        verdicts: list[Verdict] = [Same("items count", len(payload.items), 2)]
        if len(payload.items) != 2:
            return verdicts
        first, second = payload.items
        verdicts += [
            Same("items[0].scope_type", first.scope_type, UserEntityType.name()),
            Held[UUID]("items[0].scope_id", first.scope_id, SameAs(laid.caller.id, MY_SCOPE)),
            Same("items[0].entity_type", first.entity_type, "role"),
            Same("items[0].permissions", first.permissions, [PermissionBitDTO.READ]),
            Same("items[1].scope_type", second.scope_type, "domain"),
            Held[UUID](
                "items[1].scope_id",
                second.scope_id,
                SameAs(
                    laid.domain.id,
                    Says(
                        "대상 도메인의 id",
                        english="the id of the target domain",
                    ),
                ),
            ),
            Same("items[1].entity_type", second.entity_type, "session"),
            Same("items[1].permissions", second.permissions, []),
        ]
        return verdicts


@dataclass(frozen=True)
class ThePermissionMatrixItself(Then[RolesAndACaller, list[ScopeEntityOperationCombinationInfo]]):
    @override
    def says(self) -> str:
        return Says(
            "배선된 스코프와 엔티티, 연산을 모두 실은 표가 옵니다",
            english="the table carrying every wired scope, entity and operation comes back",
        )

    @override
    def look(
        self, laid: RolesAndACaller, answered: Answered[list[ScopeEntityOperationCombinationInfo]]
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [MissingResponse(answered.raised)]
        return [Held("items", payload, ThePermissionMatrix())]


@dataclass(frozen=True)
class TheEntityOperationsItself(Then[RolesAndACaller, list[EntityOperationCombinationInfo]]):
    @override
    def says(self) -> str:
        return Says(
            "배선된 엔티티와 그 연산이 이름 순으로 옵니다",
            english="every wired entity with its operations comes back in name order",
        )

    @override
    def look(
        self, laid: RolesAndACaller, answered: Answered[list[EntityOperationCombinationInfo]]
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [MissingResponse(answered.raised)]
        return [Held("items", payload, TheEntityOperations())]


@dataclass(frozen=True)
class TheScopeEntitiesItself(Then[RolesAndACaller, list[ScopeEntityCombinationInfo]]):
    @override
    def says(self) -> str:
        return Says(
            "스코프마다 지목할 수 있는 엔티티가 이름 순으로 옵니다",
            english="every scope comes back with the entities it may name, in name order",
        )

    @override
    def look(
        self, laid: RolesAndACaller, answered: Answered[list[ScopeEntityCombinationInfo]]
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [MissingResponse(answered.raised)]
        return [Held("items", payload, TheScopeEntities())]


@dataclass(frozen=True)
class AUserHoldingARoleAsksItsScope(
    Scenario[TestSeedingSession, RolesAndACaller, RBACAdapter, MyScopePermissionsPayload]
):
    @override
    def summary(self) -> str:
        return "a-user-holding-a-role-asks-what-they-hold-in-their-own-scope"

    @override
    def describe(self) -> str:
        return Says(
            "자기 스코프의 역할 읽기 권한을 가진 역할을 가진 사용자가 자기 스코프에서 역할에 "
            "대해 가진 권한을 물으면, 그 비트가 옵니다",
            english=(
                "when a user holding a role with role read permission in their own scope asks "
                "what they hold on roles there, that bit comes back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, RolesAndACaller]:
        return RolesAndSomeone(self_grant=(Permission.READ,))

    @override
    def when(self) -> When[RolesAndACaller, RBACAdapter, MyScopePermissionsPayload]:
        return AskingMyScopePermissions()

    @override
    def then(self) -> Then[RolesAndACaller, MyScopePermissionsPayload]:
        return TheBitsIHold()


@dataclass(frozen=True)
class AUserGrantedNothingMayNotAskTheirScope(
    Scenario[TestSeedingSession, RolesAndACaller, RBACAdapter, MyScopePermissionsPayload]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-ask-what-they-hold"

    @override
    def describe(self) -> str:
        return Says(
            "아무 역할도 가진 것이 없는 사용자는 자기 스코프에서 가진 권한을 물을 수 없습니다",
            english=(
                "a user holding no role cannot ask what permissions they hold in their own scope"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, RolesAndACaller]:
        return RolesAndSomeone()

    @override
    def when(self) -> When[RolesAndACaller, RBACAdapter, MyScopePermissionsPayload]:
        return AskingMyScopePermissions()

    @override
    def then(self) -> Then[RolesAndACaller, MyScopePermissionsPayload]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class AUserHoldingARoleAsksSeveralScopes(
    Scenario[TestSeedingSession, RolesAndACaller, RBACAdapter, MyAtomicBulkScopePermissionsPayload]
):
    @override
    def summary(self) -> str:
        return "a-user-holding-a-role-asks-several-scopes-at-once"

    @override
    def describe(self) -> str:
        return Says(
            "자기 스코프의 역할 읽기 권한을 가진 역할을 가진 사용자가 자기 스코프의 역할과 대상 "
            "도메인의 세션에 대해 가진 권한을 한 번에 물으면, 자리마다 그 비트가 옵니다",
            english=(
                "when a user holding a role with role read permission in their own scope asks in "
                "one call about roles there and sessions in a target domain, the bits come back "
                "for each target"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, RolesAndACaller]:
        return RolesAndSomeone(self_grant=(Permission.READ,))

    @override
    def when(self) -> When[RolesAndACaller, RBACAdapter, MyAtomicBulkScopePermissionsPayload]:
        return AskingSeveralScopes()

    @override
    def then(self) -> Then[RolesAndACaller, MyAtomicBulkScopePermissionsPayload]:
        return TheBitsPerTarget()


@dataclass(frozen=True)
class AUserGrantedNothingMayNotAskSeveralScopes(
    Scenario[TestSeedingSession, RolesAndACaller, RBACAdapter, MyAtomicBulkScopePermissionsPayload]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-ask-several-scopes"

    @override
    def describe(self) -> str:
        return Says(
            "아무 역할도 가진 것이 없는 사용자는 자기 스코프에서 가진 권한을 한 번에 물을 수 "
            "없습니다",
            english=(
                "a user holding no role cannot ask in one call what permissions they hold in "
                "their own scope"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, RolesAndACaller]:
        return RolesAndSomeone()

    @override
    def when(self) -> When[RolesAndACaller, RBACAdapter, MyAtomicBulkScopePermissionsPayload]:
        return AskingSeveralScopes()

    @override
    def then(self) -> Then[RolesAndACaller, MyAtomicBulkScopePermissionsPayload]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class AnyUserReadsThePermissionMatrix(
    Scenario[
        TestSeedingSession, RolesAndACaller, RBACAdapter, list[ScopeEntityOperationCombinationInfo]
    ]
):
    @override
    def summary(self) -> str:
        return "any-user-reads-the-permission-matrix"

    @override
    def describe(self) -> str:
        return Says(
            "아무 역할도 가진 것이 없는 사용자도 역할 편집기의 권한 표를 읽을 수 있습니다",
            english=(
                "a user holding no role can still read the permission matrix of the role editor"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, RolesAndACaller]:
        return RolesAndSomeone()

    @override
    def when(self) -> When[RolesAndACaller, RBACAdapter, list[ScopeEntityOperationCombinationInfo]]:
        return ReadingThePermissionMatrix()

    @override
    def then(self) -> Then[RolesAndACaller, list[ScopeEntityOperationCombinationInfo]]:
        return ThePermissionMatrixItself()


@dataclass(frozen=True)
class AnyUserReadsTheEntityOperations(
    Scenario[TestSeedingSession, RolesAndACaller, RBACAdapter, list[EntityOperationCombinationInfo]]
):
    @override
    def summary(self) -> str:
        return "any-user-reads-the-entity-operation-combinations"

    @override
    def describe(self) -> str:
        return Says(
            "아무 역할도 가진 것이 없는 사용자도 역할이 허용할 수 있는 엔티티와 연산을 읽을 수 "
            "있습니다",
            english=(
                "a user holding no role can still read the entities and operations a role may "
                "permit"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, RolesAndACaller]:
        return RolesAndSomeone()

    @override
    def when(self) -> When[RolesAndACaller, RBACAdapter, list[EntityOperationCombinationInfo]]:
        return ReadingTheEntityOperations()

    @override
    def then(self) -> Then[RolesAndACaller, list[EntityOperationCombinationInfo]]:
        return TheEntityOperationsItself()


@dataclass(frozen=True)
class AnyUserReadsTheScopeEntities(
    Scenario[TestSeedingSession, RolesAndACaller, RBACAdapter, list[ScopeEntityCombinationInfo]]
):
    @override
    def summary(self) -> str:
        return "any-user-reads-the-scope-entity-combinations"

    @override
    def describe(self) -> str:
        return Says(
            "아무 역할도 가진 것이 없는 사용자도 스코프마다 권한이 지목할 수 있는 엔티티를 읽을 "
            "수 있습니다",
            english=(
                "a user holding no role can still read the entities a permission may name in each "
                "scope"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, RolesAndACaller]:
        return RolesAndSomeone()

    @override
    def when(self) -> When[RolesAndACaller, RBACAdapter, list[ScopeEntityCombinationInfo]]:
        return ReadingTheScopeEntities()

    @override
    def then(self) -> Then[RolesAndACaller, list[ScopeEntityCombinationInfo]]:
        return TheScopeEntitiesItself()


SCENARIOS: list[HeldStep] = [
    AUserHoldingARoleAsksItsScope(),
    AUserGrantedNothingMayNotAskTheirScope(),
    AUserHoldingARoleAsksSeveralScopes(),
    AUserGrantedNothingMayNotAskSeveralScopes(),
    AnyUserReadsThePermissionMatrix(),
    AnyUserReadsTheEntityOperations(),
    AnyUserReadsTheScopeEntities(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_held_permissions(
    scenario: HeldStep, adapter: RBACAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
