"""사용자 SSH 키를 scope 로 검색하기."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override
from uuid import UUID

import pytest

from ai.backend.common.dto.manager.v2.ssh_key.request import (
    ScopedSearchSSHKeysInput,
    SSHKeyFilter,
    SSHKeyOrder,
    SSHKeyOrderField,
)
from ai.backend.common.dto.manager.v2.ssh_key.response import SearchSSHKeysPayload
from ai.backend.manager.api.adapters.ssh_key.adapter import SSHKeyAdapter
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Held,
    Same,
    SameAs,
    Says,
    Scenario,
    Then,
    Verdict,
    When,
)
from bai_scenario.components.answers import MissingResponse, TheCallIsRefused
from bai_scenario.components.ssh_key import (
    DEFAULT_PUBLIC_KEY,
    SomeoneWithSSHKeys,
    SSHKeyholder,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

PAGE_SIZE = 10

type SearchStep = Scenario[TestSeedingSession, SSHKeyholder, SSHKeyAdapter, SearchSSHKeysPayload]


@dataclass(frozen=True)
class SearchingMyDefaultKeys(When[SSHKeyholder, SSHKeyAdapter, SearchSSHKeysPayload]):
    """자기 사용자를 scope 로, default SSH 키만 검색한다."""

    @override
    def operation(self) -> str:
        return "scoped_search"

    @override
    def describe(self, laid: SSHKeyholder) -> str:
        return Says(
            f"{laid.caller.username}이 자기 SSH 키 중 default 인 것만 {PAGE_SIZE}개까지 검색합니다",
            english=(
                f"{laid.caller.username} searches up to {PAGE_SIZE} of their SSH keys for the "
                "default one"
            ),
        )

    @override
    async def call(self, adapter: SSHKeyAdapter, laid: SSHKeyholder) -> SearchSSHKeysPayload:
        with ActingAs(laid.caller):
            return await adapter.scoped_search(
                ScopedSearchSSHKeysInput(
                    user_id=laid.caller.id,
                    filter=SSHKeyFilter(is_default=True),
                    order=[SSHKeyOrder(field=SSHKeyOrderField.IS_DEFAULT)],
                    limit=PAGE_SIZE,
                )
            )


@dataclass(frozen=True)
class OnlyTheDefaultKey(Then[SSHKeyholder, SearchSSHKeysPayload]):
    @override
    def says(self) -> str:
        return Says(
            "다른 사용자의 키와 default 아닌 키는 빠지고, 자기 default SSH 키 하나만 실린 페이지가 "
            "응답으로 옵니다",
            english=(
                "a page holding only their default SSH key comes back, without the other user's "
                "key or the key that is not the default"
            ),
        )

    @override
    def look(self, laid: SSHKeyholder, answered: Answered[SearchSSHKeysPayload]) -> list[Verdict]:
        page = answered.response
        if page is None:
            return [MissingResponse(answered.raised)]
        verdicts: list[Verdict] = [
            Same("total_count", page.total_count, 1),
            Same("has_next_page", page.has_next_page, False),
            Same("has_previous_page", page.has_previous_page, False),
            Same("items.length", len(page.items), 1),
        ]
        if len(page.items) != 1:
            return verdicts
        node = page.items[0]
        seeded = laid.default_key()
        name = Says("심어 둔 자기 default SSH 키", english="their seeded default SSH key")
        verdicts.extend([
            Held("items[0].id", node.id, SameAs(seeded.id, name)),
            Held("items[0].field_id", node.field_id, SameAs(seeded.id, name)),
            Held[UUID](
                "items[0].user_id",
                node.user_id,
                SameAs(laid.caller.id, Says("호출한 사용자", english="the calling user")),
            ),
            Same("items[0].public_key", node.public_key, DEFAULT_PUBLIC_KEY),
            Same("items[0].is_default", node.is_default, True),
        ])
        return verdicts


@dataclass(frozen=True)
class AUserGrantedReadFindsTheirDefaultKey(
    Scenario[TestSeedingSession, SSHKeyholder, SSHKeyAdapter, SearchSSHKeysPayload]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-read-finds-their-default-key"

    @override
    def describe(self) -> str:
        return Says(
            "자기 사용자에 READ 권한을 받은 사용자가 자기 SSH 키 중 default 인 것만 검색하면 "
            "다른 사용자의 키 없이 자기 default 키 하나만 옵니다",
            english=(
                "when a user granted READ on their own user searches their SSH keys for the "
                "default one, only their default key comes back and no other user's key"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, SSHKeyholder]:
        return SomeoneWithSSHKeys(permissions=(Permission.READ,), with_stranger=True)

    @override
    def when(self) -> When[SSHKeyholder, SSHKeyAdapter, SearchSSHKeysPayload]:
        return SearchingMyDefaultKeys()

    @override
    def then(self) -> Then[SSHKeyholder, SearchSSHKeysPayload]:
        return OnlyTheDefaultKey()


@dataclass(frozen=True)
class AUserWithoutReadMayNotSearchTheirKeys(
    Scenario[TestSeedingSession, SSHKeyholder, SSHKeyAdapter, SearchSSHKeysPayload]
):
    @override
    def summary(self) -> str:
        return "a-user-without-read-may-not-search-their-keys"

    @override
    def describe(self) -> str:
        return Says(
            "자기 사용자에 아무 권한도 받지 않은 사용자가 자기 SSH 키를 검색하려 하면 권한 부족으로 거부됩니다",
            english=(
                "when a user granted no permission on their own user tries to search their SSH "
                "keys, it is rejected for lack of permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, SSHKeyholder]:
        return SomeoneWithSSHKeys()

    @override
    def when(self) -> When[SSHKeyholder, SSHKeyAdapter, SearchSSHKeysPayload]:
        return SearchingMyDefaultKeys()

    @override
    def then(self) -> Then[SSHKeyholder, SearchSSHKeysPayload]:
        return TheCallIsRefused(NotEnoughPermission)


SCENARIOS: list[SearchStep] = [
    AUserGrantedReadFindsTheirDefaultKey(),
    AUserWithoutReadMayNotSearchTheirKeys(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_searching(
    scenario: SearchStep, adapter: SSHKeyAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
