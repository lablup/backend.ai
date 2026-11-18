from __future__ import annotations

from typing import Protocol

from cryptography.exceptions import UnsupportedAlgorithm
from cryptography.hazmat.primitives import serialization as crypto_serialization
from cryptography.hazmat.primitives.asymmetric.types import PublicKeyTypes

from ai.backend.common.types import SSHPublicKey
from ai.backend.manager.errors.keypair import InvalidSSHPublicKey


class PublicKeyLoader(Protocol):
    def __call__(self, data: bytes) -> PublicKeyTypes: ...


DEFAULT_PUBLIC_KEY_LOADER: PublicKeyLoader = crypto_serialization.load_ssh_public_key


class SSHKeyValidator:
    """
    Validate an SSH public key used for SSH/SFTP connections.

    The accepted format is determined by the injected loader. By default the public
    key is accepted in the OpenSSH single-line format (e.g. ``ssh-ed25519 AAAA...``).
    """

    _public_key_loader: PublicKeyLoader

    def __init__(
        self,
        public_key_loader: PublicKeyLoader = DEFAULT_PUBLIC_KEY_LOADER,
    ) -> None:
        self._public_key_loader = public_key_loader

    def validate(self, public_key: SSHPublicKey) -> None:
        """
        Validate that the public key is well-formed.

        :raises InvalidSSHPublicKey: the public key cannot be parsed.
        """
        self._load_public_key(public_key)

    def _load_public_key(self, public_key: SSHPublicKey) -> PublicKeyTypes:
        try:
            return self._public_key_loader(public_key.encode())
        except (ValueError, UnsupportedAlgorithm) as e:
            raise InvalidSSHPublicKey("Invalid public key format") from e
