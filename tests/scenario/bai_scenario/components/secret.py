"""What a secret scenario table says besides the call.

The adapter has no row of its own. What it counts and rewrites is the keypair secret every
seeded user carries, so a situation is a caller and the users beside them, some holding a
plaintext secret and some one the config key encrypted.
"""

from __future__ import annotations

import base64
from dataclasses import dataclass
from typing import Any, override

from bai_scenario.components.domain import WAS_HERE, SomeoneOf
from bai_scenario.components.system import role_named
from bai_scenario.seeds.domain.domain import SeedDomain
from bai_scenario.seeds.resource_policy.keypair import SeedKeypairPolicy
from bai_scenario.seeds.resource_policy.project import SeedProjectPolicy
from bai_scenario.seeds.resource_policy.user import SeedUserPolicy
from bai_scenario.seeds.seeder import Laid, Seeder, SeedNest
from bai_scenario.seeds.user.user import SeedUserOf

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.secret.response import (
    AdminReencryptSecretsPayload,
    AdminSecretStatusPayload,
)
from ai.backend.manager.data.secret.types import KeyProviderType, SecretKeyId, SecretKeyMaterial
from ai.backend.manager.data.user.types import UserData
from ai.backend.manager.errors.auth import InsufficientPrivilege
from ai.backend.manager.models.keypair.row import KEYPAIR_SECRET_KEY_CONTEXT
from ai.backend.manager.secret.config_provider import ConfigKeyProvider
from ai.backend.manager.secret.keys import KeyEncryptionKey
from ai.backend.manager.secret.pool import KeyProviderPool
from ai.backend.manager.secret.types import SecretValue
from ai.backend.testutils.scenario_steps import Answered, Given, Refused, Same, Then, Verdict

KEY_ID = SecretKeyId("k1")
KEY_MATERIAL = SecretKeyMaterial(base64.b64encode(b"0123456789abcdef0123456789abcdef").decode())
"""설정 키 제공자가 쥐는 키 하나. 설정 오버라이드와 시드가 같은 키를 쓴다."""

WRITE_PROVIDER = "secret_encryption.write_provider_type"
CONFIG_PROVIDER = "secret_encryption.config_provider"
CONFIG_KEYS: dict[str, Any] = {"active_key_id": KEY_ID, "keys": {KEY_ID: KEY_MATERIAL}}
"""설정 키 제공자를 켜는 오버라이드. 쓰기 제공자는 행마다 따로 고른다."""


def config_key_pool(write_provider: KeyProviderType) -> KeyProviderPool:
    """The pool a row's config builds, so a seed can encrypt with the same key."""
    provider = ConfigKeyProvider(
        keys={
            KEY_ID: KeyEncryptionKey(
                key_id=KEY_ID, material=base64.b64decode(KEY_MATERIAL, validate=True)
            )
        },
        active_key_id=KEY_ID,
    )
    return KeyProviderPool(providers=[provider], write_provider_type=write_provider)


@dataclass(frozen=True)
class AKeyringAndACaller:
    """부를 사람과, 그 사람까지 센 비밀 키의 수. 평문인 것과 설정 키로 암호화된 것을 따로 센다."""

    caller: UserData
    plaintext: int
    encrypted: int


@dataclass(frozen=True)
class SomeoneWithASecret(SeedNest[Laid[UserData]]):
    """비밀 키가 미리 준비된 사용자 한 명. 암호화된 것을 심는 유일한 길이다."""

    domain: Laid[Any]
    secret_key: SecretValue
    role: UserRole = UserRole.USER

    @override
    def kind(self) -> str:
        return "암호화된 비밀 키를 가진 사용자 한 명 준비"

    @override
    def lay(self, seed: Seeder) -> Laid[UserData]:
        seed.once(SeedProjectPolicy())
        policy = seed.creating(SeedUserPolicy())
        key_policy = seed.creating(SeedKeypairPolicy())
        return seed.provisioning(
            SeedUserOf(role=self.role, secret_key=self.secret_key), self.domain, policy, key_policy
        )


@dataclass(frozen=True)
class UsersHoldingSecrets(Given[Any, AKeyringAndACaller]):
    """부를 사람과 그 옆의 사용자들. 평문 비밀을 든 사람과 암호화된 비밀을 든 사람의 수를 정한다."""

    role: UserRole = UserRole.SUPERADMIN
    plaintext_besides: int = 1
    encrypted_besides: int = 0
    caller_encrypted: bool = False

    @override
    def describe(self) -> str:
        parts = [f"{role_named(self.role)} 한 명"]
        if self.plaintext_besides:
            parts.append(f"평문 비밀 키를 든 사용자 {self.plaintext_besides}명")
        if self.encrypted_besides:
            parts.append(f"설정 키로 암호화된 비밀 키를 든 사용자 {self.encrypted_besides}명")
        return ", ".join(parts)

    @override
    async def lay(self, seeding: Any) -> AKeyringAndACaller:
        home = await seeding.creating(SeedDomain(name_hint="home", description=WAS_HERE))
        pool = config_key_pool(KeyProviderType.CONFIG)
        if self.caller_encrypted:
            secret = await pool.encrypt("sk-caller", KEYPAIR_SECRET_KEY_CONTEXT)
            caller = await seeding.within(SomeoneWithASecret(home, secret, role=self.role))
        else:
            caller = await seeding.within(SomeoneOf(home, role=self.role))
        for _ in range(self.plaintext_besides):
            await seeding.within(SomeoneOf(home))
        for i in range(self.encrypted_besides):
            secret = await pool.encrypt(f"sk-{i}", KEYPAIR_SECRET_KEY_CONTEXT)
            await seeding.within(SomeoneWithASecret(home, secret))
        return AKeyringAndACaller(
            caller=seeding.made(caller),
            plaintext=self.plaintext_besides + (0 if self.caller_encrypted else 1),
            encrypted=self.encrypted_besides + (1 if self.caller_encrypted else 0),
        )


def _counts(plaintext: int, encrypted: int) -> list[tuple[str, str, str | None, int]]:
    """The count rows a status answers for the keypair column, in the order it sorts them."""
    rows: list[tuple[str, str, str | None, int]] = []
    if encrypted:
        rows.append((KEYPAIR_SECRET_KEY_CONTEXT, KeyProviderType.CONFIG.value, KEY_ID, encrypted))
    if plaintext:
        rows.append((KEYPAIR_SECRET_KEY_CONTEXT, KeyProviderType.PLAIN.value, None, plaintext))
    return rows


def status_verdicts(
    at: str,
    status: AdminSecretStatusPayload,
    *,
    write_provider: KeyProviderType,
    plaintext: int,
    encrypted: int,
) -> list[Verdict]:
    """Every place of one status answer."""
    return [
        Same(f"{at}write_provider_type", status.write_provider_type, write_provider.value),
        Same(
            f"{at}counts",
            [(one.column, one.provider_type, one.key_id, one.count) for one in status.counts],
            _counts(plaintext, encrypted),
        ),
    ]


@dataclass(frozen=True)
class TheStatusCountsWhatIsLaid(Then[AKeyringAndACaller, AdminSecretStatusPayload]):
    """심은 비밀 키를 쥔 키마다 센 집계가 온다."""

    write_provider: KeyProviderType

    @override
    def says(self) -> str:
        return "심은 비밀 키가 쥔 키마다 세어져 온다"

    @override
    def look(
        self, laid: AKeyringAndACaller, answered: Answered[AdminSecretStatusPayload]
    ) -> list[Verdict]:
        status = answered.response
        if status is None:
            return [Refused(InsufficientPrivilege, answered.raised)]
        return status_verdicts(
            "",
            status,
            write_provider=self.write_provider,
            plaintext=laid.plaintext,
            encrypted=laid.encrypted,
        )


@dataclass(frozen=True)
class EveryRowIsRewrittenOntoTheWriter(Then[AKeyringAndACaller, AdminReencryptSecretsPayload]):
    """심은 비밀 키를 모두 훑어 모두 다시 쓰고, 그 뒤의 상태는 전부 쓰기 제공자에 있다."""

    write_provider: KeyProviderType

    @override
    def says(self) -> str:
        return "모두 훑어 모두 다시 쓰고, 전부 쓰기 제공자로 옮겨진 상태가 온다"

    @override
    def look(
        self, laid: AKeyringAndACaller, answered: Answered[AdminReencryptSecretsPayload]
    ) -> list[Verdict]:
        progress = answered.response
        if progress is None:
            return [Refused(InsufficientPrivilege, answered.raised)]
        total = laid.plaintext + laid.encrypted
        onto_config = self.write_provider is KeyProviderType.CONFIG
        return [
            Same("scanned", progress.scanned, total),
            Same("reencrypted", progress.reencrypted, total),
            *status_verdicts(
                "status.",
                progress.status,
                write_provider=self.write_provider,
                plaintext=0 if onto_config else total,
                encrypted=total if onto_config else 0,
            ),
        ]
