"""
The contract every key provider implements.

A provider decides which key id it writes under and how the data encryption key is
wrapped. The stored value names only which provider to hand it back to.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from ai.backend.manager.secret.types import EncryptedData


class KeyProvider(ABC):
    @abstractmethod
    def provider_id(self) -> str:
        """The id written into stored values, naming this provider as their reader."""
        raise NotImplementedError

    @abstractmethod
    async def encrypt(self, plaintext: str, context: str) -> EncryptedData:
        """Encrypt a new value under this provider's current key."""
        raise NotImplementedError

    @abstractmethod
    async def decrypt(self, data: EncryptedData, context: str) -> str:
        """Recover the plaintext of a value this provider wrote."""
        raise NotImplementedError

    @abstractmethod
    async def rewrap(self, data: EncryptedData, context: str) -> EncryptedData:
        """
        Move a value onto this provider's current key.

        Only the wrapped data encryption key changes, so the plaintext is never produced.
        """
        raise NotImplementedError
