"""Write specs for the keypair a user authorizes with."""

from __future__ import annotations

import secrets

from bai_scenario.seeds.seeder import FieldOf

from ai.backend.common.data.entity.user import UserID
from ai.backend.common.types import AccessKey
from ai.backend.manager.data.keypair.types import KeyPairData, KeyPairSecrets
from ai.backend.manager.data.user.types import UserData
from ai.backend.manager.models.keypair.creators import DefaultKeypairCreator
from ai.backend.manager.secret.types import SecretValue


def seed_default_keypair(
    policy_name: str, *, is_admin: bool = False
) -> FieldOf[UserData, KeyPairData]:
    """The key a user authorizes with. A request that resolves the caller's keypair
    finds nothing without it."""
    token = secrets.token_hex(8).upper()
    return FieldOf(
        hint="keypair",
        owner_id=lambda user: UserID(user.id),
        spec=DefaultKeypairCreator(
            secrets=KeyPairSecrets(
                access_key=AccessKey(f"AK{token}"),
                secret_key=SecretValue(f"sk-{token}"),
                ssh_public_key="",
                ssh_private_key="",
            ),
            is_active=True,
            is_admin=is_admin,
            resource_policy=policy_name,
        ),
    )
