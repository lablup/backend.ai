from __future__ import annotations

from collections.abc import AsyncGenerator

import pytest

from ai.backend.common.clients.valkey_client.client import ValkeyStandaloneClient
from ai.backend.common.health.checkers.valkey import ValkeyHealthChecker
from ai.backend.common.health.exceptions import ValkeyHealthCheckError
from ai.backend.testutils.bootstrap import HostPortPairModel


class TestValkeyHealthChecker:
    """Test ValkeyHealthChecker with real Valkey/Redis containers."""

    @pytest.fixture
    async def valkey_client(
        self,
        redis_container: tuple[str, HostPortPairModel],
    ) -> AsyncGenerator[ValkeyStandaloneClient, None]:
        """Create a Valkey standalone client connected to the test container."""
        from ai.backend.common.clients.valkey_client.client import ValkeyStandaloneTarget

        container_id, hostport_pair = redis_container

        target = ValkeyStandaloneTarget(address=hostport_pair.address)
        client = ValkeyStandaloneClient(
            target,
            db_id=0,
            human_readable_name="test-health-checker",
        )
        await client.connect()

        try:
            yield client
        finally:
            await client.disconnect()

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_success(self, valkey_client: ValkeyStandaloneClient) -> None:
        """Test successful health check with real Valkey connection."""
        checker = ValkeyHealthChecker(
            client=valkey_client,
            timeout=5.0,
        )

        # Should not raise
        await checker.check_health()

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_timeout_property(
        self,
        valkey_client: ValkeyStandaloneClient,
    ) -> None:
        """Test that timeout property returns the correct value."""
        timeout_value = 3.5
        checker = ValkeyHealthChecker(
            client=valkey_client,
            timeout=timeout_value,
        )

        assert checker.timeout == timeout_value

    @pytest.mark.asyncio
    async def test_connection_error(self) -> None:
        """Test health check failure with unreachable Valkey server."""
        from ai.backend.common.clients.valkey_client.client import ValkeyStandaloneTarget

        # Create client pointing to non-existent server
        target = ValkeyStandaloneTarget(address="localhost:99999")
        client = ValkeyStandaloneClient(
            target,
            db_id=0,
            human_readable_name="test-fail",
        )

        try:
            # Connection will fail, but let's test the checker anyway
            await client.connect()
        except Exception:
            # Expected - connection should fail
            pass

        try:
            checker = ValkeyHealthChecker(
                client=client,
                timeout=1.0,
            )

            with pytest.raises(ValkeyHealthCheckError) as exc_info:
                await checker.check_health()

            # Should contain error information
            assert "health check failed" in str(exc_info.value).lower()
        finally:
            await client.disconnect()

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_multiple_checks(
        self,
        valkey_client: ValkeyStandaloneClient,
    ) -> None:
        """Test that multiple health checks work correctly."""
        checker = ValkeyHealthChecker(
            client=valkey_client,
            timeout=5.0,
        )

        # Multiple checks should all succeed
        await checker.check_health()
        await checker.check_health()
        await checker.check_health()
