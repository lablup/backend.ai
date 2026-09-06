"""The keypair secret key as a secret column: what generation writes and what a read gives back."""

from __future__ import annotations

import base64

import pytest
import sqlalchemy as sa

from ai.backend.manager.config.unified import SecretEncryptionConfig
from ai.backend.manager.models.base import SecretColumn
from ai.backend.manager.models.keypair.row import (
    KEYPAIR_SECRET_KEY_CONTEXT,
    KeyPairRow,
    generate_keypair_data,
)
from ai.backend.manager.secret.pool import KeyProviderPool
from ai.backend.manager.secret.types import EncryptedData, SecretValue

_LEGACY_SECRET_KEY = "cWbsM_vBB4CzTW7JdORRMx8SjGI3-wEXAMPLEKEY"


def _pool(write_provider_type: str) -> KeyProviderPool:
    return KeyProviderPool.from_config(
        SecretEncryptionConfig.model_validate({
            "write-provider-type": write_provider_type,
            "config-provider": {
                "active-key-id": "v1",
                "keys": {"v1": base64.b64encode(b"\x01" * 32).decode()},
            },
        })
    )


class TestTheColumn:
    def test_the_secret_key_is_a_secret_column(self) -> None:
        column = KeyPairRow.__table__.c.secret_key.type
        assert isinstance(column, SecretColumn)
        assert column.context == KEYPAIR_SECRET_KEY_CONTEXT

    def test_the_column_carries_no_length_limit(self) -> None:
        # An encrypted value exceeds the legacy 40 characters, and by how much follows
        # the key provider that wrote it.
        column = KeyPairRow.__table__.c.secret_key.type
        assert isinstance(column, SecretColumn)
        assert isinstance(column.impl_instance, sa.UnicodeText)


class TestGeneration:
    async def test_a_generated_key_is_encrypted_when_a_write_provider_is_named(self) -> None:
        secrets = await generate_keypair_data(_pool("config"))
        assert isinstance(secrets.secret_key.content, EncryptedData)
        assert secrets.secret_key.serialize().startswith("bai-enc:1:config:v1:")

    async def test_a_generated_key_is_plaintext_without_a_write_provider(self) -> None:
        secrets = await generate_keypair_data(_pool("plain"))
        assert isinstance(secrets.secret_key.content, str)
        assert secrets.secret_key.serialize() == secrets.secret_key.content

    @pytest.mark.parametrize("write_provider_type", ["plain", "config"])
    async def test_a_generated_key_reads_back_at_its_generated_length(
        self, write_provider_type: str
    ) -> None:
        pool = _pool(write_provider_type)
        secrets = await generate_keypair_data(pool)
        plaintext = await pool.decrypt(secrets.secret_key, KEYPAIR_SECRET_KEY_CONTEXT)
        assert len(plaintext) == len(_LEGACY_SECRET_KEY)

    async def test_a_generated_key_survives_serialization(self) -> None:
        pool = _pool("config")
        secrets = await generate_keypair_data(pool)
        plaintext = await pool.decrypt(secrets.secret_key, KEYPAIR_SECRET_KEY_CONTEXT)
        stored = SecretValue.parse(secrets.secret_key.serialize())
        assert await pool.decrypt(stored, KEYPAIR_SECRET_KEY_CONTEXT) == plaintext
