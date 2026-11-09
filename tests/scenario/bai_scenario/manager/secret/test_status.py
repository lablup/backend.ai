"""비밀 상태 조회 — 저장된 비밀 키가 어느 키로 암호화돼 있는지 집계하고, 누가 조회할 수 있는가.

집계 대상 비밀은 키페어의 비밀 키 하나뿐이고 호출자도 키페어를 가지므로, 집계에는 언제나
호출자의 비밀 키가 포함된다.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, override

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.secret.response import AdminSecretStatusPayload
from ai.backend.manager.api.adapters.secret.adapter import SecretAdapter
from ai.backend.manager.data.secret.types import KeyProviderType
from ai.backend.manager.errors.auth import InsufficientPrivilege
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Configured, Given, Says, Scenario, Then, When
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.secret import (
    CONFIG_KEYS,
    CONFIG_PROVIDER,
    WRITE_PROVIDER,
    AKeyringAndACaller,
    TheStatusCountsWhatIsLaid,
    UsersHoldingSecrets,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type StatusStep = Scenario[
    TestSeedingSession, AKeyringAndACaller, SecretAdapter, AdminSecretStatusPayload
]


@dataclass(frozen=True)
class ReadingTheStatus(When[AKeyringAndACaller, SecretAdapter, AdminSecretStatusPayload]):
    """상태를 조회한다."""

    @override
    def operation(self) -> str:
        return "admin_secret_status"

    @override
    def describe(self, laid: AKeyringAndACaller) -> str:
        return Says(
            f"{laid.caller.username} 이 비밀 상태를 조회합니다",
            english=f"{laid.caller.username} reads the secret status",
        )

    @override
    async def call(
        self, adapter: SecretAdapter, laid: AKeyringAndACaller
    ) -> AdminSecretStatusPayload:
        with ActingAs(laid.caller):
            return await adapter.admin_secret_status()


@dataclass(frozen=True)
class TheSuperadminCountsPlaintextSecrets(
    Scenario[TestSeedingSession, AKeyringAndACaller, SecretAdapter, AdminSecretStatusPayload]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-reads-a-status-counting-the-plaintext-secrets"

    @override
    def describe(self) -> str:
        return Says(
            "쓰기 provider 가 평문일 때 superadmin 이 상태를 조회하면, 쓰기 provider 는 평문이고 "
            "집계는 호출자까지 포함해 평문 비밀 키를 가진 수 한 항목입니다",
            english=(
                "when the write provider is plaintext and the superadmin reads the status, "
                "the write provider is plaintext and the count is one entry for the secrets "
                "held in plaintext, including the caller's"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AKeyringAndACaller]:
        return UsersHoldingSecrets(role=UserRole.SUPERADMIN, plaintext_besides=1)

    @override
    def when(self) -> When[AKeyringAndACaller, SecretAdapter, AdminSecretStatusPayload]:
        return ReadingTheStatus()

    @override
    def then(self) -> Then[AKeyringAndACaller, AdminSecretStatusPayload]:
        return TheStatusCountsWhatIsLaid(write_provider=KeyProviderType.PLAIN)


@dataclass(frozen=True)
class MixedKeysAreCountedApart(
    Scenario[TestSeedingSession, AKeyringAndACaller, SecretAdapter, AdminSecretStatusPayload],
    Configured,
):
    @override
    def summary(self) -> str:
        return "secrets-on-different-keys-are-counted-apart"

    @override
    def describe(self) -> str:
        return Says(
            "설정 키로 암호화된 비밀 키와 평문 비밀 키가 섞여 있을 때 상태를 조회하면, "
            "그 키로 암호화된 수와 평문인 수가 두 항목으로 따로 반환됩니다",
            english=(
                "when secrets encrypted with the config key and plaintext secrets are mixed, "
                "reading the status returns the encrypted count and the plaintext count "
                "as two separate entries"
            ),
        )

    @override
    def config(self) -> Mapping[str, Any]:
        return {WRITE_PROVIDER: KeyProviderType.CONFIG.value, CONFIG_PROVIDER: CONFIG_KEYS}

    @override
    def given(self) -> Given[TestSeedingSession, AKeyringAndACaller]:
        return UsersHoldingSecrets(
            role=UserRole.SUPERADMIN, plaintext_besides=0, encrypted_besides=1
        )

    @override
    def when(self) -> When[AKeyringAndACaller, SecretAdapter, AdminSecretStatusPayload]:
        return ReadingTheStatus()

    @override
    def then(self) -> Then[AKeyringAndACaller, AdminSecretStatusPayload]:
        return TheStatusCountsWhatIsLaid(write_provider=KeyProviderType.CONFIG)


@dataclass(frozen=True)
class TheMonitorReadsTheStatusLikeTheSuperadmin(
    Scenario[TestSeedingSession, AKeyringAndACaller, SecretAdapter, AdminSecretStatusPayload]
):
    @override
    def summary(self) -> str:
        return "the-monitor-reads-the-secret-status-like-the-superadmin"

    @override
    def describe(self) -> str:
        return Says(
            "모니터 역할이 상태를 조회하면 superadmin 과 같은 응답이 반환됩니다. "
            "superadmin 검사는 모니터의 읽기를 허용합니다",
            english=(
                "when the monitor role reads the status, the same response as the superadmin's "
                "comes back, because the superadmin check allows the monitor to read"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AKeyringAndACaller]:
        return UsersHoldingSecrets(role=UserRole.MONITOR, plaintext_besides=1)

    @override
    def when(self) -> When[AKeyringAndACaller, SecretAdapter, AdminSecretStatusPayload]:
        return ReadingTheStatus()

    @override
    def then(self) -> Then[AKeyringAndACaller, AdminSecretStatusPayload]:
        return TheStatusCountsWhatIsLaid(write_provider=KeyProviderType.PLAIN)


@dataclass(frozen=True)
class AUserWhoIsNotTheSuperadminMayNotReadTheStatus(
    Scenario[TestSeedingSession, AKeyringAndACaller, SecretAdapter, AdminSecretStatusPayload]
):
    @override
    def summary(self) -> str:
        return "a-user-who-is-not-the-superadmin-may-not-read-the-secret-status"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 아닌 사용자가 상태를 조회하면 역할 부족으로 거부됩니다",
            english="when a user who is not the superadmin reads the status, it is rejected "
            "for lack of the role",
        )

    @override
    def given(self) -> Given[TestSeedingSession, AKeyringAndACaller]:
        return UsersHoldingSecrets(role=UserRole.USER, plaintext_besides=0)

    @override
    def when(self) -> When[AKeyringAndACaller, SecretAdapter, AdminSecretStatusPayload]:
        return ReadingTheStatus()

    @override
    def then(self) -> Then[AKeyringAndACaller, AdminSecretStatusPayload]:
        return TheCallIsRefused(InsufficientPrivilege)


SCENARIOS: list[StatusStep] = [
    TheSuperadminCountsPlaintextSecrets(),
    MixedKeysAreCountedApart(),
    TheMonitorReadsTheStatusLikeTheSuperadmin(),
    AUserWhoIsNotTheSuperadminMayNotReadTheStatus(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_status(
    scenario: StatusStep, adapter: SecretAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
