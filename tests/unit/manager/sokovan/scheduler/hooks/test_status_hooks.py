"""Regression tests for status-based transition hooks.

Covers the volatile inter-container network cleanup performed by
``TerminatedTransitionHook`` (BA-6273). The cleanup was lost in a series
of refactors, leaking Docker overlay (MULTI_NODE) and agent-local
(SINGLE_NODE) networks after sessions terminated.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from ai.backend.common.types import AgentId, ClusterMode, SessionId
from ai.backend.manager.errors.common import ServerMisconfiguredError
from ai.backend.manager.models.network import NetworkType
from ai.backend.manager.sokovan.scheduler.hooks.status import (
    TerminatedHookDependencies,
    TerminatedTransitionHook,
)


class TestTerminatedTransitionHookNetworkCleanup:
    """Volatile network cleanup on session TERMINATED transition (BA-6273)."""

    @pytest.fixture
    def agent_client(self) -> AsyncMock:
        return AsyncMock()

    @pytest.fixture
    def agent_client_pool(self, agent_client: AsyncMock) -> MagicMock:
        acquire_cm = MagicMock()
        acquire_cm.__aenter__ = AsyncMock(return_value=agent_client)
        acquire_cm.__aexit__ = AsyncMock(return_value=None)
        pool = MagicMock()
        pool.acquire = MagicMock(return_value=acquire_cm)
        return pool

    @pytest.fixture
    def network_plugin(self) -> AsyncMock:
        return AsyncMock()

    @pytest.fixture
    def network_plugin_ctx(self, network_plugin: AsyncMock) -> MagicMock:
        ctx = MagicMock()
        ctx.plugins = {"overlay": network_plugin}
        return ctx

    @pytest.fixture
    def config_provider(self) -> MagicMock:
        cp = MagicMock()
        cp.config.network.inter_container.default_driver = "overlay"
        return cp

    @pytest.fixture
    def deps(
        self,
        agent_client_pool: MagicMock,
        network_plugin_ctx: MagicMock,
        config_provider: MagicMock,
    ) -> TerminatedHookDependencies:
        return TerminatedHookDependencies(
            agent_client_pool=agent_client_pool,
            network_plugin_ctx=network_plugin_ctx,
            config_provider=config_provider,
        )

    @pytest.fixture
    def hook(self, deps: TerminatedHookDependencies) -> TerminatedTransitionHook:
        return TerminatedTransitionHook(deps)

    @pytest.fixture
    def agent_id(self) -> str:
        return "agent-1"

    @pytest.fixture
    def session_id(self) -> SessionId:
        return SessionId(uuid4())

    @pytest.fixture
    def network_id(self, request: pytest.FixtureRequest) -> str | None:
        value: str | None = getattr(request, "param", "net-123")
        return value

    @pytest.fixture
    def network_type(self, request: pytest.FixtureRequest) -> NetworkType | None:
        value: NetworkType | None = getattr(request, "param", NetworkType.VOLATILE)
        return value

    @pytest.fixture
    def multi_node_session(
        self,
        network_type: NetworkType | None,
        network_id: str | None,
        session_id: SessionId,
    ) -> MagicMock:
        session = MagicMock()
        session.session_info.identity.id = session_id
        session.session_info.network.network_type = network_type
        session.session_info.network.network_id = network_id
        session.session_info.resource.cluster_mode = ClusterMode.MULTI_NODE.name
        session.main_kernel.resource.agent = None
        return session

    @pytest.fixture
    def single_node_session(
        self,
        network_type: NetworkType | None,
        network_id: str | None,
        agent_id: str,
        session_id: SessionId,
    ) -> MagicMock:
        session = MagicMock()
        session.session_info.identity.id = session_id
        session.session_info.network.network_type = network_type
        session.session_info.network.network_id = network_id
        session.session_info.resource.cluster_mode = ClusterMode.SINGLE_NODE.name
        session.main_kernel.resource.agent = agent_id
        return session

    async def test_multinode_volatile_destroys_overlay_network(
        self,
        hook: TerminatedTransitionHook,
        multi_node_session: MagicMock,
        network_plugin: AsyncMock,
        agent_client: AsyncMock,
    ) -> None:
        await hook.execute(multi_node_session)

        network_plugin.destroy_network.assert_awaited_once_with(network_id="net-123")
        agent_client.destroy_local_network.assert_not_awaited()

    async def test_singlenode_volatile_destroys_local_network(
        self,
        hook: TerminatedTransitionHook,
        single_node_session: MagicMock,
        agent_client_pool: MagicMock,
        agent_client: AsyncMock,
        network_plugin: AsyncMock,
    ) -> None:
        await hook.execute(single_node_session)

        agent_client_pool.acquire.assert_called_once_with(AgentId("agent-1"))
        agent_client.destroy_local_network.assert_awaited_once_with("net-123")
        network_plugin.destroy_network.assert_not_awaited()

    @pytest.mark.parametrize(
        "network_type",
        [NetworkType.PERSISTENT, NetworkType.HOST, None],
        indirect=True,
    )
    async def test_non_volatile_network_skips_destroy(
        self,
        hook: TerminatedTransitionHook,
        multi_node_session: MagicMock,
        network_plugin: AsyncMock,
        agent_client: AsyncMock,
    ) -> None:
        await hook.execute(multi_node_session)

        network_plugin.destroy_network.assert_not_awaited()
        agent_client.destroy_local_network.assert_not_awaited()

    @pytest.mark.parametrize("network_id", [None], indirect=True)
    async def test_missing_network_id_skips_destroy(
        self,
        hook: TerminatedTransitionHook,
        multi_node_session: MagicMock,
        network_plugin: AsyncMock,
        agent_client: AsyncMock,
    ) -> None:
        await hook.execute(multi_node_session)

        network_plugin.destroy_network.assert_not_awaited()
        agent_client.destroy_local_network.assert_not_awaited()

    async def test_multinode_without_driver_raises(
        self,
        hook: TerminatedTransitionHook,
        config_provider: MagicMock,
        multi_node_session: MagicMock,
        network_plugin: AsyncMock,
    ) -> None:
        config_provider.config.network.inter_container.default_driver = None

        with pytest.raises(ServerMisconfiguredError):
            await hook.execute(multi_node_session)

        network_plugin.destroy_network.assert_not_awaited()

    async def test_destroy_failure_propagates(
        self,
        hook: TerminatedTransitionHook,
        multi_node_session: MagicMock,
        network_plugin: AsyncMock,
    ) -> None:
        """Blocking hook: destroy failures must propagate so the coordinator
        keeps the session in TERMINATING and the self-healing loop retries."""
        network_plugin.destroy_network.side_effect = RuntimeError("docker unreachable")

        with pytest.raises(RuntimeError, match="docker unreachable"):
            await hook.execute(multi_node_session)
