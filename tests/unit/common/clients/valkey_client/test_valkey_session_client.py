from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator

import pytest

from ai.backend.common.clients.valkey_client.client import (
    AbstractValkeyClient,
    create_valkey_client,
)
from ai.backend.common.clients.valkey_client.valkey_session.client import (
    LOGIN_HISTORY_KEY_PREFIX,
    ValkeySessionClient,
)
from ai.backend.common.typed_validators import HostPortPair as HostPortPairModel
from ai.backend.common.types import ValkeyTarget


class TestLoginFailures:
    @pytest.fixture
    async def raw_client(
        self, redis_container: tuple[str, HostPortPairModel]
    ) -> AsyncIterator[AbstractValkeyClient]:
        client = create_valkey_client(
            valkey_target=ValkeyTarget(addr=redis_container[1].address),
            db_id=0,
            human_readable_name="test.login",
        )
        await client.connect()
        try:
            yield client
        finally:
            await client.disconnect()

    @pytest.fixture
    def session_client(self, raw_client: AbstractValkeyClient) -> ValkeySessionClient:
        return ValkeySessionClient(raw_client)

    async def test_concurrent_failures_are_all_counted(
        self, session_client: ValkeySessionClient, test_case_ns: str
    ) -> None:
        await asyncio.gather(
            *(session_client.record_login_failure(test_case_ns, 60, 10) for _ in range(30))
        )
        value = await session_client.get_login_history(test_case_ns)
        assert value is not None
        assert json.loads(value)["login_fail_count"] == 30

    async def test_late_failure_preserves_block_expiry(
        self,
        session_client: ValkeySessionClient,
        raw_client: AbstractValkeyClient,
        test_case_ns: str,
    ) -> None:
        await session_client.record_login_failure(test_case_ns, 60, 1)
        before = await session_client.get_login_history(test_case_ns)
        assert before is not None
        async with raw_client.client() as conn:
            expiry = await conn.custom_command([
                "PEXPIRETIME",
                LOGIN_HISTORY_KEY_PREFIX + test_case_ns,
            ])
        await session_client.record_login_failure(test_case_ns, 60, 1)
        after = await session_client.get_login_history(test_case_ns)
        assert after is not None
        assert json.loads(after)["login_fail_count"] == 2
        assert json.loads(after)["last_login_attempt"] == json.loads(before)["last_login_attempt"]
        async with raw_client.client() as conn:
            assert (
                await conn.custom_command(["PEXPIRETIME", LOGIN_HISTORY_KEY_PREFIX + test_case_ns])
                == expiry
            )
