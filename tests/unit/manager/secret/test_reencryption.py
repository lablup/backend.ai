"""The stored secret re-encryption pass: what it writes and what it reports.

The fake ops stand in for one encrypted column, which is what the catalog holds today.
"""

from __future__ import annotations

import base64
from collections.abc import AsyncGenerator, MutableMapping, Sequence
from contextlib import asynccontextmanager
from typing import Any, override

import pytest

from ai.backend.common.types import AccessKey
from ai.backend.manager.config.unified import SecretEncryptionConfig
from ai.backend.manager.data.secret.types import KeyProviderType
from ai.backend.manager.repositories.ops.v2.secret.provider import SecretOpsProvider
from ai.backend.manager.repositories.ops.v2.secret.read import (
    SecretReadOps,
    SecretTarget,
    StoredSecret,
)
from ai.backend.manager.repositories.ops.v2.secret.write import SecretWriteOps
from ai.backend.manager.repositories.secret.db_source.db_source import _CHUNK_SIZE
from ai.backend.manager.repositories.secret.repository import SecretRepository
from ai.backend.manager.secret.pool import KeyProviderPool
from ai.backend.manager.secret.types import EncryptedData, SecretValue

_KEY_V1 = base64.b64encode(b"\x01" * 32).decode()
_KEY_V2 = base64.b64encode(b"\x02" * 32).decode()
_CONTEXT = "keypairs.secret_key"


def _pool(write_provider_type: str, active_key_id: str = "v1") -> KeyProviderPool:
    return KeyProviderPool.from_config(
        SecretEncryptionConfig.model_validate({
            "write-provider-type": write_provider_type,
            "config-provider": {
                "active-key-id": active_key_id,
                "keys": {"v1": _KEY_V1, "v2": _KEY_V2},
            },
        })
    )


class _FakeWriteOps(SecretWriteOps):
    """The two pass primitives over an in-memory column."""

    _store: MutableMapping[AccessKey, str]

    def __init__(self, store: MutableMapping[AccessKey, str]) -> None:
        self._store = store

    @override
    async def scan_secrets(
        self, target: SecretTarget, after: Any | None, limit: int
    ) -> Sequence[StoredSecret]:
        keys = sorted(key for key in self._store if after is None or key > after)
        return [
            StoredSecret(key=key, value=SecretValue.parse(self._store[key])) for key in keys[:limit]
        ]

    @override
    async def rewrite_secret(
        self, target: SecretTarget, key: Any, expected: SecretValue, replacement: SecretValue
    ) -> bool:
        if self._store.get(key) != expected.serialize():
            return False
        self._store[key] = replacement.serialize()
        return True


class _FakeOpsProvider(SecretOpsProvider):
    _store: MutableMapping[AccessKey, str]

    def __init__(self, store: MutableMapping[AccessKey, str]) -> None:
        self._store = store

    @asynccontextmanager
    @override
    async def read_ops(self) -> AsyncGenerator[SecretReadOps]:
        yield _FakeWriteOps(self._store)

    @asynccontextmanager
    @override
    async def write_ops(self) -> AsyncGenerator[SecretWriteOps]:
        yield _FakeWriteOps(self._store)


async def _encrypted(pool: KeyProviderPool, plaintext: str) -> str:
    return (await pool.encrypt(plaintext, _CONTEXT)).serialize()


class TestReencryption:
    async def test_plaintext_rows_are_encrypted_under_the_active_key(self) -> None:
        store: dict[AccessKey, str] = {AccessKey("AKIA1"): "sk-one", AccessKey("AKIA2"): "sk-two"}
        pool = _pool("config", "v1")
        repository = SecretRepository(_FakeOpsProvider(store), pool)

        progress = await repository.reencrypt()

        assert (progress.scanned, progress.reencrypted) == (2, 2)
        for stored in store.values():
            assert stored.startswith("bai-enc:1:config:v1:")

    async def test_a_row_already_on_the_active_key_is_encrypted_again(self) -> None:
        pool = _pool("config", "v1")
        before = SecretValue.parse(await _encrypted(pool, "sk-one"))
        assert isinstance(before.content, EncryptedData)
        store: dict[AccessKey, str] = {AccessKey("AKIA1"): before.serialize()}
        repository = SecretRepository(_FakeOpsProvider(store), pool)

        progress = await repository.reencrypt()

        after = SecretValue.parse(store[AccessKey("AKIA1")])
        assert isinstance(after.content, EncryptedData)
        assert progress.reencrypted == 1
        # A fresh data encryption key per write, so nothing of the stored value survives.
        assert after.content.ciphertext != before.content.ciphertext
        assert after.content.nonce != before.content.nonce
        assert after.content.wrapped_key.blob != before.content.wrapped_key.blob
        assert await pool.decrypt(after, _CONTEXT) == "sk-one"

    async def test_a_row_on_an_older_key_moves_to_the_active_one(self) -> None:
        store: dict[AccessKey, str] = {
            AccessKey("AKIA1"): await _encrypted(_pool("config", "v1"), "sk-one")
        }
        pool = _pool("config", "v2")

        await SecretRepository(_FakeOpsProvider(store), pool).reencrypt()

        moved = SecretValue.parse(store[AccessKey("AKIA1")])
        assert isinstance(moved.content, EncryptedData)
        assert moved.content.wrapped_key.key_id == "v2"
        assert await pool.decrypt(moved, _CONTEXT) == "sk-one"

    async def test_the_plain_target_returns_stored_secrets_to_plaintext(self) -> None:
        store: dict[AccessKey, str] = {
            AccessKey("AKIA1"): await _encrypted(_pool("config", "v1"), "sk-one")
        }
        repository = SecretRepository(_FakeOpsProvider(store), _pool("plain"))

        progress = await repository.reencrypt()

        assert progress.reencrypted == 1
        assert store[AccessKey("AKIA1")] == "sk-one"

    async def test_a_keypair_reissued_mid_pass_keeps_its_new_secret(self) -> None:
        store: dict[AccessKey, str] = {AccessKey("AKIA1"): "sk-old"}
        pool = _pool("config", "v1")

        class _ReissuingOps(_FakeWriteOps):
            @override
            async def rewrite_secret(
                self,
                target: SecretTarget,
                key: Any,
                expected: SecretValue,
                replacement: SecretValue,
            ) -> bool:
                # The keypair is reissued between the read and the write.
                store[key] = "sk-new"
                return await super().rewrite_secret(target, key, expected, replacement)

        class _ReissuingProvider(_FakeOpsProvider):
            @asynccontextmanager
            @override
            async def write_ops(self) -> AsyncGenerator[SecretWriteOps]:
                yield _ReissuingOps(store)

        progress = await SecretRepository(_ReissuingProvider(store), pool).reencrypt()

        assert progress.reencrypted == 0
        assert store[AccessKey("AKIA1")] == "sk-new"

    async def test_a_column_longer_than_one_chunk_is_read_whole(self) -> None:
        store: dict[AccessKey, str] = {
            AccessKey(f"AKIA{index:04d}"): f"sk-{index}" for index in range(_CHUNK_SIZE + 3)
        }
        repository = SecretRepository(_FakeOpsProvider(store), _pool("config", "v1"))

        progress = await repository.reencrypt()

        assert (progress.scanned, progress.reencrypted) == (len(store), len(store))


class TestStatus:
    async def test_the_counts_are_grouped_by_the_key_holding_each_value(self) -> None:
        store: dict[AccessKey, str] = {
            AccessKey("AKIA1"): "sk-one",
            AccessKey("AKIA2"): await _encrypted(_pool("config", "v1"), "sk-two"),
            AccessKey("AKIA3"): await _encrypted(_pool("config", "v2"), "sk-three"),
        }
        status = await SecretRepository(_FakeOpsProvider(store), _pool("config", "v2")).status()

        assert status.write_provider_type is KeyProviderType.CONFIG
        assert [
            (count.column, count.provider_type, count.key_id, count.count)
            for count in status.counts
        ] == [
            (_CONTEXT, KeyProviderType.CONFIG, "v1", 1),
            (_CONTEXT, KeyProviderType.CONFIG, "v2", 1),
            (_CONTEXT, KeyProviderType.PLAIN, None, 1),
        ]

    @pytest.mark.parametrize("write_provider_type", ["plain", "config"])
    async def test_a_pass_leaves_every_value_on_the_write_provider(
        self, write_provider_type: str
    ) -> None:
        store: dict[AccessKey, str] = {AccessKey("AKIA1"): "sk-one", AccessKey("AKIA2"): "sk-two"}
        repository = SecretRepository(_FakeOpsProvider(store), _pool(write_provider_type))

        progress = await repository.reencrypt()

        assert [count.provider_type for count in progress.status.counts] == [
            KeyProviderType(write_provider_type)
        ]
