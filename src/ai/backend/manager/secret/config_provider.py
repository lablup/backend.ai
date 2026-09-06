"""The key provider that reads its key encryption keys from the unified config."""

from __future__ import annotations

import base64
import binascii
from collections.abc import Mapping
from dataclasses import replace
from typing import ClassVar, Self, override

from ai.backend.manager.config.unified import ConfigKeyProviderConfig
from ai.backend.manager.data.secret.types import (
    KeyProviderType,
    SecretKeyId,
    SecretKeyMaterial,
)
from ai.backend.manager.errors.secret import InvalidSecretKeyMaterial, UnknownSecretKeyId
from ai.backend.manager.secret.keys import DataEncryptionKey, EncryptedBytes, KeyEncryptionKey
from ai.backend.manager.secret.provider import KeyProvider
from ai.backend.manager.secret.types import EncryptedData


class ConfigKeyProvider(KeyProvider):
    PROVIDER_TYPE: ClassVar[KeyProviderType] = KeyProviderType.CONFIG

    _keys: Mapping[SecretKeyId, KeyEncryptionKey]
    _active_key_id: SecretKeyId

    def __init__(
        self, keys: Mapping[SecretKeyId, KeyEncryptionKey], active_key_id: SecretKeyId
    ) -> None:
        self._keys = keys
        self._active_key_id = active_key_id

    @classmethod
    def from_config(cls, config: ConfigKeyProviderConfig) -> Self:
        keys = {
            key_id: KeyEncryptionKey(key_id=key_id, material=cls._decode(key_id, material))
            for key_id, material in config.keys.items()
        }
        return cls(keys=keys, active_key_id=config.active_key_id)

    @classmethod
    def _decode(cls, key_id: SecretKeyId, material: SecretKeyMaterial) -> bytes:
        try:
            return base64.b64decode(material, altchars=b"-_", validate=True)
        except (binascii.Error, ValueError) as e:
            raise InvalidSecretKeyMaterial(
                f"The key encryption key {key_id!r} is not valid base64."
            ) from e

    @override
    def provider_type(self) -> KeyProviderType:
        return self.PROVIDER_TYPE

    @override
    async def encrypt(self, plaintext: str, context: str) -> EncryptedData:
        dek = DataEncryptionKey.generate()
        data = dek.encrypt(plaintext, context)
        return EncryptedData(
            provider_type=self.PROVIDER_TYPE,
            wrapped_key=self._active_key().wrap(dek, context),
            nonce=data.nonce,
            ciphertext=data.ciphertext,
        )

    @override
    async def decrypt(self, data: EncryptedData, context: str) -> str:
        dek = self._key_of(data.wrapped_key.key_id).unwrap(data.wrapped_key, context)
        return dek.decrypt(EncryptedBytes(nonce=data.nonce, ciphertext=data.ciphertext), context)

    @override
    async def rewrap(self, data: EncryptedData, context: str) -> EncryptedData:
        active = self._active_key()
        if data.wrapped_key.key_id == active.key_id:
            return data
        dek = self._key_of(data.wrapped_key.key_id).unwrap(data.wrapped_key, context)
        return replace(data, wrapped_key=active.wrap(dek, context))

    def _active_key(self) -> KeyEncryptionKey:
        return self._key_of(self._active_key_id)

    def _key_of(self, key_id: SecretKeyId) -> KeyEncryptionKey:
        key = self._keys.get(key_id)
        if key is None:
            raise UnknownSecretKeyId(f"No key encryption key is configured for {key_id!r}.")
        return key
