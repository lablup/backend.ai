from __future__ import annotations

import uuid
from typing import Any, cast
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

from ai.backend.agent.agent import AbstractAgent
from ai.backend.agent.config.unified import AgentUnifiedConfig, ContainerdConfig
from ai.backend.agent.containerd.agent import ContainerdAgent
from ai.backend.agent.containerd.rpc.client import ContainerdClient
from ai.backend.agent.errors.agent import InvalidAgentConfigError
from ai.backend.common.types import KernelId


@pytest.fixture
def base_init(mocker: MockerFixture) -> MagicMock:
    return mocker.patch.object(AbstractAgent, "__init__", return_value=None)


def _local_config(
    containerd: dict[str, Any], bind_host: str = "0.0.0.0", advertised_host: str | None = None
) -> AgentUnifiedConfig:
    config = MagicMock()
    config.containerd = ContainerdConfig.model_validate(containerd)
    config.container.bind_host = bind_host
    config.container.advertised_host = advertised_host
    config.container.port_range = (30000, 30999)
    return cast(AgentUnifiedConfig, config)


def _new_agent(local_config: AgentUnifiedConfig) -> ContainerdAgent:
    agent = object.__new__(ContainerdAgent)
    ContainerdAgent.__init__(agent, MagicMock(), local_config, computers={}, slots={})
    return agent


class TestContainerdAgentInit:
    def test_create_task_timeout_reaches_the_client(self, base_init: MagicMock) -> None:
        agent = _new_agent(_local_config({"create-task-timeout": 120}))

        assert isinstance(agent._client, ContainerdClient)
        assert agent._client._config.create_task_timeout == 120.0

    def test_bridge_settings_reach_the_network(self, base_init: MagicMock) -> None:
        agent = _new_agent(_local_config({"bridge-name": "bai1", "bridge-subnet": "10.9.0.0/24"}))

        assert agent._network.netns_path(KernelId(uuid.UUID(int=1))).startswith("/run/netns/bai1-")

    def test_base_init_receives_the_remaining_arguments(self, base_init: MagicMock) -> None:
        config = _local_config({})

        _new_agent(config)

        _, kwargs = base_init.call_args
        assert kwargs == {"computers": {}, "slots": {}}

    @pytest.mark.parametrize("host", ["", "0.0.0.0", "10.0.0.5"])
    def test_usable_bind_host_is_accepted(self, base_init: MagicMock, host: str) -> None:
        _new_agent(_local_config({}, bind_host=host))

    @pytest.mark.parametrize("host", ["127.0.0.1", "localhost", "::1", "example.com"])
    def test_unusable_bind_host_is_refused(self, base_init: MagicMock, host: str) -> None:
        with pytest.raises(InvalidAgentConfigError, match="bind-host"):
            _new_agent(_local_config({}, bind_host=host))

    @pytest.mark.parametrize("host", ["127.0.0.1", "localhost", "::1"])
    def test_loopback_advertised_host_is_refused(self, base_init: MagicMock, host: str) -> None:
        with pytest.raises(InvalidAgentConfigError, match="advertised-host"):
            _new_agent(_local_config({}, advertised_host=host))

    def test_named_advertised_host_is_accepted(self, base_init: MagicMock) -> None:
        _new_agent(_local_config({}, advertised_host="agent1.example.com"))
