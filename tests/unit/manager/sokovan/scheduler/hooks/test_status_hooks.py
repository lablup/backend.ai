"""Regression tests for status-based transition hooks.

Covers the volatile inter-container network cleanup performed by
``TerminatedTransitionHook``. The cleanup was lost in a series
of refactors, leaking Docker overlay (MULTI_NODE) and agent-local
(SINGLE_NODE) networks after sessions terminated.
"""

from __future__ import annotations

from collections.abc import Iterator
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from ai.backend.common.types import AgentId, ClusterMode, SessionId
from ai.backend.manager.errors.common import ServerMisconfiguredError
from ai.backend.manager.models.network import NetworkType
from ai.backend.manager.sokovan.recorder.pool import RecordPool
from ai.backend.manager.sokovan.recorder.types import StepStatus
from ai.backend.manager.sokovan.scheduler.hooks.status import (
    TerminatedHookDependencies,
    TerminatedTransitionHook,
)
from ai.backend.manager.sokovan.scheduler.recorder import SessionRecorderContext


class TestTerminatedTransitionHookNetworkCleanup:
    """Volatile network cleanup on session TERMINATED transition."""

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

    @pytest.fixture(autouse=True)
    def recorder_pool(self, session_id: SessionId) -> Iterator[RecordPool[SessionId]]:
        """Ambient recorder scope, mirroring the coordinator scope the hook always
        runs within in production. Tests assert on the pool by requesting it by name."""
        with SessionRecorderContext.scope("terminate", entity_ids=[session_id]) as pool:
            yield pool

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

    async def test_records_terminate_cleanup_into_pool(
        self,
        hook: TerminatedTransitionHook,
        recorder_pool: RecordPool[SessionId],
        multi_node_session: MagicMock,
        session_id: SessionId,
    ) -> None:
        """The hook records a terminate_cleanup phase/step into the scope's pool
        so the coordinator can persist it as session scheduling sub_steps."""
        await hook.execute(multi_node_session)

        record = recorder_pool.build_all_records()[session_id]
        cleanup = next(p for p in record.phases if p.name == "terminate_cleanup")
        assert cleanup.status == StepStatus.SUCCESS
        step = next(s for s in cleanup.steps if s.name == "destroy_network")
        assert step.status == StepStatus.SUCCESS

    async def test_records_terminate_cleanup_failure_with_error_code(
        self,
        hook: TerminatedTransitionHook,
        recorder_pool: RecordPool[SessionId],
        config_provider: MagicMock,
        multi_node_session: MagicMock,
        session_id: SessionId,
    ) -> None:
        """A failed cleanup is recorded as FAILED with an error_code, since the
        hook raises BackendAIError subclasses (ServerMisconfiguredError)."""
        config_provider.config.network.inter_container.default_driver = None

        with pytest.raises(ServerMisconfiguredError):
            await hook.execute(multi_node_session)

        record = recorder_pool.build_all_records()[session_id]
        cleanup = next(p for p in record.phases if p.name == "terminate_cleanup")
        assert cleanup.status == StepStatus.FAILED
        step = next(s for s in cleanup.steps if s.name == "destroy_network")
        assert step.status == StepStatus.FAILED
        assert step.error_code is not None
