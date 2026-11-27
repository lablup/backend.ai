"""The node is announced to the manager only once its RPC transport serves."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any, cast
from unittest.mock import AsyncMock, MagicMock

import pytest
from pytest_mock import MockerFixture

from ai.backend.agent.agent import AbstractAgent
from ai.backend.agent.errors import AgentInitializationError
from ai.backend.agent.runtime import AgentRuntime
from ai.backend.agent.server import AgentRPCServer, agent_server_ctx


def _events(stub: Any) -> list[str]:
    return [type(call.args[0]).__name__ for call in stub.anycast_event.await_args_list]


class TestAgentInitDoesNotAnnounce:
    """`__ainit__` runs before the RPC transport serves, so it must not announce the node."""

    @pytest.fixture
    def local_cron(self, mocker: MockerFixture) -> MagicMock:
        module = "ai.backend.agent.agent"
        for name in ("EventProducer", "BackgroundTaskManagerArgs", "current_loop"):
            mocker.patch(f"{module}.{name}")
        mocker.patch(f"{module}.EventDispatcher", return_value=MagicMock(start=AsyncMock()))
        mocker.patch(f"{module}.BackgroundTaskManager", return_value=MagicMock(init=AsyncMock()))
        for name in (
            "ValkeyContainerLogClient",
            "ValkeyStreamClient",
            "ValkeyStatClient",
            "ValkeyBgtaskClient",
            "ValkeyImageClient",
            "ValkeyScheduleClient",
        ):
            mocker.patch(f"{module}.{name}", MagicMock(create=AsyncMock()))
        # Keeps whatever `__ainit__` runs in an executor off the host.
        mocker.patch(f"{module}.run_in_executor_with_context", AsyncMock(return_value=None))
        mocker.patch(
            f"{module}.Runner",
            return_value=MagicMock(register_observer=AsyncMock(), start=AsyncMock()),
        )
        return mocker.patch(f"{module}.LocalCron", return_value=MagicMock(start=AsyncMock()))

    async def test_init_builds_the_heartbeat_without_starting_it_or_announcing(
        self, local_cron: MagicMock
    ) -> None:
        stub = MagicMock(
            computers={},
            _skip_initial_scan=True,
            _make_message_queue=AsyncMock(),
            anycast_event=AsyncMock(),
        )
        # Real values for config values `__ainit__` may read as numbers, not MagicMocks.
        stub.local_config.agent.abuse_report_path = None
        stub.local_config.agent.kernel_creation_concurrency = 1
        stub.local_config.container.port_range = (30000, 31000)

        await AbstractAgent.__ainit__(stub)

        local_cron.assert_called_once()
        local_cron.return_value.start.assert_not_awaited()
        stub.anycast_event.assert_not_awaited()


class TestAgentStartServing:
    async def test_start_serving_starts_the_heartbeat_and_announces(self) -> None:
        cron = SimpleNamespace(start=AsyncMock())
        stub = SimpleNamespace(_local_cron=cron, anycast_event=AsyncMock())

        await AbstractAgent.start_serving(cast(Any, stub))

        cron.start.assert_awaited_once()
        assert _events(stub) == ["AgentStartedEvent"]

    async def test_stop_serving_stops_the_heartbeat(self) -> None:
        cron = SimpleNamespace(stop=AsyncMock())
        stub = SimpleNamespace(_local_cron=cron, anycast_event=AsyncMock())

        await AbstractAgent.stop_serving(cast(Any, stub))

        cron.stop.assert_awaited_once()
        assert _events(stub) == []

    async def test_stop_serving_before_the_cron_is_built_is_harmless(self) -> None:
        stub = SimpleNamespace(_local_cron=None, anycast_event=AsyncMock())

        await AbstractAgent.stop_serving(cast(Any, stub))

        assert _events(stub) == []


class TestRuntimeServing:
    async def test_every_agent_starts_and_stops_serving(self) -> None:
        agents = [MagicMock(start_serving=AsyncMock(), stop_serving=AsyncMock()) for _ in range(2)]
        runtime = SimpleNamespace(get_agents=lambda: agents)

        await AgentRuntime.start_serving(cast(Any, runtime))
        await AgentRuntime.stop_serving(cast(Any, runtime))

        for agent in agents:
            agent.start_serving.assert_awaited_once()
            agent.stop_serving.assert_awaited_once()


class TestServerAnnouncesOnlyOnceTheTransportServes:
    @pytest.fixture
    def server(self) -> AgentRPCServer:
        server = object.__new__(AgentRPCServer)
        server._transport_entered = False
        server.runtime = MagicMock(start_serving=AsyncMock(), stop_serving=AsyncMock())
        server.rpc_server = MagicMock(__aenter__=AsyncMock())
        return server

    async def test_announcing_before_the_transport_serves_is_refused(
        self, server: AgentRPCServer
    ) -> None:
        with pytest.raises(AgentInitializationError, match="before its RPC transport is serving"):
            await server.start_serving()

        cast(Any, server.runtime).start_serving.assert_not_awaited()

    async def test_it_announces_once_the_transport_is_serving(self, server: AgentRPCServer) -> None:
        await server.__aenter__()
        await server.start_serving()

        cast(Any, server.runtime).start_serving.assert_awaited_once()

    async def test_stopping_takes_the_announcement_back(self, server: AgentRPCServer) -> None:
        server._transport_entered = True

        await server.stop_serving()

        cast(Any, server.runtime).stop_serving.assert_awaited_once()
        with pytest.raises(AgentInitializationError):
            await server.start_serving()


class TestServerContextWithdrawsAFailedAnnouncement:
    async def test_a_failing_start_serving_still_stops_serving(self, mocker: MockerFixture) -> None:
        agent_server = MagicMock(
            start_serving=AsyncMock(side_effect=AgentInitializationError("announce failed")),
            stop_serving=AsyncMock(),
        )
        mocker.patch.object(AgentRPCServer, "new", AsyncMock(return_value=agent_server))
        mocker.patch("ai.backend.agent.server.build_root_server", return_value=MagicMock())
        mocker.patch(
            "ai.backend.agent.server.web.AppRunner", return_value=MagicMock(setup=AsyncMock())
        )
        mocker.patch(
            "ai.backend.agent.server.web.TCPSite", return_value=MagicMock(start=AsyncMock())
        )
        local_config = MagicMock()
        local_config.otel.enabled = False
        local_config.agent_common.ssl_enabled = False

        with pytest.raises(AgentInitializationError):
            async with agent_server_ctx(local_config, MagicMock()):
                pass

        agent_server.stop_serving.assert_awaited_once()
