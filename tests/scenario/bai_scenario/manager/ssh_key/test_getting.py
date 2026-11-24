"""SSH 키 하나 읽기."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override

import pytest

from ai.backend.common.dto.manager.v2.ssh_key.response import SSHKeyNode
from ai.backend.manager.api.adapters.ssh_key.adapter import SSHKeyAdapter
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.errors.common import GenericBadRequest
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Says, Scenario, Then, When
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.ssh_key import (
    DEFAULT_PUBLIC_KEY,
    SomeoneWithSSHKeys,
    SSHKeyholder,
    TheSSHKeyNode,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type GettingStep = Scenario[TestSeedingSession, SSHKeyholder, SSHKeyAdapter, SSHKeyNode]


@dataclass(frozen=True)
class ReadingMyDefaultKey(When[SSHKeyholder, SSHKeyAdapter, SSHKeyNode]):
    """자기 default SSH 키를 id 로 읽는다."""

    @override
    def operation(self) -> str:
        return "get"

    @override
    def describe(self, laid: SSHKeyholder) -> str:
        return Says(
            f"{laid.caller.username}이 자기 default SSH 키를 id 로 읽습니다",
            english=f"{laid.caller.username} reads their default SSH key by its id",
        )

    @override
    async def call(self, adapter: SSHKeyAdapter, laid: SSHKeyholder) -> SSHKeyNode:
        with ActingAs(laid.caller):
            return await adapter.get(laid.default_key().id)


@dataclass(frozen=True)
class AUserGrantedReadReadsTheirKey(
    Scenario[TestSeedingSession, SSHKeyholder, SSHKeyAdapter, SSHKeyNode]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-user-granted-read-reads-their-key"

    @override
    def describe(self) -> str:
        return Says(
            "자기 사용자에 READ 권한을 받은 사용자가 자기 SSH 키를 id 로 읽으면 그 키가 응답으로 옵니다",
            english=(
                "when a user granted READ on their own user reads their SSH key by its id, "
                "that key comes back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, SSHKeyholder]:
        return SomeoneWithSSHKeys(permissions=(Permission.READ,))

    @override
    def when(self) -> When[SSHKeyholder, SSHKeyAdapter, SSHKeyNode]:
        return ReadingMyDefaultKey()

    @override
    def then(self) -> Then[SSHKeyholder, SSHKeyNode]:
        return TheSSHKeyNode(started=self.started, public_key=DEFAULT_PUBLIC_KEY, is_default=True)


@dataclass(frozen=True)
class AUserWithoutReadMayNotReadTheirKey(
    Scenario[TestSeedingSession, SSHKeyholder, SSHKeyAdapter, SSHKeyNode]
):
    @override
    def summary(self) -> str:
        return "a-user-without-read-may-not-read-their-key"

    @override
    def describe(self) -> str:
        return Says(
            "자기 사용자에 아무 권한도 받지 않은 사용자가 자기 SSH 키를 읽으려 하면, "
            "소유자 조회 단계가 없는 키와 같은 예외로 막습니다",
            english=(
                "a user granted no permission on their own user who tries to read their SSH key "
                "is rejected at the owner lookup step with the same exception as a key that does "
                "not exist"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, SSHKeyholder]:
        return SomeoneWithSSHKeys()

    @override
    def when(self) -> When[SSHKeyholder, SSHKeyAdapter, SSHKeyNode]:
        return ReadingMyDefaultKey()

    @override
    def then(self) -> Then[SSHKeyholder, SSHKeyNode]:
        return TheCallIsRefused(GenericBadRequest)


SCENARIOS: list[GettingStep] = [
    AUserGrantedReadReadsTheirKey(started=datetime.now(UTC)),
    AUserWithoutReadMayNotReadTheirKey(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_getting(
    scenario: GettingStep, adapter: SSHKeyAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
