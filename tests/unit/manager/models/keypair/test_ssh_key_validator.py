from __future__ import annotations

from collections.abc import Callable

import pytest
from cryptography.hazmat.primitives import serialization as crypto_serialization
from cryptography.hazmat.primitives.asymmetric import ec, ed25519, rsa
from cryptography.hazmat.primitives.asymmetric.types import PublicKeyTypes

from ai.backend.common.types import SSHPublicKey
from ai.backend.manager.errors.keypair import InvalidSSHPublicKey
from ai.backend.manager.models.keypair.ssh_key_validator import SSHKeyValidator

PublicKeyFactory = Callable[[], SSHPublicKey]


def _openssh_public_key(key: PublicKeyTypes) -> SSHPublicKey:
    return SSHPublicKey(
        key.public_bytes(
            crypto_serialization.Encoding.OpenSSH, crypto_serialization.PublicFormat.OpenSSH
        ).decode("utf-8")
    )


def rsa_public_key() -> SSHPublicKey:
    return _openssh_public_key(
        rsa.generate_private_key(public_exponent=65537, key_size=2048).public_key()
    )


def ed25519_public_key() -> SSHPublicKey:
    return _openssh_public_key(ed25519.Ed25519PrivateKey.generate().public_key())


def ecdsa_public_key() -> SSHPublicKey:
    return _openssh_public_key(ec.generate_private_key(ec.SECP256R1()).public_key())


class TestSSHKeyValidatorValidPublicKeys:
    @pytest.mark.parametrize(
        "factory",
        [
            rsa_public_key,
            ed25519_public_key,
            ecdsa_public_key,
        ],
    )
    def test_public_key_passes(self, factory: PublicKeyFactory) -> None:
        # Should not raise.
        SSHKeyValidator().validate(factory())


class TestSSHKeyValidatorPublicKeyFormat:
    def test_garbage_public_key_raises(self) -> None:
        with pytest.raises(InvalidSSHPublicKey):
            SSHKeyValidator().validate(SSHPublicKey("not-a-public-key"))
