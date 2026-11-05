"""키페어 여럿을 한 번에 읽기와 access key 로 찾기 — 자리마다 무엇이 오는가."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, override
from uuid import uuid4

import pytest

from ai.backend.common.data.entity.keypair import KeyPairID
from ai.backend.common.dto.manager.v2.keypair import KeypairNode
from ai.backend.manager.api.adapters.user.adapter import UserAdapter
from ai.backend.manager.data.keypair.types import KeyPairData
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.data.user.types import UserData
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.errors.user import UserNotFound
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
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.domain import WAS_HERE, SomeoneOf
from bai_scenario.components.user import AGrant, KeypairNodeLook
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario
from bai_scenario.seeds.domain.domain import TestSeedDomain
from bai_scenario.seeds.resource_policy.keypair import TestSeedKeypairPolicy
from bai_scenario.seeds.user.fields import TestSeedKeypairOf

type Loaded = list[KeypairNode | Exception | None]
type Found = list[KeyPairID | None]
type Answer = Loaded | Found

NO_SUCH_KEY = "AKNOSUCHKEY"


@dataclass(frozen=True)
class ACallerAndAKey:
    """키를 가진 사람과, 그 키를 읽거나 찾을 사람."""

    caller: UserData
    target: UserData
    key: KeyPairData


@dataclass(frozen=True)
class SomeoneAndAKeyOwner(Given[Any, ACallerAndAKey]):
    """한 도메인의 사용자 둘. ``granted``면 호출자가 대상에 READ를 받는다."""

    granted: bool

    @override
    def describe(self) -> str:
        if self.granted:
            return Says(
                "도메인 하나와 사용자 둘, 대상은 기본이 아닌 키를 하나 더 갖고, "
                "호출자는 대상에 대한 사용자 읽기 권한을 받았습니다",
                english=(
                    "one domain and two users, the target holds one more keypair besides the "
                    "default one, and the caller holds the user read permission on the target"
                ),
            )
        return Says(
            "도메인 하나와 사용자 둘, 대상은 기본이 아닌 키를 하나 더 갖고, "
            "호출자는 아무 권한도 받지 않았습니다",
            english=(
                "one domain and two users, the target holds one more keypair besides the "
                "default one, and the caller holds no permission"
            ),
        )

    @override
    async def lay(self, seeding: Any) -> ACallerAndAKey:
        domain = await seeding.creating(TestSeedDomain(name_hint="home", description=WAS_HERE))
        target = await seeding.within(SomeoneOf(domain))
        policy = await seeding.creating(TestSeedKeypairPolicy())
        key = await seeding.adding(
            TestSeedKeypairOf(resource_policy=seeding.made(policy).name), target
        )
        caller = await seeding.within(SomeoneOf(domain))
        if self.granted:
            await seeding.within(AGrant.on_user(target, caller, Permission.READ))
        return ACallerAndAKey(seeding.made(caller), seeding.made(target), seeding.made(key))


@dataclass(frozen=True)
class LoadingTheKeyAndMissing(When[ACallerAndAKey, UserAdapter, Answer]):
    """키와 없는 id를 한 번에 읽는다."""

    @override
    def operation(self) -> str:
        return "bulk_get_keypair_ids"

    @override
    def describe(self, laid: ACallerAndAKey) -> str:
        return Says(
            f"{laid.caller.username}이 {laid.target.username}의 키와 없는 id 를 일괄 읽습니다",
            english=(
                f"{laid.caller.username} batch reads the key of {laid.target.username} and a "
                "missing id"
            ),
        )

    @override
    async def call(self, adapter: UserAdapter, laid: ACallerAndAKey) -> Answer:
        with ActingAs(laid.caller):
            return await adapter.bulk_get_keypair_ids([
                KeyPairID(laid.key.id),
                KeyPairID(uuid4()),
            ])


@dataclass(frozen=True)
class LookingUpTheKeyAndMissing(When[ACallerAndAKey, UserAdapter, Answer]):
    """access key 둘을 한 번에 찾는다. 둘째는 어떤 키도 아닌 값이다."""

    @override
    def operation(self) -> str:
        return "bulk_lookup_keypair_access_keys"

    @override
    def describe(self, laid: ACallerAndAKey) -> str:
        return Says(
            f"{laid.caller.username}이 {laid.target.username}의 access key 와 없는 access key 로 "
            "키를 찾습니다",
            english=(
                f"{laid.caller.username} looks up the access key of {laid.target.username} and "
                "an access key nobody holds"
            ),
        )

    @override
    async def call(self, adapter: UserAdapter, laid: ACallerAndAKey) -> Answer:
        with ActingAs(laid.caller):
            return await adapter.bulk_lookup_keypair_access_keys([
                str(laid.key.access_key),
                NO_SUCH_KEY,
            ])


@dataclass(frozen=True)
class LookingUpWithoutLogin(When[ACallerAndAKey, UserAdapter, Answer]):
    """로그인 문맥 없이 access key 로 찾는다."""

    @override
    def operation(self) -> str:
        return "bulk_lookup_keypair_access_keys"

    @override
    def describe(self, laid: ACallerAndAKey) -> str:
        return Says(
            "로그인 문맥 없이 access key 로 키를 찾습니다",
            english="without a login context, looks up an access key",
        )

    @override
    async def call(self, adapter: UserAdapter, laid: ACallerAndAKey) -> Answer:
        return await adapter.bulk_lookup_keypair_access_keys([str(laid.key.access_key)])


@dataclass(frozen=True)
class TheKeyThenAGap(Then[ACallerAndAKey, Answer]):
    """읽은 키는 노드로, 없는 id 자리는 빈 값으로 온다."""

    started: datetime

    @override
    def says(self) -> str:
        return Says(
            "읽은 키는 노드로, 없는 id 자리는 빈 값으로 옵니다",
            english="the key read comes back as a node and the missing id as an empty value",
        )

    @override
    def look(self, laid: ACallerAndAKey, answered: Answered[Answer]) -> list[Verdict]:
        loaded = answered.response
        if not isinstance(loaded, list):
            return [Refused(NotEnoughPermission, answered.raised)]
        first, second = loaded
        seen: list[Verdict] = [Same("length", len(loaded), 2)]
        if isinstance(first, KeypairNode):
            seen.extend(KeypairNodeLook(self.started).verdicts(first, laid.key, laid.target))
            seen.append(
                Held(
                    "field_id",
                    first.field_id,
                    SameAs(
                        laid.key.id,
                        Says("미리 저장한 키페어", english="the keypair seeded in advance"),
                    ),
                )
            )
        else:
            seen.append(Same("[0]", type(first).__name__, "KeypairNode"))
        seen.append(Same("[1]", second, None))
        return seen


@dataclass(frozen=True)
class ARejectionForTheKeyAndAGap(Then[ACallerAndAKey, Answer]):
    """읽을 수 없는 키는 거부되고, 없는 id 자리는 빈 값으로 온다."""

    @override
    def says(self) -> str:
        return Says(
            "읽을 수 없는 키는 권한 부족으로 거부되고, 없는 id 자리는 빈 값으로 옵니다",
            english=(
                "the unreadable key is rejected for lack of permission and the missing id "
                "comes back empty"
            ),
        )

    @override
    def look(self, laid: ACallerAndAKey, answered: Answered[Answer]) -> list[Verdict]:
        loaded = answered.response
        if not isinstance(loaded, list):
            return [Refused(NotEnoughPermission, answered.raised)]
        first, second = loaded
        return [
            Same("length", len(loaded), 2),
            Refused(NotEnoughPermission, first if isinstance(first, Exception) else None),
            Same("[1]", second, None),
        ]


@dataclass(frozen=True)
class TheKeyIdThenAGap(Then[ACallerAndAKey, Answer]):
    """찾은 키의 id는 그 키의 것으로, 없는 access key 자리는 빈 값으로 온다."""

    @override
    def says(self) -> str:
        return Says(
            "찾은 키의 id 는 그 키의 것이고, 없는 access key 자리는 비어 있습니다",
            english="the key found comes back as its id and the access key nobody holds is empty",
        )

    @override
    def look(self, laid: ACallerAndAKey, answered: Answered[Answer]) -> list[Verdict]:
        found = answered.response
        if not isinstance(found, list):
            return [Same("raised", type(answered.raised).__name__, None)]
        first, second = found
        return [
            Same("length", len(found), 2),
            Held[object](
                "[0]",
                first,
                SameAs(
                    laid.key.id,
                    Says("미리 저장한 키페어", english="the keypair seeded in advance"),
                ),
            ),
            Same("[1]", second, None),
        ]


@dataclass(frozen=True)
class AGrantedCallerLoadsTheKey(Scenario[TestSeedingSession, ACallerAndAKey, UserAdapter, Answer]):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-user-granted-read-on-another-loads-their-key-by-id"

    @override
    def describe(self) -> str:
        return Says(
            "대상 사용자 스코프에서 사용자 읽기 권한을 받은 사용자가 그 사용자의 키와 없는 id 를 "
            "한 번에 읽으면, 키 전체와 빈 값이 차례로 옵니다",
            english=(
                "when a user granted the user read permission in the target user scope reads "
                "that user's key and a missing id at once, the whole key and an empty value "
                "come back in that order"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ACallerAndAKey]:
        return SomeoneAndAKeyOwner(granted=True)

    @override
    def when(self) -> When[ACallerAndAKey, UserAdapter, Answer]:
        return LoadingTheKeyAndMissing()

    @override
    def then(self) -> Then[ACallerAndAKey, Answer]:
        return TheKeyThenAGap(started=self.started)


@dataclass(frozen=True)
class AUserGrantedNothingGetsARejectionForTheKey(
    Scenario[TestSeedingSession, ACallerAndAKey, UserAdapter, Answer]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-gets-a-rejection-for-anothers-key"

    @override
    def describe(self) -> str:
        return Says(
            "권한을 받지 않은 사용자가 다른 사용자의 키와 없는 id 를 한 번에 읽으면, 그 키 항목은 "
            "권한 부족으로 거부되고 없는 id 자리는 빈 값으로 옵니다",
            english=(
                "when a user holding no permission reads another user's key and a missing id "
                "at once, that key entry is rejected for lack of permission and the missing "
                "id entry is empty"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ACallerAndAKey]:
        return SomeoneAndAKeyOwner(granted=False)

    @override
    def when(self) -> When[ACallerAndAKey, UserAdapter, Answer]:
        return LoadingTheKeyAndMissing()

    @override
    def then(self) -> Then[ACallerAndAKey, Answer]:
        return ARejectionForTheKeyAndAGap()


@dataclass(frozen=True)
class AUserLooksUpTheAccessKey(Scenario[TestSeedingSession, ACallerAndAKey, UserAdapter, Answer]):
    @override
    def summary(self) -> str:
        return "a-user-looks-up-the-keypair-an-access-key-names"

    @override
    def describe(self) -> str:
        return Says(
            "사용자가 access key 와 어떤 키도 아닌 access key 를 한 번에 찾으면, 첫째는 그 키의 "
            "id 로, 둘째는 빈 값으로 옵니다",
            english=(
                "when a user looks up an access key and an access key nobody holds at once, "
                "the first comes back as that keypair's id and the second as an empty value"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ACallerAndAKey]:
        return SomeoneAndAKeyOwner(granted=False)

    @override
    def when(self) -> When[ACallerAndAKey, UserAdapter, Answer]:
        return LookingUpTheKeyAndMissing()

    @override
    def then(self) -> Then[ACallerAndAKey, Answer]:
        return TheKeyIdThenAGap()


@dataclass(frozen=True)
class ACallWithoutLoginIsRefused(Scenario[TestSeedingSession, ACallerAndAKey, UserAdapter, Answer]):
    @override
    def summary(self) -> str:
        return "looking-up-an-access-key-without-login-is-refused"

    @override
    def describe(self) -> str:
        return Says(
            "로그인 문맥 없이 access key 로 키를 찾으면, 사용자를 찾을 수 없다는 것으로 거부됩니다",
            english=(
                "looking up a key by an access key without a login context is rejected as "
                "user not found"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ACallerAndAKey]:
        return SomeoneAndAKeyOwner(granted=False)

    @override
    def when(self) -> When[ACallerAndAKey, UserAdapter, Answer]:
        return LookingUpWithoutLogin()

    @override
    def then(self) -> Then[ACallerAndAKey, Answer]:
        return TheCallIsRefused(UserNotFound)


SCENARIOS: list[Scenario[TestSeedingSession, ACallerAndAKey, UserAdapter, Answer]] = [
    AGrantedCallerLoadsTheKey(started=datetime.now(UTC)),
    AUserGrantedNothingGetsARejectionForTheKey(),
    AUserLooksUpTheAccessKey(),
    ACallWithoutLoginIsRefused(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_loading_keypairs(
    scenario: Scenario[TestSeedingSession, ACallerAndAKey, UserAdapter, Answer],
    adapter: UserAdapter,
    engine: ExtendedAsyncSAEngine,
) -> None:
    await run_scenario(scenario, adapter, engine)
