from __future__ import annotations

from collections.abc import AsyncGenerator

import pytest

from ai.backend.common.etcd import AsyncEtcd, ConfigScopes
from ai.backend.common.health_checker.checkers.etcd import EtcdHealthChecker
from ai.backend.testutils.bootstrap import HostPortPairModel


class TestEtcdHealthChecker:
    """Test EtcdHealthChecker with real etcd containers."""

    @pytest.fixture
    async def etcd_client(
        self,
        etcd_container: tuple[str, HostPortPairModel],
        test_ns: str,
    ) -> AsyncGenerator[AsyncEtcd, None]:
        """Create an AsyncEtcd client connected to the test container."""
        from ai.backend.common.types import HostPortPair

        container_id, etcd_addr = etcd_container

        scope_prefix_map = {
            ConfigScopes.GLOBAL: "",
            ConfigScopes.NODE: f"nodes/test/{test_ns}",
        }

        etcd = AsyncEtcd(
            [HostPortPair(etcd_addr.host, etcd_addr.port)],
            namespace=test_ns,
            scope_prefix_map=scope_prefix_map,
        )

        try:
            yield etcd
        finally:
            await etcd.close()

    @pytest.mark.asyncio
    async def test_success(self, etcd_client: AsyncEtcd) -> None:
        """Test successful health check with real etcd connection."""
        checker = EtcdHealthChecker(
            etcd=etcd_client,
            timeout=5.0,
        )

        result = await checker.check_service()
        assert len(result.results) == 1
        status = result.results[list(result.results.keys())[0]]
        assert status.is_healthy
        assert status.error_message is None

    @pytest.mark.asyncio
    async def test_timeout_property(self, etcd_client: AsyncEtcd) -> None:
        """Test that timeout property returns the correct value."""
        timeout_value = 3.5
        checker = EtcdHealthChecker(
            etcd=etcd_client,
            timeout=timeout_value,
        )

        assert checker.timeout == timeout_value

    @pytest.mark.asyncio
    async def test_connection_error(self) -> None:
        """Test health check failure with unreachable etcd server."""
        # Create client pointing to non-existent server
        from ai.backend.common.types import HostPortPair

        scope_prefix_map = {
            ConfigScopes.GLOBAL: "",
        }

        etcd = AsyncEtcd(
            [HostPortPair("localhost", 99999)],
            namespace="test",
            scope_prefix_map=scope_prefix_map,
        )

        try:
            checker = EtcdHealthChecker(
                etcd=etcd,
                timeout=1.0,
            )

            result = await checker.check_service()
            assert len(result.results) == 1
            status = result.results[list(result.results.keys())[0]]
            assert not status.is_healthy
            assert status.error_message is not None
        finally:
            await etcd.close()

    @pytest.mark.asyncio
    async def test_multiple_checks(self, etcd_client: AsyncEtcd) -> None:
        """Test that multiple health checks work correctly."""
        checker = EtcdHealthChecker(
            etcd=etcd_client,
            timeout=5.0,
        )

        # Multiple checks should all succeed
        result1 = await checker.check_service()
        assert result1.results[list(result1.results.keys())[0]].is_healthy

        result2 = await checker.check_service()
        assert result2.results[list(result2.results.keys())[0]].is_healthy

        result3 = await checker.check_service()
        assert result3.results[list(result3.results.keys())[0]].is_healthy
