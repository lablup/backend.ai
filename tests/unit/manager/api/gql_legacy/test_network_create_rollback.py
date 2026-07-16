"""The GQL createNetwork mutation must release the plugin's subnet/VNI/etcd meta when the
DB/RBAC step fails, or the block leaks and a same-subnet retry fails with
RequestedSubnetUnavailable. gql_mutation_wrapper reports most failures as an ok=False result
(re-raising only Timeout/Cancelled), so both surfaces are exercised here.
"""

import asyncio
from unittest.mock import AsyncMock

import pytest

from ai.backend.manager.api.gql_legacy.network import (
    CreateNetwork,
    _run_create_network_with_rollback,
)


class TestCreateNetworkRollback:
    async def test_success_does_not_roll_back(self) -> None:
        plugin = AsyncMock()

        async def run_mutation() -> CreateNetwork:
            return CreateNetwork(ok=True, msg="Network created")

        result = await _run_create_network_with_rollback(plugin, "net-1", run_mutation)

        assert result.ok is True
        plugin.destroy_network.assert_not_called()

    async def test_ok_false_result_rolls_back(self) -> None:
        # gql_mutation_wrapper swallows a DB/RBAC failure into ok=False; the claimed subnet/VNI must
        # still be released so it does not leak and block a same-subnet retry.
        plugin = AsyncMock()

        async def run_mutation() -> CreateNetwork:
            return CreateNetwork(ok=False, msg="integrity error")

        result = await _run_create_network_with_rollback(plugin, "net-1", run_mutation)

        assert result.ok is False
        plugin.destroy_network.assert_awaited_once_with("net-1")

    async def test_raised_exception_rolls_back_and_propagates(self) -> None:
        # gql_mutation_wrapper re-raises TimeoutError; the resources must be released before it
        # propagates to the caller.
        plugin = AsyncMock()

        async def run_mutation() -> CreateNetwork:
            raise TimeoutError("db timeout")

        with pytest.raises(TimeoutError):
            await _run_create_network_with_rollback(plugin, "net-1", run_mutation)

        plugin.destroy_network.assert_awaited_once_with("net-1")

    async def test_cancellation_rolls_back_and_propagates(self) -> None:
        # asyncio.CancelledError is a BaseException, not an Exception — it must still trigger the
        # rollback (or a cancelled create leaks the subnet/VNI) and then re-propagate unchanged.
        plugin = AsyncMock()

        async def run_mutation() -> CreateNetwork:
            raise asyncio.CancelledError()

        with pytest.raises(asyncio.CancelledError):
            await _run_create_network_with_rollback(plugin, "net-1", run_mutation)

        plugin.destroy_network.assert_awaited_once_with("net-1")

    async def test_rollback_failure_is_swallowed(self) -> None:
        # destroy_network is best-effort: its own failure must not mask the original outcome.
        plugin = AsyncMock()
        plugin.destroy_network.side_effect = RuntimeError("etcd down")

        async def run_mutation() -> CreateNetwork:
            return CreateNetwork(ok=False, msg="integrity error")

        result = await _run_create_network_with_rollback(plugin, "net-1", run_mutation)

        assert result.ok is False
        plugin.destroy_network.assert_awaited_once_with("net-1")
