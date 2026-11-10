"""
End-to-end checks for a secret column.

Every case goes through the column's own hooks, so a value is encrypted, turned into
the string a column stores, read back from that string, and only then decrypted.
"""

from __future__ import annotations

import base64

import pytest
import sqlalchemy as sa
from sqlalchemy.engine.default import DefaultDialect
from sqlalchemy.engine.interfaces import Dialect

from ai.backend.manager.config.unified import SecretEncryptionConfig
from ai.backend.manager.data.secret.types import KeyProviderType
from ai.backend.manager.errors.secret import InvalidSecretBinding, SecretDecryptionFailed
from ai.backend.manager.models.base import SecretColumn
from ai.backend.manager.secret.pool import KeyProviderPool
from ai.backend.manager.secret.types import EncryptedData, SecretValue

CONTEXT = "keypairs.secret_key"
OTHER_CONTEXT = "object_storages.secret_key"
PLAINTEXT = "AKIAIOSFODNN7EXAMPLEKEYSECRET0123456789ab"


def _key(seed: int) -> str:
    return base64.b64encode(bytes([seed]) * 32).decode()


def _pool(write_provider_type: str, active_key_id: str = "v1") -> KeyProviderPool:
    return KeyProviderPool.from_config(
        SecretEncryptionConfig.model_validate({
            "write-provider-type": write_provider_type,
            "config-provider": {
                "active-key-id": active_key_id,
                "keys": {"v1": _key(1), "v2": _key(2)},
            },
        })
    )


@pytest.fixture
def dialect() -> Dialect:
    return DefaultDialect()


@pytest.fixture
def column() -> SecretColumn:
    return SecretColumn(CONTEXT)


def _store(column: SecretColumn, dialect: Dialect, value: SecretValue) -> str:
    """Bind a value the way an INSERT would, and return what the column writes."""
    stored = column.process_bind_param(value, dialect)
    assert stored is not None
    return stored


def _load(column: SecretColumn, dialect: Dialect, stored: str) -> SecretValue:
    """Read a stored string back the way a SELECT would."""
    loaded = column.process_result_value(stored, dialect)
    assert loaded is not None
    return loaded


class TestThroughTheColumn:
    async def test_an_encrypted_value_survives_a_write_and_a_read(
        self, column: SecretColumn, dialect: Dialect
    ) -> None:
        pool = _pool("config")
        stored = _store(column, dialect, await pool.encrypt(PLAINTEXT, CONTEXT))
        assert stored.startswith("bai-enc:1:config:v1:")
        assert PLAINTEXT not in stored
        assert await pool.decrypt(_load(column, dialect, stored), CONTEXT) == PLAINTEXT

    async def test_a_plaintext_value_survives_a_write_and_a_read(
        self, column: SecretColumn, dialect: Dialect
    ) -> None:
        pool = _pool("plain")
        stored = _store(column, dialect, await pool.encrypt(PLAINTEXT, CONTEXT))
        assert stored == PLAINTEXT
        assert await pool.decrypt(_load(column, dialect, stored), CONTEXT) == PLAINTEXT

    async def test_a_legacy_row_reads_back_as_its_plaintext(
        self, column: SecretColumn, dialect: Dialect
    ) -> None:
        pool = _pool("config")
        assert await pool.decrypt(_load(column, dialect, PLAINTEXT), CONTEXT) == PLAINTEXT

    async def test_two_writes_of_one_plaintext_are_stored_differently(
        self, column: SecretColumn, dialect: Dialect
    ) -> None:
        pool = _pool("config")
        first = _store(column, dialect, await pool.encrypt(PLAINTEXT, CONTEXT))
        second = _store(column, dialect, await pool.encrypt(PLAINTEXT, CONTEXT))
        assert first != second
        assert await pool.decrypt(_load(column, dialect, first), CONTEXT) == PLAINTEXT
        assert await pool.decrypt(_load(column, dialect, second), CONTEXT) == PLAINTEXT

    async def test_a_value_stored_before_a_key_rotation_still_reads(
        self, column: SecretColumn, dialect: Dialect
    ) -> None:
        stored = _store(column, dialect, await _pool("config", "v1").encrypt(PLAINTEXT, CONTEXT))
        rotated = _pool("config", "v2")
        assert await rotated.decrypt(_load(column, dialect, stored), CONTEXT) == PLAINTEXT

    async def test_a_value_read_under_another_column_fails_authentication(
        self, column: SecretColumn, dialect: Dialect
    ) -> None:
        pool = _pool("config")
        stored = _store(column, dialect, await pool.encrypt(PLAINTEXT, CONTEXT))
        with pytest.raises(SecretDecryptionFailed):
            await pool.decrypt(_load(column, dialect, stored), OTHER_CONTEXT)


class TestRewrapThroughTheColumn:
    async def test_a_rewrapped_value_survives_a_write_and_a_read(
        self, column: SecretColumn, dialect: Dialect
    ) -> None:
        stored = _store(column, dialect, await _pool("config", "v1").encrypt(PLAINTEXT, CONTEXT))
        rotated = _pool("config", "v2")

        rewrapped = _store(
            column, dialect, await rotated.rewrap(_load(column, dialect, stored), CONTEXT)
        )

        assert rewrapped.startswith("bai-enc:1:config:v2:")
        assert await rotated.decrypt(_load(column, dialect, rewrapped), CONTEXT) == PLAINTEXT

    async def test_rewrapping_leaves_the_ciphertext_alone(
        self, column: SecretColumn, dialect: Dialect
    ) -> None:
        before = _load(
            column,
            dialect,
            _store(column, dialect, await _pool("config", "v1").encrypt(PLAINTEXT, CONTEXT)),
        )
        after = _load(
            column,
            dialect,
            _store(column, dialect, await _pool("config", "v2").rewrap(before, CONTEXT)),
        )
        assert isinstance(before.content, EncryptedData)
        assert isinstance(after.content, EncryptedData)
        assert after.content.nonce == before.content.nonce
        assert after.content.ciphertext == before.content.ciphertext
        assert after.content.wrapped_key.blob != before.content.wrapped_key.blob

    async def test_a_plaintext_row_rewraps_into_an_encrypted_one(
        self, column: SecretColumn, dialect: Dialect
    ) -> None:
        pool = _pool("config")
        rewrapped = _store(
            column, dialect, await pool.rewrap(_load(column, dialect, PLAINTEXT), CONTEXT)
        )
        assert rewrapped.startswith("bai-enc:1:config:v1:")
        assert await pool.decrypt(_load(column, dialect, rewrapped), CONTEXT) == PLAINTEXT

    async def test_an_encrypted_row_rewraps_back_to_plaintext(
        self, column: SecretColumn, dialect: Dialect
    ) -> None:
        stored = _store(column, dialect, await _pool("config").encrypt(PLAINTEXT, CONTEXT))
        plain_pool = _pool("plain")

        rewrapped = _store(
            column, dialect, await plain_pool.rewrap(_load(column, dialect, stored), CONTEXT)
        )

        assert rewrapped == PLAINTEXT
        assert await plain_pool.decrypt(_load(column, dialect, rewrapped), CONTEXT) == PLAINTEXT


class TestBinding:
    def test_a_bare_string_is_refused(self, column: SecretColumn, dialect: Dialect) -> None:
        with pytest.raises(InvalidSecretBinding):
            column.process_bind_param(PLAINTEXT, dialect)

    def test_a_bare_encrypted_value_is_refused(
        self, column: SecretColumn, dialect: Dialect
    ) -> None:
        with pytest.raises(InvalidSecretBinding):
            column.process_bind_param({"provider_type": KeyProviderType.CONFIG}, dialect)

    def test_none_passes_through(self, column: SecretColumn, dialect: Dialect) -> None:
        assert column.process_bind_param(None, dialect) is None
        assert column.process_result_value(None, dialect) is None

    def test_the_column_stores_text(self, column: SecretColumn) -> None:
        assert isinstance(column.impl_instance, sa.UnicodeText)

    def test_the_column_carries_the_context_callers_encrypt_under(
        self, column: SecretColumn
    ) -> None:
        assert column.context == CONTEXT

    def test_columns_of_different_contexts_do_not_share_a_cache_key(self) -> None:
        # Sharing one would let a compiled statement bind a value under the wrong
        # associated data.
        assert (
            SecretColumn(CONTEXT)._static_cache_key != SecretColumn(OTHER_CONTEXT)._static_cache_key
        )
