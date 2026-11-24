"""자기 default SSH 키 바꾸기."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override

import pytest

from ai.backend.common.dto.manager.v2.ssh_key.response import SSHKeyNode
from ai.backend.manager.api.adapters.ssh_key.adapter import SSHKeyAdapter
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Says, Scenario, Then, When
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.ssh_key import (
    EXTRA_PUBLIC_KEY,
    SomeoneWithSSHKeys,
    SSHKeyholder,
    TheSSHKeyNode,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type SwitchingStep = Scenario[TestSeedingSession, SSHKeyholder, SSHKeyAdapter, SSHKeyNode]


@dataclass(frozen=True)
class SwitchingToMyOtherKey(When[SSHKeyholder, SSHKeyAdapter, SSHKeyNode]):
    """default 가 아닌 자기 SSH 키를 default 로 지정한다."""

    @override
    def operation(self) -> str:
        return "switch_default"

    @override
    def describe(self, laid: SSHKeyholder) -> str:
        return Says(
            f"{laid.caller.username}이 default 가 아닌 자기 SSH 키를 default 로 지정합니다",
            english=(
                f"{laid.caller.username} sets their SSH key that is not the default as the default"
            ),
        )

    @override
    async def call(self, adapter: SSHKeyAdapter, laid: SSHKeyholder) -> SSHKeyNode:
        with ActingAs(laid.caller):
            return await adapter.switch_default(laid.extra_key().id)


@dataclass(frozen=True)
class AUserGrantedUpdateSwitchesTheirDefault(
    Scenario[TestSeedingSession, SSHKeyholder, SSHKeyAdapter, SSHKeyNode]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-user-granted-update-switches-their-default-key"

    @override
    def describe(self) -> str:
        return Says(
            "자기 사용자에 READ, UPDATE 권한을 받은 사용자가 default 가 아닌 자기 SSH 키를 default 로 "
            "지정하면, default 가 된 그 키가 응답으로 옵니다",
            english=(
                "when a user granted READ and UPDATE on their own user sets their SSH key that is not "
                "the default as the default, that key comes back as the default"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, SSHKeyholder]:
        return SomeoneWithSSHKeys(permissions=(Permission.READ, Permission.UPDATE))

    @override
    def when(self) -> When[SSHKeyholder, SSHKeyAdapter, SSHKeyNode]:
        return SwitchingToMyOtherKey()

    @override
    def then(self) -> Then[SSHKeyholder, SSHKeyNode]:
        return TheSSHKeyNode(started=self.started, public_key=EXTRA_PUBLIC_KEY, is_default=True)


@dataclass(frozen=True)
class AUserGrantedReadMayNotSwitchTheirDefault(
    Scenario[TestSeedingSession, SSHKeyholder, SSHKeyAdapter, SSHKeyNode]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-read-may-not-switch-their-default-key"

    @override
    def describe(self) -> str:
        return Says(
            "자기 사용자에 READ 권한만 받은 사용자가 자기 SSH 키를 default 로 지정하려 하면 "
            "권한 부족으로 거부됩니다",
            english=(
                "when a user granted only READ on their own user tries to set their SSH key as "
                "the default, it is rejected for lack of permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, SSHKeyholder]:
        return SomeoneWithSSHKeys(permissions=(Permission.READ,))

    @override
    def when(self) -> When[SSHKeyholder, SSHKeyAdapter, SSHKeyNode]:
        return SwitchingToMyOtherKey()

    @override
    def then(self) -> Then[SSHKeyholder, SSHKeyNode]:
        return TheCallIsRefused(NotEnoughPermission)


SCENARIOS: list[SwitchingStep] = [
    AUserGrantedUpdateSwitchesTheirDefault(started=datetime.now(UTC)),
    AUserGrantedReadMayNotSwitchTheirDefault(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_switching_default(
    scenario: SwitchingStep, adapter: SSHKeyAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
