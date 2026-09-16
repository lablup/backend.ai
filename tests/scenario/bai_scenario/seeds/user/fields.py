"""Write specs for the rows a user owns besides the ones provisioning writes.

Provisioning already writes the keypair a user authorizes with. These lay what comes
after it: another keypair, a login, and the record a login attempt leaves.
"""

from __future__ import annotations

import secrets
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.user import UserID
from ai.backend.common.types import AccessKey
from ai.backend.manager.data.auth.login_session_types import (
    LoginAttemptResult,
    LoginHistoryData,
    LoginSessionData,
)
from ai.backend.manager.data.keypair.types import KeyPairData, KeyPairSecrets
from ai.backend.manager.data.user.types import UserData
from ai.backend.manager.models.keypair.creators import KeypairCreator
from ai.backend.manager.models.login_session.creators import (
    LoginHistoryCreator,
    LoginSessionCreator,
)
from ai.backend.manager.secret.types import SecretValue
from bai_scenario.seeds.seeder import SeedField


@dataclass(frozen=True)
class SeedKeypairOf(SeedField[UserData, KeyPairData]):
    """A keypair besides the one the user authorizes with.

    The policy name is a value an earlier row answered; this seed names none of its own.
    """

    resource_policy: str
    is_active: bool = True

    @override
    def kind(self) -> str:
        state = "활성" if self.is_active else "비활성"
        return f"기본이 아닌 {state} 키 하나를 더 갖는다"

    @override
    def owner_id(self, owner: UserData) -> UserID:
        return UserID(owner.id)

    @override
    def seed(self) -> KeypairCreator:
        token = secrets.token_hex(8).upper()
        return KeypairCreator(
            secrets=KeyPairSecrets(
                access_key=AccessKey(f"AK{token}"),
                secret_key=SecretValue(f"sk-{token}"),
                ssh_public_key="",
                ssh_private_key="",
            ),
            is_active=self.is_active,
            is_admin=False,
            resource_policy=self.resource_policy,
        )


@dataclass(frozen=True)
class SeedLoginSessionOf(SeedField[UserData, LoginSessionData]):
    """A login the user holds, made with the key an earlier row answered."""

    access_key: str

    @override
    def kind(self) -> str:
        return "활성 로그인 세션 하나를 갖는다"

    @override
    def owner_id(self, owner: UserData) -> UserID:
        return UserID(owner.id)

    @override
    def seed(self) -> LoginSessionCreator:
        return LoginSessionCreator(session_token=secrets.token_hex(16), access_key=self.access_key)


@dataclass(frozen=True)
class SeedLoginHistoryOf(SeedField[UserData, LoginHistoryData]):
    """The record one successful login of the user left, under the user's own domain."""

    domain_name: str

    @override
    def kind(self) -> str:
        return "성공한 로그인 기록 하나를 갖는다"

    @override
    def owner_id(self, owner: UserData) -> UserID:
        return UserID(owner.id)

    @override
    def seed(self) -> LoginHistoryCreator:
        return LoginHistoryCreator(domain_name=self.domain_name, result=LoginAttemptResult.SUCCESS)
