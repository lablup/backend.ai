"""
The two key kinds an envelope key provider works with.

A data encryption key encrypts one stored value; a key encryption key wraps data
encryption keys. Neither leaves the provider that holds it.
"""

from __future__ import annotations

import secrets
from dataclasses import dataclass, field
from typing import Final, Self

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from ai.backend.manager.data.secret.types import SecretKeyId
from ai.backend.manager.errors.secret import (
    InvalidSecretKeyMaterial,
    SecretDecryptionFailed,
)
from ai.backend.manager.secret.types import WrappedDataEncryptionKey

KEY_SIZE: Final[int] = 32

# The size a newly drawn nonce gets. Stored values carry their own nonce, so changing
# this only affects values written afterwards.
_NONCE_SIZE: Final[int] = 12


@dataclass(frozen=True)
class EncryptedBytes:
    """What one encryption produced: the nonce it drew, and the ciphertext with its tag."""

    nonce: bytes = field(repr=False)
    ciphertext: bytes = field(repr=False)


@dataclass(frozen=True)
class DataEncryptionKey:
    """The key one stored value is encrypted with. Lives in memory only."""

    material: bytes = field(repr=False)

    def __post_init__(self) -> None:
        if len(self.material) != KEY_SIZE:
            raise InvalidSecretKeyMaterial(
                f"A data encryption key must be {KEY_SIZE} bytes but got {len(self.material)}."
            )

    @classmethod
    def generate(cls) -> Self:
        return cls(material=secrets.token_bytes(KEY_SIZE))

    def encrypt(self, plaintext: str, context: str) -> EncryptedBytes:
        nonce = secrets.token_bytes(_NONCE_SIZE)
        ciphertext = AESGCM(self.material).encrypt(
            nonce, plaintext.encode("utf-8"), context.encode("utf-8")
        )
        return EncryptedBytes(nonce=nonce, ciphertext=ciphertext)

    def decrypt(self, data: EncryptedBytes, context: str) -> str:
        try:
            plaintext = AESGCM(self.material).decrypt(
                data.nonce, data.ciphertext, context.encode("utf-8")
            )
        except InvalidTag as e:
            raise SecretDecryptionFailed(
                "The authentication tag of the secret did not verify."
            ) from e
        return plaintext.decode("utf-8")


@dataclass(frozen=True)
class KeyEncryptionKey:
    """A versioned key that wraps data encryption keys. Never encrypts a stored value."""

    key_id: SecretKeyId
    material: bytes = field(repr=False)

    def __post_init__(self) -> None:
        if not self.key_id:
            raise InvalidSecretKeyMaterial("A key encryption key must have a key id.")
        if len(self.material) != KEY_SIZE:
            raise InvalidSecretKeyMaterial(
                f"The key encryption key {self.key_id!r} must be {KEY_SIZE} bytes "
                f"but got {len(self.material)}."
            )

    def wrap(self, dek: DataEncryptionKey, context: str) -> WrappedDataEncryptionKey:
        nonce = secrets.token_bytes(_NONCE_SIZE)
        wrapped = AESGCM(self.material).encrypt(nonce, dek.material, context.encode("utf-8"))
        return WrappedDataEncryptionKey(key_id=self.key_id, blob=nonce + wrapped)

    def unwrap(self, wrapped: WrappedDataEncryptionKey, context: str) -> DataEncryptionKey:
        blob = wrapped.blob
        if len(blob) <= _NONCE_SIZE:
            raise SecretDecryptionFailed(
                f"The wrapped data encryption key is {len(blob)} bytes, too short to unwrap."
            )
        try:
            material = AESGCM(self.material).decrypt(
                blob[:_NONCE_SIZE], blob[_NONCE_SIZE:], context.encode("utf-8")
            )
        except InvalidTag as e:
            raise SecretDecryptionFailed(
                f"The data encryption key wrapped by {self.key_id!r} did not verify."
            ) from e
        return DataEncryptionKey(material=material)
