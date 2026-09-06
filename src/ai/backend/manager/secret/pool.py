"""
The set of configured key providers, plus which one writes.

Reads route by the provider id the stored value names; writes go to the one provider
designated for them. Without a write provider, new values are stored as plaintext.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from ai.backend.manager.config.unified import SecretEncryptionConfig
from ai.backend.manager.data.secret.types import KeyProviderType, SecretKeyId
from ai.backend.manager.errors.secret import (
    SecretEncryptionMisconfigured,
    UnknownSecretKeyProvider,
)
from ai.backend.manager.secret.config_provider import ConfigKeyProvider
from ai.backend.manager.secret.provider import KeyProvider
from ai.backend.manager.secret.types import EncryptedData, SecretValue


class KeyProviderPool:
    _providers: Mapping[KeyProviderType, KeyProvider]
    _writer: KeyProvider | None

    def __init__(
        self, providers: Sequence[KeyProvider], write_provider_type: KeyProviderType
    ) -> None:
        self._providers = {provider.provider_type(): provider for provider in providers}
        if len(self._providers) != len(providers):
            raise SecretEncryptionMisconfigured("Two key providers share a provider type.")
        if write_provider_type is KeyProviderType.PLAIN:
            self._writer = None
            return
        writer = self._providers.get(write_provider_type)
        if writer is None:
            raise SecretEncryptionMisconfigured(
                f"The write key provider {write_provider_type.value!r} is not configured."
            )
        self._writer = writer

    @classmethod
    def from_config(cls, config: SecretEncryptionConfig) -> KeyProviderPool:
        providers: list[KeyProvider] = []
        if config.config_provider is not None:
            providers.append(ConfigKeyProvider.from_config(config.config_provider))
        return cls(providers=providers, write_provider_type=config.write_provider_type)

    def write_provider_type(self) -> KeyProviderType:
        """The provider type new and re-encrypted secrets are written through."""
        if self._writer is None:
            return KeyProviderType.PLAIN
        return self._writer.provider_type()

    def holder_of(self, value: SecretValue) -> tuple[KeyProviderType, SecretKeyId | None]:
        """The provider and key a stored value is held by; plaintext names neither."""
        match value.content:
            case EncryptedData() as data:
                return data.provider_type, data.wrapped_key.key_id
            case _:
                return KeyProviderType.PLAIN, None

    async def reencrypt(self, value: SecretValue, context: str) -> SecretValue:
        """Encrypt the value again through the write provider, under a fresh data
        encryption key. A write target of plaintext returns it to plaintext."""
        return await self.encrypt(await self.decrypt(value, context), context)

    async def encrypt(self, plaintext: str, context: str) -> SecretValue:
        if self._writer is None:
            return SecretValue(plaintext)
        return SecretValue(await self._writer.encrypt(plaintext, context))

    async def decrypt(self, value: SecretValue, context: str) -> str:
        match value.content:
            case EncryptedData() as data:
                return await self._provider_of(data).decrypt(data, context)
            case plaintext:
                return plaintext

    async def rewrap(self, value: SecretValue, context: str) -> SecretValue:
        """
        Move a value onto the write provider's current key.

        Within one provider only the wrapped data encryption key changes. Moving between
        providers, encrypting a plaintext value, or going back to plaintext needs the
        plaintext.
        """
        if self._writer is None:
            # The write target is plaintext, so encrypted values come back to plaintext.
            return SecretValue(await self.decrypt(value, context))
        match value.content:
            case EncryptedData() as data if data.provider_type == self._writer.provider_type():
                return SecretValue(await self._writer.rewrap(data, context))
            case _:
                return await self.encrypt(await self.decrypt(value, context), context)

    def _provider_of(self, data: EncryptedData) -> KeyProvider:
        provider = self._providers.get(data.provider_type)
        if provider is None:
            raise UnknownSecretKeyProvider(
                f"No key provider of type {data.provider_type.value!r} is configured."
            )
        return provider
