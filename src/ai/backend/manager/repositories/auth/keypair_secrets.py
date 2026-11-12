from __future__ import annotations

from ai.backend.common.auth.keypair import generate_keypair
from ai.backend.common.auth.ssh import generate_ssh_keypair
from ai.backend.manager.data.keypair.types import KeyPairSecrets
from ai.backend.manager.data.ssh_keypair.types import SSHKeypairSecrets
from ai.backend.manager.models.keypair.row import KEYPAIR_SECRET_KEY_CONTEXT
from ai.backend.manager.models.ssh_keypair.row import SSH_KEYPAIR_PRIVATE_KEY_CONTEXT
from ai.backend.manager.secret.pool import KeyProviderPool


async def generate_keypair_data(key_provider_pool: KeyProviderPool) -> KeyPairSecrets:
    keypair = generate_keypair()
    return KeyPairSecrets(
        access_key=keypair.access_key,
        secret_key=await key_provider_pool.encrypt(keypair.secret_key, KEYPAIR_SECRET_KEY_CONTEXT),
    )


async def generate_ssh_keypair_data(key_provider_pool: KeyProviderPool) -> SSHKeypairSecrets:
    public_key, private_key = generate_ssh_keypair()
    return SSHKeypairSecrets(
        public_key=public_key,
        private_key=await key_provider_pool.encrypt(private_key, SSH_KEYPAIR_PRIVATE_KEY_CONTEXT),
    )
