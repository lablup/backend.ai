from __future__ import annotations

import random
from uuid import uuid4

import pytest

from ai.backend.common.clients.valkey_client.valkey_live.client import ValkeyLiveClient
from ai.backend.common.types import SessionId


async def test_valkey_live_hset_operations(test_valkey_live: ValkeyLiveClient) -> None:
    """Test hash set operations for scheduler use"""
    test_hash = f"test-hash-{random.randint(1000, 9999)}"

    # Test single field hset
    result = await test_valkey_live.add_scheduler_metadata(
        test_hash,
        {
            "field1": "value1",
        },
    )
    assert result == 1

    # Test multiple field hset with mapping
    result = await test_valkey_live.add_scheduler_metadata(
        test_hash,
        {
            "field2": "value2",
            "field3": "value3",
        },
    )
    assert result == 2


async def test_valkey_live_multiple_data_operations(test_valkey_live: ValkeyLiveClient) -> None:
    """Test multiple live data operations"""
    test_prefix = f"test-multiple-{random.randint(1000, 9999)}"
    keys = [f"{test_prefix}-key-{i}" for i in range(3)]

    # Store some test data first
    for i, key in enumerate(keys):
        await test_valkey_live.store_live_data(key, f"value-{i}")

    # Test getting multiple keys
    results = await test_valkey_live.get_multiple_live_data(keys)
    assert len(results) == 3
    assert all(result is not None for result in results)


class TestSessionLastAccessMarker:
    @pytest.fixture()
    def session_id(self) -> SessionId:
        return SessionId(uuid4())

    @pytest.fixture()
    def marker_key(self, session_id: SessionId) -> str:
        return f"session.{session_id}.last_access"

    async def test_update_writes_server_timestamp(
        self,
        test_valkey_live: ValkeyLiveClient,
        session_id: SessionId,
        marker_key: str,
    ) -> None:
        await test_valkey_live.update_session_last_access(session_id)

        raw_marker = await test_valkey_live.get_live_data(marker_key)
        assert raw_marker is not None
        assert float(raw_marker) > 0

    async def test_mark_active_requires_existing_marker(
        self,
        test_valkey_live: ValkeyLiveClient,
        session_id: SessionId,
        marker_key: str,
    ) -> None:
        await test_valkey_live.mark_session_active(session_id)

        assert await test_valkey_live.get_live_data(marker_key) is None

    async def test_mark_active_overwrites_existing_marker(
        self,
        test_valkey_live: ValkeyLiveClient,
        session_id: SessionId,
        marker_key: str,
    ) -> None:
        await test_valkey_live.update_session_last_access(session_id)

        await test_valkey_live.mark_session_active(session_id)

        assert await test_valkey_live.get_live_data(marker_key) == b"0"

    async def test_delete_removes_marker(
        self,
        test_valkey_live: ValkeyLiveClient,
        session_id: SessionId,
        marker_key: str,
    ) -> None:
        await test_valkey_live.update_session_last_access(session_id)

        await test_valkey_live.delete_session_last_access(session_id)

        assert await test_valkey_live.get_live_data(marker_key) is None


async def test_valkey_live_client_lifecycle(test_valkey_live: ValkeyLiveClient) -> None:
    """Test client lifecycle management"""
    # The client should be created and working
    test_key = f"test-lifecycle-{random.randint(1000, 9999)}"
    await test_valkey_live.store_live_data(test_key, "test-value")
    result = await test_valkey_live.get_live_data(test_key)
    assert result is not None

    # Close should work without errors
    await test_valkey_live.close()

    # Second close should not raise an error
    await test_valkey_live.close()
