"""자기 키페어 — 발급하고, 끄고, 기본으로 옮기고, 회수하고, 훑기."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from itertools import pairwise
from typing import Any, override
from uuid import UUID

import pytest

from ai.backend.common.data.entity.user import UserID
from ai.backend.common.dto.manager.v2.keypair import (
    KeypairFilter,
    KeypairNode,
    SearchMyKeypairsRequest,
)
from ai.backend.common.dto.manager.v2.keypair.response import IssueMyKeypairPayload
from ai.backend.common.dto.manager.v2.user.response import UserNode
from ai.backend.common.types import AccessKey
from ai.backend.manager.api.adapters.user.adapter import UserAdapter
from ai.backend.manager.data.common.types import SearchResult
from ai.backend.manager.data.keypair.types import KeyPairData
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.data.resource.types import KeyPairResourcePolicyData
from ai.backend.manager.data.user.types import UserData
from ai.backend.manager.errors.common import GenericBadRequest
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.errors.user import KeyPairForbidden
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
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
    Told,
    Verdict,
    When,
    in_language,
)
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.domain import WAS_HERE, WrittenByThisRun
from bai_scenario.components.user import AGrant, KeypairNodeLook, UserNodeLook
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario
from bai_scenario.seeds.domain.domain import TestSeedDomain
from bai_scenario.seeds.resource_policy.keypair import TestSeedKeypairPolicy
from bai_scenario.seeds.resource_policy.project import TestSeedProjectPolicy
from bai_scenario.seeds.resource_policy.user import TestSeedUserPolicy
from bai_scenario.seeds.seeder import Laid, TestSeeder, TestSeedNest
from bai_scenario.seeds.user.fields import TestSeedKeypairOf
from bai_scenario.seeds.user.user import TestSeedUserOf

SERVER_RATE_LIMIT = 10000
"""키 행의 요청 한도 기본값. 시드는 한도를 적지 않으므로 컬럼 기본값이 들어간다."""

NO_SUCH_KEY = "AKNOSUCHKEY000000000"
"""어떤 키도 아닌 access key. 요청에만 쓰고 어느 행과도 잇지 않는다."""

type Keys = SearchResult[KeypairNode]


@dataclass(frozen=True)
class Keyholder:
    """자기 키를 다룰 사람, 그 사람의 키 정책, 더 가진 키, 그리고 다른 사람과 그 키."""

    caller: UserData
    key_policy: str
    extra: tuple[KeyPairData, ...]
    other_key: KeyPairData | None


@dataclass(frozen=True)
class Revoked:
    """회수 답과, 뒤이어 훑은 자기 키."""

    success: bool
    after: Keys


@dataclass(frozen=True)
class Switched:
    """기본 키 전환 답과, 뒤이어 읽은 자기 사용자."""

    success: bool
    node: UserNode


@dataclass(frozen=True)
class Chained:
    """발급, 전환, 회수를 차례로 부른 답과 뒤이어 훑은 자기 키."""

    issued: IssueMyKeypairPayload
    switched: bool
    revoked: bool
    after: Keys


type Answer = object


@dataclass(frozen=True)
class SomeoneAndTheirKeyPolicy(
    TestSeedNest[tuple[Laid[KeyPairResourcePolicyData], Laid[UserData]]]
):
    """그 도메인의 사용자 한 명과, 그 사람 기본 키가 딛는 키 정책."""

    domain: Laid[Any]

    @override
    def kind(self) -> str:
        return Says(
            "키 정책을 아는 사용자 한 명 준비",
            english="Prepare one user whose key policy is known",
        )

    @override
    def lay(self, seed: TestSeeder) -> tuple[Laid[KeyPairResourcePolicyData], Laid[UserData]]:
        seed.once(TestSeedProjectPolicy())
        policy = seed.creating(TestSeedUserPolicy())
        key_policy = seed.creating(TestSeedKeypairPolicy())
        user = seed.provisioning(TestSeedUserOf(), self.domain, policy, key_policy)
        return key_policy, user


@dataclass(frozen=True)
class SomeoneWithKeys(Given[Any, Keyholder]):
    """자기 키를 다룰 사용자 한 명. 권한, 더 가진 키 수, 다른 사람의 키 유무를 고른다."""

    permissions: Sequence[Permission] = ()
    extra_keys: int = 0
    other_holds_a_key: bool = False

    @override
    def describe(self) -> str:
        if self.permissions:
            names = ", ".join(str(p.name) for p in self.permissions)
            granted = Says(
                f"자기 사용자에 {names} 권한을 받았습니다",
                english=f"the user holds the {names} permission on their own user",
            )
        else:
            granted = Says(
                "아무 권한도 받지 않았습니다",
                english="the user holds no permission",
            )
        others_ko = ", 기본 아닌 키를 가진 다른 사용자 한 명" if self.other_holds_a_key else ""
        others_en = (
            ", one other user holding an extra key that is not the default"
            if self.other_holds_a_key
            else ""
        )
        return Says(
            f"도메인 하나와 기본 아닌 키 {self.extra_keys}개를 가진 사용자 한 명{others_ko}, "
            f"그 사용자는 {granted}",
            english=(
                f"one domain and one user holding {self.extra_keys} extra keys that are not "
                f"the default{others_en}, and {in_language(granted, Language.ENGLISH)}"
            ),
        )

    @override
    async def lay(self, seeding: Any) -> Keyholder:
        domain = await seeding.creating(TestSeedDomain(name_hint="home", description=WAS_HERE))
        key_policy, caller = await seeding.within(SomeoneAndTheirKeyPolicy(domain))
        policy_name = seeding.made(key_policy).name
        extra = [
            await seeding.adding(TestSeedKeypairOf(resource_policy=policy_name), caller)
            for _ in range(self.extra_keys)
        ]
        other_key = None
        if self.other_holds_a_key:
            _, other = await seeding.within(SomeoneAndTheirKeyPolicy(domain))
            other_key = await seeding.adding(TestSeedKeypairOf(resource_policy=policy_name), other)
        if self.permissions:
            await seeding.within(AGrant.on_user(caller, caller, *self.permissions))
        return Keyholder(
            caller=seeding.made(caller),
            key_policy=policy_name,
            extra=tuple(seeding.made(one) for one in extra),
            other_key=seeding.made(other_key) if other_key is not None else None,
        )


async def _my_default_key(adapter: UserAdapter) -> str:
    found = await adapter.search_my_keypairs(
        SearchMyKeypairsRequest(filter=KeypairFilter(is_default=True))
    )
    return found.items[0].access_key


@dataclass(frozen=True)
class Issuing(When[Keyholder, UserAdapter, Answer]):
    @override
    def operation(self) -> str:
        return "issue_my_keypair"

    @override
    def describe(self, laid: Keyholder) -> str:
        return Says(
            f"{laid.caller.username}이 자기 키를 발급합니다",
            english=f"{laid.caller.username} issues their own key",
        )

    @override
    async def call(self, adapter: UserAdapter, laid: Keyholder) -> Answer:
        with ActingAs(laid.caller):
            return await adapter.issue_my_keypair(laid.caller.id)


@dataclass(frozen=True)
class RevokingTheExtraKey(When[Keyholder, UserAdapter, Answer]):
    @override
    def operation(self) -> str:
        return "revoke_my_keypair"

    @override
    def describe(self, laid: Keyholder) -> str:
        return Says(
            f"{laid.caller.username}이 기본 아닌 자기 키를 회수하고 자기 키를 다시 조회합니다",
            english=(
                f"{laid.caller.username} revokes their own extra key and searches their own "
                "keys again"
            ),
        )

    @override
    async def call(self, adapter: UserAdapter, laid: Keyholder) -> Answer:
        with ActingAs(laid.caller):
            payload = await adapter.revoke_my_keypair(str(laid.extra[0].access_key))
            after = await adapter.search_my_keypairs(SearchMyKeypairsRequest())
        return Revoked(payload.success, after)


@dataclass(frozen=True)
class RevokingTheDefaultKey(When[Keyholder, UserAdapter, Answer]):
    @override
    def operation(self) -> str:
        return "revoke_my_keypair"

    @override
    def describe(self, laid: Keyholder) -> str:
        return Says(
            f"{laid.caller.username}이 자기 키 검색으로 기본 키를 찾아 그 키를 회수합니다",
            english=(
                f"{laid.caller.username} finds the default key through their own key search "
                "and revokes it"
            ),
        )

    @override
    async def call(self, adapter: UserAdapter, laid: Keyholder) -> Answer:
        with ActingAs(laid.caller):
            return await adapter.revoke_my_keypair(await _my_default_key(adapter))


@dataclass(frozen=True)
class RevokingAKeyNobodyHolds(When[Keyholder, UserAdapter, Answer]):
    @override
    def operation(self) -> str:
        return "revoke_my_keypair"

    @override
    def describe(self, laid: Keyholder) -> str:
        return Says(
            f"{laid.caller.username}이 어떤 키도 아닌 값으로 회수합니다",
            english=f"{laid.caller.username} revokes with an access key nobody holds",
        )

    @override
    async def call(self, adapter: UserAdapter, laid: Keyholder) -> Answer:
        with ActingAs(laid.caller):
            return await adapter.revoke_my_keypair(NO_SUCH_KEY)


@dataclass(frozen=True)
class TurningOffTheExtraKey(When[Keyholder, UserAdapter, Answer]):
    @override
    def operation(self) -> str:
        return "update_my_keypair"

    @override
    def describe(self, laid: Keyholder) -> str:
        return Says(
            f"{laid.caller.username}이 기본 아닌 자기 키를 비활성으로 변경합니다",
            english=f"{laid.caller.username} turns their own extra key inactive",
        )

    @override
    async def call(self, adapter: UserAdapter, laid: Keyholder) -> Answer:
        with ActingAs(laid.caller):
            payload = await adapter.update_my_keypair(str(laid.extra[0].access_key), False)
        return payload.keypair


@dataclass(frozen=True)
class TurningOffTheDefaultKey(When[Keyholder, UserAdapter, Answer]):
    @override
    def operation(self) -> str:
        return "update_my_keypair"

    @override
    def describe(self, laid: Keyholder) -> str:
        return Says(
            f"{laid.caller.username}이 자기 키 검색으로 기본 키를 찾아 비활성으로 변경합니다",
            english=(
                f"{laid.caller.username} finds the default key through their own key search "
                "and turns it inactive"
            ),
        )

    @override
    async def call(self, adapter: UserAdapter, laid: Keyholder) -> Answer:
        with ActingAs(laid.caller):
            return await adapter.update_my_keypair(await _my_default_key(adapter), False)


@dataclass(frozen=True)
class SwitchingToTheExtraKey(When[Keyholder, UserAdapter, Answer]):
    @override
    def operation(self) -> str:
        return "switch_default_access_key"

    @override
    def describe(self, laid: Keyholder) -> str:
        return Says(
            f"{laid.caller.username}이 기본 아닌 자기 키로 기본 키를 옮기고 자기 사용자를 "
            "다시 읽습니다",
            english=(
                f"{laid.caller.username} moves the default key to their own extra key and "
                "reads their own user again"
            ),
        )

    @override
    async def call(self, adapter: UserAdapter, laid: Keyholder) -> Answer:
        with ActingAs(laid.caller):
            payload = await adapter.switch_default_access_key(
                UserID(laid.caller.id), laid.extra[0].access_key
            )
            node = await adapter.get(laid.caller.id)
        return Switched(payload.success, node.user)


@dataclass(frozen=True)
class SwitchingToAnExtraKeyWithoutRereading(When[Keyholder, UserAdapter, Answer]):
    @override
    def operation(self) -> str:
        return "switch_default_access_key"

    @override
    def describe(self, laid: Keyholder) -> str:
        return Says(
            f"{laid.caller.username}이 기본 아닌 자기 키로 기본 키를 옮깁니다",
            english=f"{laid.caller.username} moves the default key to their own extra key",
        )

    @override
    async def call(self, adapter: UserAdapter, laid: Keyholder) -> Answer:
        with ActingAs(laid.caller):
            return await adapter.switch_default_access_key(
                UserID(laid.caller.id), laid.extra[0].access_key
            )


@dataclass(frozen=True)
class SwitchingToSomeoneElsesKey(When[Keyholder, UserAdapter, Answer]):
    @override
    def operation(self) -> str:
        return "switch_default_access_key"

    @override
    def describe(self, laid: Keyholder) -> str:
        return Says(
            f"{laid.caller.username}이 다른 사용자의 키로 기본 키를 옮깁니다",
            english=f"{laid.caller.username} moves the default key to another user's key",
        )

    @override
    async def call(self, adapter: UserAdapter, laid: Keyholder) -> Answer:
        assert laid.other_key is not None
        with ActingAs(laid.caller):
            return await adapter.switch_default_access_key(
                UserID(laid.caller.id), AccessKey(laid.other_key.access_key)
            )


@dataclass(frozen=True)
class SearchingMyKeys(When[Keyholder, UserAdapter, Answer]):
    @override
    def operation(self) -> str:
        return "search_my_keypairs"

    @override
    def describe(self, laid: Keyholder) -> str:
        return Says(
            f"{laid.caller.username}이 페이지 인자 없이 자기 키를 조회합니다",
            english=f"{laid.caller.username} searches their own keys without page arguments",
        )

    @override
    async def call(self, adapter: UserAdapter, laid: Keyholder) -> Answer:
        with ActingAs(laid.caller):
            return await adapter.search_my_keypairs(SearchMyKeypairsRequest())


@dataclass(frozen=True)
class IssuingThenSwitchingThenRevoking(When[Keyholder, UserAdapter, Answer]):
    @override
    def operation(self) -> str:
        return "issue_my_keypair"

    @override
    def describe(self, laid: Keyholder) -> str:
        return Says(
            f"{laid.caller.username}이 자기 키 검색으로 기본 키를 찾고, 키를 발급해 그 키로 "
            "기본 키를 옮긴 다음 원래 기본 키를 회수하고 자기 키를 다시 조회합니다",
            english=(
                f"{laid.caller.username} finds the default key through their own key search, "
                "issues a key, moves the default key to it, revokes the original default key, "
                "and searches their own keys again"
            ),
        )

    @override
    async def call(self, adapter: UserAdapter, laid: Keyholder) -> Answer:
        with ActingAs(laid.caller):
            original = await _my_default_key(adapter)
            issued = await adapter.issue_my_keypair(laid.caller.id)
            switched = await adapter.switch_default_access_key(
                UserID(laid.caller.id), AccessKey(issued.keypair.access_key)
            )
            revoked = await adapter.revoke_my_keypair(original)
            after = await adapter.search_my_keypairs(SearchMyKeypairsRequest())
        return Chained(issued, switched.success, revoked.success, after)


@dataclass(frozen=True)
class At(Verdict):
    """목록 원소 하나를 본 것. 자리 이름 앞에 원소 자리를 붙인다."""

    prefix: str
    inner: Verdict

    @override
    def told(self) -> Told:
        told = self.inner.told()
        return Told(
            Says(
                f"{self.prefix}{told.says}",
                english=f"{self.prefix}{in_language(told.says, Language.ENGLISH)}",
            ),
            problems=tuple(f"{self.prefix}{one}" for one in told.problems),
        )


def _at(prefix: str, verdicts: Sequence[Verdict]) -> list[Verdict]:
    return [At(prefix, one) for one in verdicts]


def _default_key(started: datetime, node: KeypairNode, laid: Keyholder) -> list[Verdict]:
    written = WrittenByThisRun(started)
    random_key = Says(
        "시드가 매번 새로 만든 access key 입니다",
        english="it is an access key the seed makes anew every time",
    )
    return [
        Skipped("id", random_key),
        Skipped("access_key", random_key),
        Same("is_active", node.is_active, True),
        Same("is_admin", node.is_admin, False),
        Same("is_default", node.is_default, True),
        Same("rate_limit", node.rate_limit, SERVER_RATE_LIMIT),
        Same("resource_policy", node.resource_policy, laid.key_policy),
        Same("num_queries", node.num_queries, 0),
        Same("last_used", node.last_used, None),
        Held(
            "user_id",
            node.user_id,
            SameAs(laid.caller.id, Says("키 소유자", english="the key owner")),
        ),
        Held("created_at", node.created_at, written),
        Held("modified_at", node.modified_at, written),
    ]


def _extra_key(key: KeyPairData, *, is_active: bool = True) -> KeyPairData:
    return replace(key, is_active=is_active, is_default=False, rate_limit=SERVER_RATE_LIMIT)


@dataclass(frozen=True)
class TheIssuedKey(Then[Keyholder, Answer]):
    started: datetime

    @override
    def says(self) -> str:
        return Says(
            "기본 키를 따르는 기본 아닌 새 키와 secret 이 응답으로 옵니다",
            english=(
                "a new key that is not the default, following the default key, and its "
                "secret come back"
            ),
        )

    @override
    def look(self, laid: Keyholder, answered: Answered[Answer]) -> list[Verdict]:
        payload = answered.response
        if not isinstance(payload, IssueMyKeypairPayload):
            return [Refused(NotEnoughPermission, answered.raised)]
        return [
            *KeypairNodeLook(self.started).generated(
                payload.keypair,
                laid.caller,
                is_active=True,
                is_admin=False,
                is_default=False,
                rate_limit=SERVER_RATE_LIMIT,
                resource_policy=laid.key_policy,
            ),
            Skipped(
                "secret_key",
                Says(
                    "매니저가 매번 새로 생성합니다",
                    english="the manager makes it anew every time",
                ),
            ),
        ]


@dataclass(frozen=True)
class OnlyTheDefaultKeyIsLeft(Then[Keyholder, Answer]):
    started: datetime

    @override
    def says(self) -> str:
        return Says(
            "회수에 성공하고, 뒤이은 자기 키 검색에 기본 키만 남습니다",
            english=(
                "the revoke succeeds and only the default key is left in the own key search "
                "that follows"
            ),
        )

    @override
    def look(self, laid: Keyholder, answered: Answered[Answer]) -> list[Verdict]:
        result = answered.response
        if not isinstance(result, Revoked):
            return [Refused(NotEnoughPermission, answered.raised)]
        after = result.after
        seen: list[Verdict] = [
            Same("success", result.success, True),
            Same("after.total_count", after.total_count, 1),
            Same("after.has_next_page", after.has_next_page, False),
            Same("after.has_previous_page", after.has_previous_page, False),
            Same("after.items.length", len(after.items), 1),
        ]
        if after.items:
            seen.extend(_at("after.items[0].", _default_key(self.started, after.items[0], laid)))
        return seen


@dataclass(frozen=True)
class TheKeyIsOff(Then[Keyholder, Answer]):
    started: datetime

    @override
    def says(self) -> str:
        return Says(
            "활성만 변경된 키 노드 전체가 응답으로 옵니다",
            english="the whole key node with only the active flag changed comes back",
        )

    @override
    def look(self, laid: Keyholder, answered: Answered[Answer]) -> list[Verdict]:
        node = answered.response
        if not isinstance(node, KeypairNode):
            return [Refused(NotEnoughPermission, answered.raised)]
        return KeypairNodeLook(self.started).verdicts(
            node, _extra_key(laid.extra[0], is_active=False), laid.caller
        )


@dataclass(frozen=True)
class TheDefaultKeyMoved(Then[Keyholder, Answer]):
    started: datetime

    @override
    def says(self) -> str:
        return Says(
            "전환에 성공하고, 뒤이은 읽기에서 기본 키가 추가한 키입니다",
            english=(
                "the switch succeeds and the default key in the read that follows is the extra key"
            ),
        )

    @override
    def look(self, laid: Keyholder, answered: Answered[Answer]) -> list[Verdict]:
        result = answered.response
        if not isinstance(result, Switched):
            return [Refused(NotEnoughPermission, answered.raised)]
        return [
            Same("success", result.success, True),
            *_at(
                "node.",
                UserNodeLook(self.started).verdicts(
                    result.node,
                    laid.caller,
                    main_access_key=SameAs(
                        str(laid.extra[0].access_key),
                        Says("추가한 키", english="the extra key"),
                    ),
                ),
            ),
        ]


@dataclass(frozen=True)
class OnlyMyTwoKeys(Then[Keyholder, Answer]):
    started: datetime

    @override
    def says(self) -> str:
        return Says(
            "자기 키 둘만 옵니다",
            english="only their own two keys come back",
        )

    @override
    def look(self, laid: Keyholder, answered: Answered[Answer]) -> list[Verdict]:
        page = answered.response
        if not isinstance(page, SearchResult):
            return [Refused(NotEnoughPermission, answered.raised)]
        items: list[KeypairNode] = sorted(page.items, key=lambda one: one.is_default)
        seen: list[Verdict] = [
            Same("total_count", page.total_count, 2),
            Same("has_next_page", page.has_next_page, False),
            Same("has_previous_page", page.has_previous_page, False),
            Same(
                "items.is_default(extra key first)",
                [one.is_default for one in items],
                [False, True],
            ),
        ]
        if len(items) == 2:
            seen.extend(
                _at(
                    "items[the extra key].",
                    KeypairNodeLook(self.started).verdicts(
                        items[0], _extra_key(laid.extra[0]), laid.caller
                    ),
                )
            )
            seen.extend(_at("items[the default key].", _default_key(self.started, items[1], laid)))
        return seen


@dataclass(frozen=True)
class NewestFirst(Condition[list[tuple[datetime, UUID]]]):
    """생성 시각 내림차순, 같은 시각이면 field id 오름차순."""

    @override
    def says(self) -> str:
        return Says(
            "생성 시각 내림차순, 같은 시각이면 field id 오름차순입니다",
            english="descending creation time, then ascending field id for the same time",
        )

    @override
    def holds(self, got: list[tuple[datetime, UUID]]) -> bool:
        return all(a[0] > b[0] or (a[0] == b[0] and a[1] < b[1]) for a, b in pairwise(got))


@dataclass(frozen=True)
class TheFirstTenOfEleven(Then[Keyholder, Answer]):
    started: datetime

    @override
    def says(self) -> str:
        return Says(
            "자기 키 열한 개 중 열 개가 최근순으로 오고 다음 페이지가 있습니다",
            english=("ten of their eleven keys come back newest first and there is a next page"),
        )

    @override
    def look(self, laid: Keyholder, answered: Answered[Answer]) -> list[Verdict]:
        page = answered.response
        if not isinstance(page, SearchResult):
            return [Refused(NotEnoughPermission, answered.raised)]
        items: list[KeypairNode] = list(page.items)
        return [
            Same("total_count", page.total_count, 11),
            Same("has_next_page", page.has_next_page, True),
            Same("has_previous_page", page.has_previous_page, False),
            Same("items.length", len(items), 10),
            Held(
                "items(created_at, field_id)",
                [(one.created_at, one.field_id) for one in items if one.created_at is not None],
                NewestFirst(),
            ),
            Held(
                "items.user_id",
                [one.user_id for one in items],
                SameAs(
                    [laid.caller.id] * len(items), Says("모두 부른 사람", english="all the caller")
                ),
            ),
            Held(
                "items.created_at",
                min((one.created_at for one in items if one.created_at), default=None),
                WrittenByThisRun(self.started),
            ),
            Skipped(
                "the remaining item fields",
                Says(
                    "순서와 개수를 보는 행입니다. 키 노드 전체는 다른 행이 봅니다",
                    english=(
                        "this row looks at order and count; another row looks at the whole key node"
                    ),
                ),
            ),
        ]


@dataclass(frozen=True)
class OnlyTheIssuedKeyIsLeft(Then[Keyholder, Answer]):
    started: datetime

    @override
    def says(self) -> str:
        return Says(
            "세 호출이 통과하고 발급한 키 하나만 남습니다",
            english="all three calls pass and only the issued key is left",
        )

    @override
    def look(self, laid: Keyholder, answered: Answered[Answer]) -> list[Verdict]:
        chain = answered.response
        if not isinstance(chain, Chained):
            return [Refused(NotEnoughPermission, answered.raised)]
        after = chain.after
        issued = chain.issued.keypair.access_key
        seen: list[Verdict] = [
            *_at(
                "issued.",
                KeypairNodeLook(self.started).generated(
                    chain.issued.keypair,
                    laid.caller,
                    is_active=True,
                    is_admin=False,
                    is_default=False,
                    rate_limit=SERVER_RATE_LIMIT,
                    resource_policy=laid.key_policy,
                ),
            ),
            Skipped(
                "issued.secret_key",
                Says(
                    "매니저가 매번 새로 생성합니다",
                    english="the manager makes it anew every time",
                ),
            ),
            Same("switched", chain.switched, True),
            Same("revoked", chain.revoked, True),
            Same("after.total_count", after.total_count, 1),
            Same("after.has_next_page", after.has_next_page, False),
            Same("after.has_previous_page", after.has_previous_page, False),
            Held(
                "after.items.access_key",
                [one.access_key for one in after.items],
                SameAs([issued], Says("발급한 키", english="the key issued")),
            ),
        ]
        if after.items:
            left = after.items[0]
            written = WrittenByThisRun(self.started)
            seen.extend(
                _at(
                    "after.items[0].",
                    [
                        Same("is_active", left.is_active, True),
                        Same("is_admin", left.is_admin, False),
                        Same("is_default", left.is_default, True),
                        Same("rate_limit", left.rate_limit, SERVER_RATE_LIMIT),
                        Same("resource_policy", left.resource_policy, laid.key_policy),
                        Skipped(
                            "ssh_public_key",
                            Says(
                                "매니저가 생성한 RSA 키입니다",
                                english="it is the RSA key the manager created",
                            ),
                        ),
                        Same("num_queries", left.num_queries, 0),
                        Same("last_used", left.last_used, None),
                        Held(
                            "user_id",
                            left.user_id,
                            SameAs(laid.caller.id, Says("키 소유자", english="the key owner")),
                        ),
                        Held("created_at", left.created_at, written),
                        Held("modified_at", left.modified_at, written),
                    ],
                )
            )
        return seen


RW = (Permission.READ, Permission.UPDATE)

type Row = Scenario[TestSeedingSession, Keyholder, UserAdapter, Answer]


@dataclass(frozen=True)
class OwnKeyRow(Scenario[TestSeedingSession, Keyholder, UserAdapter, Answer]):
    """표의 한 행. 이름, 보장하는 것, 세 단계를 값으로 받는다."""

    name: str
    guarantee: str
    situation: SomeoneWithKeys
    calling: When[Keyholder, UserAdapter, Answer]
    seeing: Then[Keyholder, Answer]

    @override
    def summary(self) -> str:
        return self.name

    @override
    def describe(self) -> str:
        return self.guarantee

    @override
    def given(self) -> Given[TestSeedingSession, Keyholder]:
        return self.situation

    @override
    def when(self) -> When[Keyholder, UserAdapter, Answer]:
        return self.calling

    @override
    def then(self) -> Then[Keyholder, Answer]:
        return self.seeing


NOW = datetime.now(UTC)

SCENARIOS: list[Row] = [
    OwnKeyRow(
        "a-user-granted-update-on-themself-issues-a-key-that-follows-their-default-key",
        Says(
            "자기 사용자 스코프에서 UPDATE 를 받은 사용자가 발급하면, 기본 키의 관리자 표시, "
            "정책, 요청 한도를 따르고 기본 표시는 없는 키와 secret 이 응답으로 옵니다",
            english=(
                "when a user granted UPDATE in their own user scope issues a key, the key "
                "follows the admin flag, policy, and rate limit of the default key, holds no "
                "default flag, and comes back with its secret"
            ),
        ),
        SomeoneWithKeys(permissions=(Permission.UPDATE,)),
        Issuing(),
        TheIssuedKey(started=NOW),
    ),
    OwnKeyRow(
        "a-user-granted-nothing-may-not-issue-their-own-key",
        Says(
            "역할을 받지 않은 사용자가 자기 키를 발급하려 하면, 본인이어도 엔티티 권한 문이 "
            "막습니다",
            english=(
                "a user holding no role who tries to issue their own key is rejected by the "
                "entity permission gate even for themselves"
            ),
        ),
        SomeoneWithKeys(),
        Issuing(),
        TheCallIsRefused(NotEnoughPermission),
    ),
    OwnKeyRow(
        "a-user-granted-read-and-update-revokes-a-non-default-key",
        Says(
            "권한 받은 사용자가 자기의 기본 아닌 키를 회수하면, 성공이 오고 자기 키 검색에서 "
            "그 키가 빠집니다",
            english=(
                "when a user holding the permission revokes their own extra key, success comes "
                "back and that key leaves their own key search"
            ),
        ),
        SomeoneWithKeys(permissions=RW, extra_keys=1),
        RevokingTheExtraKey(),
        OnlyTheDefaultKeyIsLeft(started=NOW),
    ),
    OwnKeyRow(
        "a-user-granted-nothing-may-not-revoke-their-own-key",
        Says(
            "역할을 받지 않은 사용자가 회수하려 하면, "
            "소유자 조회 단계가 없는 키와 같은 예외로 막습니다",
            english=(
                "a user holding no role who tries to revoke a key is rejected at the owner "
                "lookup step with the same exception as a key that does not exist"
            ),
        ),
        SomeoneWithKeys(extra_keys=1),
        RevokingTheExtraKey(),
        TheCallIsRefused(GenericBadRequest),
    ),
    OwnKeyRow(
        "a-user-granted-only-read-may-not-revoke-their-own-key",
        Says(
            "자기 스코프에서 READ 만 받은 사용자가 회수하려 하면, "
            "소유자 조회는 지나고 엔티티 권한 문이 막습니다",
            english=(
                "a user granted only READ in their own scope who tries to revoke a key passes "
                "the owner lookup and is rejected by the entity permission gate"
            ),
        ),
        SomeoneWithKeys(permissions=(Permission.READ,), extra_keys=1),
        RevokingTheExtraKey(),
        TheCallIsRefused(NotEnoughPermission),
    ),
    OwnKeyRow(
        "the-default-key-may-not-be-revoked",
        Says(
            "권한 받은 사용자가 자기 기본 키를 회수하려 하면, 입력 검증이 막습니다",
            english=(
                "when a user holding the permission tries to revoke their own default key, "
                "input validation rejects it"
            ),
        ),
        SomeoneWithKeys(permissions=RW),
        RevokingTheDefaultKey(),
        TheCallIsRefused(KeyPairForbidden),
    ),
    OwnKeyRow(
        "an-access-key-nobody-holds-may-not-be-revoked",
        Says(
            "권한 받은 사용자가 어떤 키도 아닌 값을 주면, "
            "소유자 조회 단계가 권한 없음과 같은 예외로 막습니다",
            english=(
                "when a user holding the permission gives a value that is no key, the owner "
                "lookup step rejects it with the same exception as a missing permission"
            ),
        ),
        SomeoneWithKeys(permissions=RW),
        RevokingAKeyNobodyHolds(),
        TheCallIsRefused(GenericBadRequest),
    ),
    OwnKeyRow(
        "a-user-granted-read-and-update-turns-off-a-non-default-key",
        Says(
            "자기 스코프에서 READ 와 UPDATE 를 받은 사용자가 기본 아닌 키를 비활성으로 변경하면, "
            "활성만 변경된 키 노드가 응답으로 옵니다",
            english=(
                "when a user granted READ and UPDATE in their own scope turns an extra key "
                "inactive, the key node comes back with only the active flag changed"
            ),
        ),
        SomeoneWithKeys(permissions=RW, extra_keys=1),
        TurningOffTheExtraKey(),
        TheKeyIsOff(started=NOW),
    ),
    OwnKeyRow(
        "a-user-granted-nothing-may-not-turn-off-their-own-key",
        Says(
            "역할 없이 키를 비활성으로 변경하려 하면, 소유자 조회 단계가 막습니다",
            english=(
                "a user holding no role who tries to turn a key inactive is rejected at the "
                "owner lookup step"
            ),
        ),
        SomeoneWithKeys(extra_keys=1),
        TurningOffTheExtraKey(),
        TheCallIsRefused(GenericBadRequest),
    ),
    OwnKeyRow(
        "a-user-granted-only-read-may-not-turn-off-their-own-key",
        Says(
            "READ 만 받고 키를 비활성으로 변경하려 하면, 엔티티 권한 문이 막습니다",
            english=(
                "a user holding only READ who tries to turn a key inactive is rejected by the "
                "entity permission gate"
            ),
        ),
        SomeoneWithKeys(permissions=(Permission.READ,), extra_keys=1),
        TurningOffTheExtraKey(),
        TheCallIsRefused(NotEnoughPermission),
    ),
    OwnKeyRow(
        "the-default-key-may-not-be-turned-off",
        Says(
            "권한 받은 사용자가 자기 기본 키를 비활성으로 변경하려 하면, 입력 검증이 막습니다",
            english=(
                "when a user holding the permission tries to turn their own default key "
                "inactive, input validation rejects it"
            ),
        ),
        SomeoneWithKeys(permissions=RW),
        TurningOffTheDefaultKey(),
        TheCallIsRefused(KeyPairForbidden),
    ),
    OwnKeyRow(
        "a-user-granted-read-and-update-moves-their-default-key",
        Says(
            "자기 스코프에서 UPDATE 를 받은 사용자가 기본 아닌 활성 키로 기본 키를 옮기면, "
            "성공이 오고 사용자 노드의 기본 키가 그 키가 됩니다",
            english=(
                "when a user granted UPDATE in their own scope moves the default key to an "
                "extra key that is active, success comes back and the default key of the user "
                "node becomes that key"
            ),
        ),
        SomeoneWithKeys(permissions=RW, extra_keys=1),
        SwitchingToTheExtraKey(),
        TheDefaultKeyMoved(started=NOW),
    ),
    OwnKeyRow(
        "a-user-granted-nothing-may-not-move-their-default-key",
        Says(
            "역할 없이 기본 키를 옮기려 하면, 엔티티 권한 문이 막습니다",
            english=(
                "a user holding no role who tries to move the default key is rejected by the "
                "entity permission gate"
            ),
        ),
        SomeoneWithKeys(extra_keys=1),
        SwitchingToAnExtraKeyWithoutRereading(),
        TheCallIsRefused(NotEnoughPermission),
    ),
    OwnKeyRow(
        "someone-elses-key-may-not-become-the-default-key",
        Says(
            "권한 받은 사용자가 다른 사용자의 키를 주면, 입력 검증이 막습니다",
            english=(
                "when a user holding the permission gives another user's key, input "
                "validation rejects it"
            ),
        ),
        SomeoneWithKeys(permissions=(Permission.UPDATE,), other_holds_a_key=True),
        SwitchingToSomeoneElsesKey(),
        TheCallIsRefused(KeyPairForbidden),
    ),
    OwnKeyRow(
        "a-user-granted-read-searching-their-keys-sees-only-their-own",
        Says(
            "자기 스코프에서 READ 를 받은 사용자가 자기 키를 조회하면, 다른 사용자의 키는 빠집니다",
            english=(
                "when a user granted READ in their own scope searches their own keys, the keys "
                "of other users are left out"
            ),
        ),
        SomeoneWithKeys(permissions=(Permission.READ,), extra_keys=1, other_holds_a_key=True),
        SearchingMyKeys(),
        OnlyMyTwoKeys(started=NOW),
    ),
    OwnKeyRow(
        "a-user-granted-nothing-may-not-search-their-own-keys",
        Says(
            "역할 없이 자기 키를 조회하려 하면, 스코프 권한 문이 막습니다",
            english=(
                "a user holding no role who tries to search their own keys is rejected by the "
                "scope permission gate"
            ),
        ),
        SomeoneWithKeys(),
        SearchingMyKeys(),
        TheCallIsRefused(NotEnoughPermission),
    ),
    OwnKeyRow(
        "searching-own-keys-without-page-arguments-answers-the-ten-newest",
        Says(
            "권한 받은 사용자가 페이지 인자 없이 조회하면, "
            "생성 시각 내림차순 열 개와 다음 페이지 여부가 응답으로 옵니다",
            english=(
                "when a user holding the permission searches without page arguments, ten keys "
                "in descending creation time and the next page flag come back"
            ),
        ),
        SomeoneWithKeys(permissions=(Permission.READ,), extra_keys=10),
        SearchingMyKeys(),
        TheFirstTenOfEleven(started=NOW),
    ),
    OwnKeyRow(
        "an-issued-key-made-default-lets-the-original-default-key-be-revoked",
        Says(
            "권한 받은 사용자가 키를 발급하고 그 키로 기본 키를 옮긴 다음 원래 기본 키를 "
            "회수하면, 세 호출이 차례로 통과하고 발급한 키 하나만 남습니다",
            english=(
                "when a user holding the permission issues a key, moves the default key to it, "
                "and revokes the original default key, all three calls pass in turn and only "
                "the issued key is left"
            ),
        ),
        SomeoneWithKeys(permissions=RW),
        IssuingThenSwitchingThenRevoking(),
        OnlyTheIssuedKeyIsLeft(started=NOW),
    ),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_own_keypairs(
    scenario: Row, adapter: UserAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
