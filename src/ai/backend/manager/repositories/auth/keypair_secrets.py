from __future__ import annotations

import base64
import secrets

from ai.backend.common.auth.ssh import generate_ssh_keypair
from ai.backend.common.types import AccessKey, SecretKey
from ai.backend.manager.data.keypair.types import KeyPairSecrets
from ai.backend.manager.models.keypair.row import KEYPAIR_SECRET_KEY_CONTEXT
from ai.backend.manager.secret.pool import KeyProviderPool


def generate_keypair() -> tuple[AccessKey, SecretKey]:
    """
    AWS-like access key and secret key generation.
    """
    ak = "AKIA" + base64.b32encode(secrets.token_bytes(10)).decode("ascii")
    sk = secrets.token_urlsafe(30)
    return AccessKey(ak), SecretKey(sk)


async def generate_keypair_data(key_provider_pool: KeyProviderPool) -> KeyPairSecrets:
    ak, sk = generate_keypair()
    pubkey, privkey = generate_ssh_keypair()
    return KeyPairSecrets(
        access_key=ak,
        secret_key=await key_provider_pool.encrypt(sk, KEYPAIR_SECRET_KEY_CONTEXT),
        ssh_public_key=pubkey,
        ssh_private_key=privkey,
    )
