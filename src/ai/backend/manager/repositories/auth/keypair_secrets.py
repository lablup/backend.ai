from __future__ import annotations

from ai.backend.common.auth.keypair import generate_keypair
from ai.backend.common.auth.ssh import generate_ssh_keypair
from ai.backend.manager.data.keypair.types import KeyPairSecrets
from ai.backend.manager.models.keypair.row import KEYPAIR_SECRET_KEY_CONTEXT
from ai.backend.manager.secret.pool import KeyProviderPool


async def generate_keypair_data(key_provider_pool: KeyProviderPool) -> KeyPairSecrets:
    keypair = generate_keypair()
    pubkey, privkey = generate_ssh_keypair()
    return KeyPairSecrets(
        access_key=keypair.access_key,
        secret_key=await key_provider_pool.encrypt(keypair.secret_key, KEYPAIR_SECRET_KEY_CONTEXT),
        ssh_public_key=pubkey,
        ssh_private_key=privkey,
    )
