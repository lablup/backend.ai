"""자기 SSH 키 업로드."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override

import pytest

from ai.backend.common.dto.manager.v2.ssh_key.request import MyUploadSSHKeyInput
from ai.backend.common.dto.manager.v2.ssh_key.response import SSHKeyNode
from ai.backend.manager.api.adapters.ssh_key.adapter import SSHKeyAdapter
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.errors.keypair import InvalidSSHPublicKey
from ai.backend.manager.errors.permission import NotEnoughPermission
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

type UploadingStep = Scenario[TestSeedingSession, SSHKeyholder, SSHKeyAdapter, SSHKeyNode]

ANOTHER_PUBLIC_KEY = (
    "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAICuqqTj6Ee2CFRyYHeq1INgqKdEoYvyazZPR69RTWOJI"
)
"""이미 가진 키와 다른 공개키. 형식 검사를 통과하는 실제 공개키다."""

NOT_A_PUBLIC_KEY = "not-an-ssh-public-key"
"""공개키 형식이 아닌 값. 거부를 부르는 입력이라 연결값이 아니다."""


@dataclass(frozen=True)
class UploadingMyKey(When[SSHKeyholder, SSHKeyAdapter, SSHKeyNode]):
    """자기 SSH 키를 업로드한다."""

    public_key: str = DEFAULT_PUBLIC_KEY

    @override
    def operation(self) -> str:
        return "my_upload"

    @override
    def describe(self, laid: SSHKeyholder) -> str:
        if self.public_key == NOT_A_PUBLIC_KEY:
            return Says(
                f"{laid.caller.username}이 공개키 형식이 아닌 값을 자기 SSH 키로 업로드합니다",
                english=f"{laid.caller.username} uploads a value that is not a public key as their SSH key",
            )
        return Says(
            f"{laid.caller.username}이 자기 SSH 키를 업로드합니다",
            english=f"{laid.caller.username} uploads their own SSH key",
        )

    @override
    async def call(self, adapter: SSHKeyAdapter, laid: SSHKeyholder) -> SSHKeyNode:
        with ActingAs(laid.caller):
            return await adapter.my_upload(MyUploadSSHKeyInput(public_key=self.public_key))


@dataclass(frozen=True)
class AUserGrantedUpdateUploadsTheirFirstKey(
    Scenario[TestSeedingSession, SSHKeyholder, SSHKeyAdapter, SSHKeyNode]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-user-granted-update-uploads-their-first-key-as-the-default"

    @override
    def describe(self) -> str:
        return Says(
            "자기 사용자에 UPDATE 권한을 받고 SSH 키가 없는 사용자가 키를 업로드하면, 그 키가 "
            "default 로 지정되어 응답으로 옵니다",
            english=(
                "when a user granted UPDATE on their own user and holding no SSH key uploads one, "
                "it comes back as the default"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, SSHKeyholder]:
        return SomeoneWithSSHKeys(permissions=(Permission.UPDATE,), holds_keys=False)

    @override
    def when(self) -> When[SSHKeyholder, SSHKeyAdapter, SSHKeyNode]:
        return UploadingMyKey()

    @override
    def then(self) -> Then[SSHKeyholder, SSHKeyNode]:
        return TheSSHKeyNode(
            started=self.started, public_key=DEFAULT_PUBLIC_KEY, is_default=True, seeded=False
        )


@dataclass(frozen=True)
class AUserHoldingADefaultUploadsANonDefaultKey(
    Scenario[TestSeedingSession, SSHKeyholder, SSHKeyAdapter, SSHKeyNode]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-user-holding-a-default-uploads-a-key-that-is-not-the-default"

    @override
    def describe(self) -> str:
        return Says(
            "자기 사용자에 UPDATE 권한을 받고 default SSH 키를 이미 가진 사용자가 키를 업로드하면, "
            "그 키는 default 가 아닌 키로 응답이 옵니다",
            english=(
                "when a user granted UPDATE on their own user and already holding a default SSH "
                "key uploads one, it comes back as not the default"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, SSHKeyholder]:
        return SomeoneWithSSHKeys(permissions=(Permission.UPDATE,))

    @override
    def when(self) -> When[SSHKeyholder, SSHKeyAdapter, SSHKeyNode]:
        return UploadingMyKey(public_key=ANOTHER_PUBLIC_KEY)

    @override
    def then(self) -> Then[SSHKeyholder, SSHKeyNode]:
        return TheSSHKeyNode(
            started=self.started, public_key=ANOTHER_PUBLIC_KEY, is_default=False, seeded=False
        )


@dataclass(frozen=True)
class AUserGrantedReadMayNotUploadAKey(
    Scenario[TestSeedingSession, SSHKeyholder, SSHKeyAdapter, SSHKeyNode]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-read-may-not-upload-a-key"

    @override
    def describe(self) -> str:
        return Says(
            "자기 사용자에 READ 권한만 받은 사용자가 SSH 키를 업로드하려 하면 권한 부족으로 "
            "거부됩니다",
            english=(
                "when a user granted only READ on their own user tries to upload an SSH key, it is "
                "rejected for lack of permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, SSHKeyholder]:
        return SomeoneWithSSHKeys(permissions=(Permission.READ,), holds_keys=False)

    @override
    def when(self) -> When[SSHKeyholder, SSHKeyAdapter, SSHKeyNode]:
        return UploadingMyKey()

    @override
    def then(self) -> Then[SSHKeyholder, SSHKeyNode]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class AValueThatIsNotAPublicKeyIsRejected(
    Scenario[TestSeedingSession, SSHKeyholder, SSHKeyAdapter, SSHKeyNode]
):
    @override
    def summary(self) -> str:
        return "a-value-that-is-not-a-public-key-is-rejected"

    @override
    def describe(self) -> str:
        return Says(
            "자기 사용자에 UPDATE 권한을 받은 사용자라도 공개키 형식이 아닌 값을 업로드하면 "
            "거부됩니다",
            english=(
                "even a user granted UPDATE on their own user is rejected when the value they "
                "upload is not a public key"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, SSHKeyholder]:
        return SomeoneWithSSHKeys(permissions=(Permission.UPDATE,), holds_keys=False)

    @override
    def when(self) -> When[SSHKeyholder, SSHKeyAdapter, SSHKeyNode]:
        return UploadingMyKey(public_key=NOT_A_PUBLIC_KEY)

    @override
    def then(self) -> Then[SSHKeyholder, SSHKeyNode]:
        return TheCallIsRefused(InvalidSSHPublicKey)


SCENARIOS: list[UploadingStep] = [
    AUserGrantedUpdateUploadsTheirFirstKey(started=datetime.now(UTC)),
    AUserHoldingADefaultUploadsANonDefaultKey(started=datetime.now(UTC)),
    AUserGrantedReadMayNotUploadAKey(),
    AValueThatIsNotAPublicKeyIsRejected(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_uploading(
    scenario: UploadingStep, adapter: SSHKeyAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
