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
from ai.backend.common.types import KernelId


@pytest.fixture
def base_init(mocker: MockerFixture) -> MagicMock:
    return mocker.patch.object(AbstractAgent, "__init__", return_value=None)


def _local_config(containerd: dict[str, Any]) -> AgentUnifiedConfig:
    config = MagicMock()
    config.containerd = ContainerdConfig.model_validate(containerd)
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
