"""Write specs for a keypair a user holds besides the one made with them."""

from __future__ import annotations

import secrets
from dataclasses import dataclass
from typing import override

from bai_scenario.seeds.seeder import SeedField

from ai.backend.common.data.entity.user import UserID
from ai.backend.common.types import AccessKey
from ai.backend.manager.data.keypair.types import KeyPairData, KeyPairSecrets
from ai.backend.manager.data.user.types import UserData
from ai.backend.manager.models.keypair.creators import KeypairCreator
from ai.backend.manager.secret.types import SecretValue


@dataclass(frozen=True)
class SeedKeypair(SeedField[UserData, KeyPairData]):
    """One more keypair under a user, held to the named policy.

    The one made with the user carries the default marker; this one never does, so
    what a scenario sees through it depends on that marker and on which keys are active.
    """

    resource_policy: str
    active: bool = True

    @override
    def kind(self) -> str:
        state = "활성" if self.active else "비활성"
        return f"{self.resource_policy}에 매인 {state} 키 하나 더"

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
            is_active=self.active,
            is_admin=False,
            resource_policy=self.resource_policy,
        )
