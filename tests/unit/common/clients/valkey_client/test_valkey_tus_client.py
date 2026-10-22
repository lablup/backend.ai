from __future__ import annotations

import uuid
from collections.abc import AsyncIterator

import pytest

from ai.backend.common.clients.valkey_client.valkey_tus.client import (
    TusSessionId,
    TusUploadState,
    ValkeyTusClient,
)
from ai.backend.common.defs import REDIS_TUS_DB
from ai.backend.common.typed_validators import HostPortPair as HostPortPairModel
from ai.backend.common.types import ValkeyTarget


class TestValkeyTusClient:
    @pytest.fixture
    async def test_valkey_tus(
        self, redis_container: tuple[str, HostPortPairModel]
    ) -> AsyncIterator[ValkeyTusClient]:
        hostport_pair: HostPortPairModel = redis_container[1]
        valkey_target = ValkeyTarget(
            addr=hostport_pair.address,
        )
        client = await ValkeyTusClient.create(
            valkey_target,
            human_readable_name="test.tus",
            db_id=REDIS_TUS_DB,
        )
        try:
            yield client
        finally:
            await client.close()

    async def test_offset_lifecycle(self, test_valkey_tus: ValkeyTusClient) -> None:
        """Initialize → try_load_offset → advance_offset round-trip."""
        session_id = TusSessionId(f"test-session-{uuid.uuid4().hex[:8]}")
        holder_token = f"holder-{uuid.uuid4().hex[:8]}"

        await test_valkey_tus.initialize_offset(session_id, ttl_seconds=60)
        initial_state = await test_valkey_tus.get_upload_state(session_id)
        assert initial_state is not None
        assert initial_state.offset == 0
        assert 0 < initial_state.ttl_seconds <= 60

        offset = await test_valkey_tus.try_load_offset(session_id, holder_token)
        assert offset == 0

        advanced_state = await test_valkey_tus.advance_offset(
            session_id, holder_token, length=1024, offset_ttl_seconds=120
        )
        assert advanced_state == TusUploadState(offset=1024, ttl_seconds=120)
        stored_state = await test_valkey_tus.get_upload_state(session_id)
        assert stored_state is not None
        assert stored_state.offset == 1024
        assert 60 < stored_state.ttl_seconds <= 120

    async def test_upload_state_of_unknown_session_is_none(
        self, test_valkey_tus: ValkeyTusClient
    ) -> None:
        session_id = TusSessionId(f"test-session-{uuid.uuid4().hex[:8]}")

        assert await test_valkey_tus.get_upload_state(session_id) is None
