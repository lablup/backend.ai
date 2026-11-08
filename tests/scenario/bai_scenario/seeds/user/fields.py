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
    LoginSessionStatus,
)
from ai.backend.manager.data.keypair.types import KeyPairData, KeyPairSecrets
from ai.backend.manager.data.user.types import UserData
from ai.backend.manager.models.keypair.creators import KeypairCreator
from ai.backend.manager.models.login_session.creators import (
    LoginHistoryCreator,
    LoginSessionCreator,
)
from ai.backend.manager.secret.types import SecretValue
from ai.backend.testutils.scenario_steps import Language, Says, in_language
from bai_scenario.seeds.seeder import TestSeedFieldCreator


@dataclass(frozen=True)
class TestSeedKeypairOf(TestSeedFieldCreator[UserData, KeyPairData]):
    """A keypair besides the one the user authorizes with.

    The policy name is a value an earlier row answered; this seed names none of its own.
    """

    resource_policy: str
    is_active: bool = True

    @override
    def kind(self) -> str:
        state = (
            Says("활성", english="active") if self.is_active else Says("비활성", english="inactive")
        )
        return Says(
            f"기본이 아닌 {state} 키페어 하나를 더 갖습니다",
            english=(
                f"has one more {in_language(state, Language.ENGLISH)} keypair "
                "besides the default one"
            ),
        )

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
class TestSeedLoginSessionOf(TestSeedFieldCreator[UserData, LoginSessionData]):
    """A login the user holds, made with the key an earlier row answered."""

    access_key: str
    status: LoginSessionStatus = LoginSessionStatus.ACTIVE

    @override
    def kind(self) -> str:
        return Says(
            f"상태가 {self.status.value} 인 로그인 세션 하나를 갖습니다",
            english=f"has one login session in status {self.status.value}",
        )

    @override
    def owner_id(self, owner: UserData) -> UserID:
        return UserID(owner.id)

    @override
    def seed(self) -> LoginSessionCreator:
        return LoginSessionCreator(
            session_token=secrets.token_hex(16), access_key=self.access_key, status=self.status
        )


@dataclass(frozen=True)
class TestSeedLoginHistoryOf(TestSeedFieldCreator[UserData, LoginHistoryData]):
    """The record one successful login of the user left, under the user's own domain."""

    domain_name: str

    @override
    def kind(self) -> str:
        return Says(
            "성공한 로그인 이력 하나를 갖습니다",
            english="has one successful login record",
        )

    @override
    def owner_id(self, owner: UserData) -> UserID:
        return UserID(owner.id)

    @override
    def seed(self) -> LoginHistoryCreator:
        return LoginHistoryCreator(domain_name=self.domain_name, result=LoginAttemptResult.SUCCESS)
