from __future__ import annotations

from typing import Any, cast
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

from ai.backend.agent.agent import AbstractAgent
from ai.backend.agent.config.unified import AgentUnifiedConfig, ContainerdConfig
from ai.backend.agent.containerd.agent import ContainerdAgent
from ai.backend.agent.containerd.client import ContainerdClient
from ai.backend.agent.errors.agent import InvalidAgentConfigError


@pytest.fixture
def base_init(mocker: MockerFixture) -> MagicMock:
    return mocker.patch.object(AbstractAgent, "__init__", return_value=None)


def _local_config(
    containerd: dict[str, Any],
    *,
    bind_host: str = "",
    advertised_host: str | None = None,
) -> AgentUnifiedConfig:
    config = MagicMock()
    config.container.bind_host = bind_host
    config.container.advertised_host = advertised_host
    config.container.port_range = (30000, 31000)
    config.containerd = ContainerdConfig.model_validate(containerd)
    return cast(AgentUnifiedConfig, config)


def _new_agent(local_config: AgentUnifiedConfig) -> ContainerdAgent:
    agent = object.__new__(ContainerdAgent)
    ContainerdAgent.__init__(agent, MagicMock(), local_config, computers={}, slots={})
    return agent


class TestContainerdAgentInit:
    def test_create_task_timeout_reaches_the_client(self, base_init: MagicMock) -> None:
        agent = _new_agent(_local_config({"create-task-timeout": 1200}))

        client = agent._client
        assert isinstance(client, ContainerdClient)
        assert client._client._config.create_task_timeout == 1200.0

    def test_base_init_receives_the_remaining_arguments(self, base_init: MagicMock) -> None:
        config = _local_config({})

        _new_agent(config)

        _, kwargs = base_init.call_args
        assert kwargs == {"computers": {}, "slots": {}}

    def test_network_follows_the_bridge_config(self, base_init: MagicMock) -> None:
        config = _local_config({"bridge-name": "bai-x", "bridge-subnet": "172.30.5.0/24"})

        agent = _new_agent(config)

        assert agent._network._bridge == "bai-x"
        assert str(agent._network._gateway) == "172.30.5.1"

    @pytest.mark.parametrize(
        ("bind_host", "advertised_host"),
        [
            ("127.0.0.1", None),
            ("127.1.2.3", None),
            ("localhost", None),
            ("node.example.com", None),
            ("::1", None),
            ("fe80::1", None),
            ("", "127.0.0.1"),
            ("", "localhost"),
            ("", "LocalHost"),
            ("", "::1"),
            ("10.0.0.5", "127.1.2.3"),
        ],
    )
    def test_loopback_and_non_ipv4_hosts_are_refused_before_the_base_init(
        self,
        base_init: MagicMock,
        bind_host: str,
        advertised_host: str | None,
    ) -> None:
        config = _local_config({}, bind_host=bind_host, advertised_host=advertised_host)

        with pytest.raises(InvalidAgentConfigError, match=r"container\.(bind|advertised)-host"):
            _new_agent(config)

        base_init.assert_not_called()

    @pytest.mark.parametrize(
        ("bind_host", "advertised_host"),
        [("", None), ("0.0.0.0", "node.example.com"), ("10.0.0.5", "10.0.0.6")],
    )
    def test_other_hosts_are_accepted(
        self,
        base_init: MagicMock,
        bind_host: str,
        advertised_host: str | None,
    ) -> None:
        _new_agent(_local_config({}, bind_host=bind_host, advertised_host=advertised_host))
