from __future__ import annotations

import base64
import dataclasses

import pytest

from ai.backend.manager.config.unified import ConfigKeyProviderConfig, SecretEncryptionConfig
from ai.backend.manager.data.secret.types import KeyProviderType, SecretKeyId
from ai.backend.manager.errors.secret import (
    SecretDecryptionFailed,
    SecretEncryptionMisconfigured,
    UnknownSecretKeyId,
    UnknownSecretKeyProvider,
)
from ai.backend.manager.secret.config_provider import ConfigKeyProvider
from ai.backend.manager.secret.pool import KeyProviderPool
from ai.backend.manager.secret.types import EncryptedData, SecretValue, WrappedDataEncryptionKey

CONTEXT = "keypairs.secret_key"
OTHER_CONTEXT = "object_storages.secret_key"
PLAINTEXT = "AKIAIOSFODNN7EXAMPLEKEYSECRET0123456789ab"


def _key(seed: int) -> str:
    return base64.b64encode(bytes([seed]) * 32).decode()


def _provider_config(active_key_id: str = "v1", **keys: str) -> ConfigKeyProviderConfig:
    return ConfigKeyProviderConfig.model_validate({
        "active-key-id": active_key_id,
        "keys": keys or {"v1": _key(1)},
    })


@pytest.fixture
def provider() -> ConfigKeyProvider:
    return ConfigKeyProvider.from_config(_provider_config(v1=_key(1), v2=_key(2)))


@pytest.fixture
def rotated() -> ConfigKeyProvider:
    return ConfigKeyProvider.from_config(
        _provider_config(active_key_id="v2", v1=_key(1), v2=_key(2))
    )


class TestConfigKeyProvider:
    async def test_a_value_round_trips(self, provider: ConfigKeyProvider) -> None:
        data = await provider.encrypt(PLAINTEXT, CONTEXT)
        assert await provider.decrypt(data, CONTEXT) == PLAINTEXT

    async def test_the_value_names_the_provider_and_the_active_key(
        self, provider: ConfigKeyProvider
    ) -> None:
        data = await provider.encrypt(PLAINTEXT, CONTEXT)
        assert data.provider_type == ConfigKeyProvider.PROVIDER_TYPE
        assert data.wrapped_key.key_id == "v1"

    async def test_a_fresh_data_encryption_key_is_drawn_per_value(
        self, provider: ConfigKeyProvider
    ) -> None:
        first = await provider.encrypt(PLAINTEXT, CONTEXT)
        second = await provider.encrypt(PLAINTEXT, CONTEXT)
        assert first.wrapped_key.blob != second.wrapped_key.blob
        assert first.nonce != second.nonce
        assert first.ciphertext != second.ciphertext

    async def test_a_different_context_fails_authentication(
        self, provider: ConfigKeyProvider
    ) -> None:
        data = await provider.encrypt(PLAINTEXT, CONTEXT)
        with pytest.raises(SecretDecryptionFailed):
            await provider.decrypt(data, OTHER_CONTEXT)

    async def test_a_tampered_ciphertext_fails_authentication(
        self, provider: ConfigKeyProvider
    ) -> None:
        data = await provider.encrypt(PLAINTEXT, CONTEXT)
        tampered = dataclasses.replace(
            data, ciphertext=bytes([data.ciphertext[0] ^ 0x01]) + data.ciphertext[1:]
        )
        with pytest.raises(SecretDecryptionFailed):
            await provider.decrypt(tampered, CONTEXT)

    async def test_a_tampered_wrapped_key_fails_authentication(
        self, provider: ConfigKeyProvider
    ) -> None:
        data = await provider.encrypt(PLAINTEXT, CONTEXT)
        blob = data.wrapped_key.blob
        tampered = dataclasses.replace(
            data,
            wrapped_key=WrappedDataEncryptionKey(
                key_id=data.wrapped_key.key_id,
                blob=blob[:-1] + bytes([blob[-1] ^ 0x01]),
            ),
        )
        with pytest.raises(SecretDecryptionFailed):
            await provider.decrypt(tampered, CONTEXT)

    async def test_an_unconfigured_key_id_raises(self, provider: ConfigKeyProvider) -> None:
        data = await provider.encrypt(PLAINTEXT, CONTEXT)
        unknown = dataclasses.replace(
            data,
            wrapped_key=WrappedDataEncryptionKey(
                key_id=SecretKeyId("gone"), blob=data.wrapped_key.blob
            ),
        )
        with pytest.raises(UnknownSecretKeyId):
            await provider.decrypt(unknown, CONTEXT)

    async def test_a_value_written_under_an_old_key_still_decrypts(
        self, provider: ConfigKeyProvider, rotated: ConfigKeyProvider
    ) -> None:
        data = await provider.encrypt(PLAINTEXT, CONTEXT)
        assert await rotated.decrypt(data, CONTEXT) == PLAINTEXT


class TestRewrap:
    async def test_rewrap_moves_the_key_without_touching_the_ciphertext(
        self, provider: ConfigKeyProvider, rotated: ConfigKeyProvider
    ) -> None:
        data = await provider.encrypt(PLAINTEXT, CONTEXT)
        moved = await rotated.rewrap(data, CONTEXT)
        assert moved.wrapped_key.key_id == "v2"
        assert moved.wrapped_key.blob != data.wrapped_key.blob
        assert moved.nonce == data.nonce
        assert moved.ciphertext == data.ciphertext

    async def test_a_rewrapped_value_still_decrypts(
        self, provider: ConfigKeyProvider, rotated: ConfigKeyProvider
    ) -> None:
        data = await provider.encrypt(PLAINTEXT, CONTEXT)
        moved = await rotated.rewrap(data, CONTEXT)
        assert await rotated.decrypt(moved, CONTEXT) == PLAINTEXT

    async def test_rewrapping_a_value_already_on_the_active_key_changes_nothing(
        self, rotated: ConfigKeyProvider
    ) -> None:
        data = await rotated.encrypt(PLAINTEXT, CONTEXT)
        assert await rotated.rewrap(data, CONTEXT) == data


class TestKeyProviderPool:
    def _pool(self, write_provider_type: str) -> KeyProviderPool:
        return KeyProviderPool.from_config(
            SecretEncryptionConfig.model_validate({
                "write-provider-type": write_provider_type,
                "config-provider": {"active-key-id": "v1", "keys": {"v1": _key(1)}},
            })
        )

    async def test_without_a_write_provider_new_values_stay_plaintext(self) -> None:
        value = await self._pool("plain").encrypt(PLAINTEXT, CONTEXT)
        assert value.content == PLAINTEXT
        assert value.serialize() == PLAINTEXT

    async def test_with_a_write_provider_new_values_are_encrypted(self) -> None:
        value = await self._pool("config").encrypt(PLAINTEXT, CONTEXT)
        assert isinstance(value.content, EncryptedData)
        assert value.content.provider_type is KeyProviderType.CONFIG

    async def test_a_value_round_trips_through_the_pool(self) -> None:
        pool = self._pool("config")
        value = await pool.encrypt(PLAINTEXT, CONTEXT)
        assert await pool.decrypt(value, CONTEXT) == PLAINTEXT

    async def test_a_plaintext_value_reads_back_without_a_provider(self) -> None:
        pool = self._pool("plain")
        assert await pool.decrypt(SecretValue(PLAINTEXT), CONTEXT) == PLAINTEXT

    async def test_an_encrypted_value_still_reads_after_writes_go_back_to_plaintext(self) -> None:
        encrypted = await self._pool("config").encrypt(PLAINTEXT, CONTEXT)
        assert await self._pool("plain").decrypt(encrypted, CONTEXT) == PLAINTEXT

    async def test_an_unconfigured_provider_id_raises(self) -> None:
        pool = self._pool("config")
        value = await pool.encrypt(PLAINTEXT, CONTEXT)
        assert isinstance(value.content, EncryptedData)
        pool_without_provider = KeyProviderPool([], write_provider_type=KeyProviderType.PLAIN)
        with pytest.raises(UnknownSecretKeyProvider):
            await pool_without_provider.decrypt(value, CONTEXT)

    async def test_a_stored_value_naming_an_unknown_provider_type_raises(self) -> None:
        with pytest.raises(UnknownSecretKeyProvider):
            SecretValue.parse("bai-enc:1:kms:v1:AAAA:BBBB:CCCC")

    def test_omitting_a_provider_section_leaves_it_unregistered(self) -> None:
        with pytest.raises(SecretEncryptionMisconfigured):
            KeyProviderPool.from_config(
                SecretEncryptionConfig.model_validate({"write-provider-type": "config"})
            )

    def test_two_providers_sharing_an_id_are_rejected(self) -> None:
        provider = ConfigKeyProvider.from_config(_provider_config(v1=_key(1)))
        with pytest.raises(SecretEncryptionMisconfigured):
            KeyProviderPool([provider, provider], write_provider_type=KeyProviderType.PLAIN)

    async def test_rewrapping_a_plaintext_value_encrypts_it(self) -> None:
        pool = self._pool("config")
        moved = await pool.rewrap(SecretValue(PLAINTEXT), CONTEXT)
        assert isinstance(moved.content, EncryptedData)
        assert await pool.decrypt(moved, CONTEXT) == PLAINTEXT

    async def test_rewrapping_under_the_plain_write_target_returns_to_plaintext(self) -> None:
        encrypted = await self._pool("config").encrypt(PLAINTEXT, CONTEXT)
        assert await self._pool("plain").rewrap(encrypted, CONTEXT) == SecretValue(PLAINTEXT)
