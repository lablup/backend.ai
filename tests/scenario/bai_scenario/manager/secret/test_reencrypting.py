"""다시 암호화하기 — 저장된 비밀 키 전부를 쓰기 제공자로 다시 쓰고, 누가 돌릴 수 있는가.

훑기는 모든 행을 같게 다룬다. 이미 쓰기 제공자의 키에 있는 것도 다시 쓰므로 다시 쓴 수는 언제나
훑은 수와 같고, 쓰기 제공자가 평문이면 값을 평문으로 되돌린다.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, override

import pytest
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.secret import (
    CONFIG_KEYS,
    CONFIG_PROVIDER,
    WRITE_PROVIDER,
    AKeyringAndACaller,
    EveryRowIsRewrittenOntoTheWriter,
    UsersHoldingSecrets,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.secret.response import AdminReencryptSecretsPayload
from ai.backend.manager.api.adapters.secret.adapter import SecretAdapter
from ai.backend.manager.data.secret.types import KeyProviderType
from ai.backend.manager.errors.auth import InsufficientPrivilege
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Configured, Given, Scenario, Then, When

type Reencrypted = AdminReencryptSecretsPayload
type ReencryptingStep = Scenario[SeedingSession, AKeyringAndACaller, SecretAdapter, Reencrypted]


@dataclass(frozen=True)
class Reencrypting(When[AKeyringAndACaller, SecretAdapter, Reencrypted]):
    """저장된 비밀 키 전부를 다시 암호화한다."""

    @override
    def operation(self) -> str:
        return "admin_reencrypt_secrets"

    @override
    def describe(self, laid: AKeyringAndACaller) -> str:
        return f"{laid.caller.username}이 비밀 키 전부를 다시 암호화"

    @override
    async def call(self, adapter: SecretAdapter, laid: AKeyringAndACaller) -> Reencrypted:
        with ActingAs(laid.caller):
            return await adapter.admin_reencrypt_secrets()


@dataclass(frozen=True)
class PlaintextSecretsMoveOntoTheConfigKey(
    Scenario[SeedingSession, AKeyringAndACaller, SecretAdapter, Reencrypted], Configured
):
    @override
    def summary(self) -> str:
        return "reencrypting-moves-plaintext-secrets-onto-the-config-key"

    @override
    def describe(self) -> str:
        return (
            "설정 키가 쓰기 제공자일 때 평문 비밀 키 둘을 다시 암호화하면, 둘을 훑어 둘을 다시 썼다는 "
            "답과 함께 그 키가 둘을 쥐고 평문은 없는 상태가 온다"
        )

    @override
    def config(self) -> Mapping[str, Any]:
        return {WRITE_PROVIDER: KeyProviderType.CONFIG.value, CONFIG_PROVIDER: CONFIG_KEYS}

    @override
    def given(self) -> Given[SeedingSession, AKeyringAndACaller]:
        return UsersHoldingSecrets(role=UserRole.SUPERADMIN, plaintext_besides=1)

    @override
    def when(self) -> When[AKeyringAndACaller, SecretAdapter, Reencrypted]:
        return Reencrypting()

    @override
    def then(self) -> Then[AKeyringAndACaller, Reencrypted]:
        return EveryRowIsRewrittenOntoTheWriter(write_provider=KeyProviderType.CONFIG)


@dataclass(frozen=True)
class SecretsAlreadyOnTheKeyAreRewrittenAgain(
    Scenario[SeedingSession, AKeyringAndACaller, SecretAdapter, Reencrypted], Configured
):
    @override
    def summary(self) -> str:
        return "reencrypting-rewrites-secrets-already-on-the-config-key"

    @override
    def describe(self) -> str:
        return (
            "설정 키가 쓰기 제공자이고 비밀 키 둘이 이미 그 키에 있을 때 다시 암호화하면, 둘을 훑어 "
            "둘을 다시 썼다는 답이 오고 상태는 그대로 그 키가 둘이다"
        )

    @override
    def config(self) -> Mapping[str, Any]:
        return {WRITE_PROVIDER: KeyProviderType.CONFIG.value, CONFIG_PROVIDER: CONFIG_KEYS}

    @override
    def given(self) -> Given[SeedingSession, AKeyringAndACaller]:
        return UsersHoldingSecrets(
            role=UserRole.SUPERADMIN,
            plaintext_besides=0,
            encrypted_besides=1,
            caller_encrypted=True,
        )

    @override
    def when(self) -> When[AKeyringAndACaller, SecretAdapter, Reencrypted]:
        return Reencrypting()

    @override
    def then(self) -> Then[AKeyringAndACaller, Reencrypted]:
        return EveryRowIsRewrittenOntoTheWriter(write_provider=KeyProviderType.CONFIG)


@dataclass(frozen=True)
class APlainWriterRewritesPlaintextAsPlaintext(
    Scenario[SeedingSession, AKeyringAndACaller, SecretAdapter, Reencrypted]
):
    @override
    def summary(self) -> str:
        return "reencrypting-with-a-plain-writer-rewrites-plaintext-secrets-as-plaintext"

    @override
    def describe(self) -> str:
        return (
            "쓰기 제공자가 평문일 때 평문 비밀 키 둘을 다시 암호화하면, 둘을 훑어 둘을 다시 썼다는 답이 "
            "오고 상태는 그대로 평문 둘이다. 다시 쓴 수는 값이 바뀌었는지가 아니라 행을 다시 썼는지를 센다"
        )

    @override
    def given(self) -> Given[SeedingSession, AKeyringAndACaller]:
        return UsersHoldingSecrets(role=UserRole.SUPERADMIN, plaintext_besides=1)

    @override
    def when(self) -> When[AKeyringAndACaller, SecretAdapter, Reencrypted]:
        return Reencrypting()

    @override
    def then(self) -> Then[AKeyringAndACaller, Reencrypted]:
        return EveryRowIsRewrittenOntoTheWriter(write_provider=KeyProviderType.PLAIN)


@dataclass(frozen=True)
class APlainWriterTurnsEncryptedSecretsBackToPlaintext(
    Scenario[SeedingSession, AKeyringAndACaller, SecretAdapter, Reencrypted], Configured
):
    @override
    def summary(self) -> str:
        return "reencrypting-with-a-plain-writer-turns-an-encrypted-secret-back-to-plaintext"

    @override
    def describe(self) -> str:
        return (
            "쓰기 제공자가 평문이고 설정 키 제공자는 읽기용으로만 있을 때 그 키로 암호화된 비밀 키를 "
            "다시 암호화하면, 하나를 훑어 하나를 다시 썼다는 답이 오고 상태는 평문뿐이다"
        )

    @override
    def config(self) -> Mapping[str, Any]:
        return {WRITE_PROVIDER: KeyProviderType.PLAIN.value, CONFIG_PROVIDER: CONFIG_KEYS}

    @override
    def given(self) -> Given[SeedingSession, AKeyringAndACaller]:
        return UsersHoldingSecrets(
            role=UserRole.SUPERADMIN, plaintext_besides=0, caller_encrypted=True
        )

    @override
    def when(self) -> When[AKeyringAndACaller, SecretAdapter, Reencrypted]:
        return Reencrypting()

    @override
    def then(self) -> Then[AKeyringAndACaller, Reencrypted]:
        return EveryRowIsRewrittenOntoTheWriter(write_provider=KeyProviderType.PLAIN)


@dataclass(frozen=True)
class TheMonitorMayNotReencrypt(
    Scenario[SeedingSession, AKeyringAndACaller, SecretAdapter, Reencrypted]
):
    @override
    def summary(self) -> str:
        return "the-monitor-may-not-reencrypt-secrets"

    @override
    def describe(self) -> str:
        return "모니터 역할이 다시 암호화를 돌리면 역할로 거부된다. 상태는 읽을 수 있지만 훑기는 쓰기라 지나지 못한다"

    @override
    def given(self) -> Given[SeedingSession, AKeyringAndACaller]:
        return UsersHoldingSecrets(role=UserRole.MONITOR, plaintext_besides=0)

    @override
    def when(self) -> When[AKeyringAndACaller, SecretAdapter, Reencrypted]:
        return Reencrypting()

    @override
    def then(self) -> Then[AKeyringAndACaller, Reencrypted]:
        return TheCallIsRefused(InsufficientPrivilege)


@dataclass(frozen=True)
class AUserWhoIsNotTheSuperadminMayNotReencrypt(
    Scenario[SeedingSession, AKeyringAndACaller, SecretAdapter, Reencrypted]
):
    @override
    def summary(self) -> str:
        return "a-user-who-is-not-the-superadmin-may-not-reencrypt-secrets"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 아닌 사용자가 다시 암호화를 돌리면 역할로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, AKeyringAndACaller]:
        return UsersHoldingSecrets(role=UserRole.USER, plaintext_besides=0)

    @override
    def when(self) -> When[AKeyringAndACaller, SecretAdapter, Reencrypted]:
        return Reencrypting()

    @override
    def then(self) -> Then[AKeyringAndACaller, Reencrypted]:
        return TheCallIsRefused(InsufficientPrivilege)


SCENARIOS: list[ReencryptingStep] = [
    PlaintextSecretsMoveOntoTheConfigKey(),
    SecretsAlreadyOnTheKeyAreRewrittenAgain(),
    APlainWriterRewritesPlaintextAsPlaintext(),
    APlainWriterTurnsEncryptedSecretsBackToPlaintext(),
    TheMonitorMayNotReencrypt(),
    AUserWhoIsNotTheSuperadminMayNotReencrypt(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_reencrypting(
    scenario: ReencryptingStep, adapter: SecretAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
