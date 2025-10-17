from typing import Any
from unittest.mock import Mock
from uuid import uuid4

import pytest

from ai.backend.agent.config.unified import AgentUnifiedConfig
from ai.backend.agent.server import AgentRPCServer
from ai.backend.agent.types import AgentBackend
from ai.backend.common.types import AgentId, KernelId
from ai.backend.common.validators import BinarySize

RawConfigT = dict[str, Any]


@pytest.fixture
def mock_agent_server(single_agent_config: AgentUnifiedConfig) -> AgentRPCServer:
    server = object.__new__(AgentRPCServer)
    server.local_config = single_agent_config
    server.agents = {}
    server._default_agent_id = AgentId("test-agent")
    return server


@pytest.fixture
def single_agent_config() -> AgentUnifiedConfig:
    raw_config: RawConfigT = {
        "agent": {
            "backend": AgentBackend.DOCKER,
            "rpc-listen-addr": {"host": "127.0.0.1", "port": 6001},
            "id": "test-agent",
        },
        "container": {
            "scratch-type": "hostdir",
            "port-range": [30000, 31000],
        },
        "resource": {},
        "etcd": {
            "namespace": "test",
            "addr": {"host": "127.0.0.1", "port": 2379},
        },
    }
    return AgentUnifiedConfig.model_validate(raw_config)


@pytest.fixture
def multi_agent_config() -> AgentUnifiedConfig:
    raw_config: RawConfigT = {
        "agent": {
            "backend": AgentBackend.DOCKER,
            "rpc-listen-addr": {"host": "127.0.0.1", "port": 6001},
            "kernel-creation-concurrency": 4,
            "agent-sock-port": 6007,
        },
        "container": {
            "scratch-type": "hostdir",
            "port-range": [30000, 31000],
        },
        "resource": {
            "reserved-cpu": 1,
            "reserved-mem": BinarySize().check("1G"),
            "reserved-disk": BinarySize().check("8G"),
        },
        "etcd": {
            "namespace": "test",
            "addr": {"host": "127.0.0.1", "port": 2379},
        },
        "sub-agents": [
            {
                "agent": {
                    "id": "agent-1",
                    "kernel-creation-concurrency": 8,
                    "agent-sock-port": 6008,
                },
                "container": {"port-range": [31000, 32000]},
                "resource": {
                    "reserved-cpu": 2,
                    "reserved-mem": BinarySize().check("2G"),
                    "reserved-disk": BinarySize().check("16G"),
                },
            },
            {
                "agent": {
                    "id": "agent-2",
                    "kernel-creation-concurrency": 6,
                    "agent-sock-port": 6009,
                },
                "container": {"port-range": [32000, 33000]},
                "resource": {
                    "reserved-cpu": 1,
                    "reserved-mem": BinarySize().check("512M"),
                    "reserved-disk": BinarySize().check("4G"),
                },
            },
        ],
    }
    return AgentUnifiedConfig.model_validate(raw_config)


class TestAgentRPCServerSingleAgentMode:
    def test_default_agent_property_returns_single_agent(
        self, mock_agent_server: AgentRPCServer
    ) -> None:
        mock_agent = Mock()
        mock_agent.id = AgentId("test-agent")
        mock_agent_server.agents = {AgentId("test-agent"): mock_agent}

        result = mock_agent_server.default_agent

        assert result is mock_agent

    def test_select_agent_without_id_returns_default(
        self, mock_agent_server: AgentRPCServer
    ) -> None:
        mock_agent = Mock()
        mock_agent.id = AgentId("test-agent")
        mock_agent_server.agents = {AgentId("test-agent"): mock_agent}

        result = mock_agent_server._select_agent(agent_id=None)

        assert result is mock_agent

    def test_select_agent_with_valid_id_returns_agent(
        self, mock_agent_server: AgentRPCServer
    ) -> None:
        mock_agent = Mock()
        mock_agent.id = AgentId("test-agent")
        mock_agent_server.agents = {AgentId("test-agent"): mock_agent}

        result = mock_agent_server._select_agent(agent_id=AgentId("test-agent"))

        assert result is mock_agent

    def test_select_agent_with_invalid_id_raises_error(
        self, mock_agent_server: AgentRPCServer
    ) -> None:
        mock_agent = Mock()
        mock_agent.id = AgentId("test-agent")
        mock_agent_server.agents = {AgentId("test-agent"): mock_agent}

        with pytest.raises(ValueError, match="not found"):
            mock_agent_server._select_agent(agent_id=AgentId("nonexistent"))


class TestAgentRPCServerMultiAgentMode:
    def test_agents_property_returns_all_agents(self, mock_agent_server: AgentRPCServer) -> None:
        mock_agent1 = Mock()
        mock_agent1.id = AgentId("agent-1")
        mock_agent2 = Mock()
        mock_agent2.id = AgentId("agent-2")

        mock_agent_server.agents = {
            AgentId("agent-1"): mock_agent1,
            AgentId("agent-2"): mock_agent2,
        }

        assert len(mock_agent_server.agents) == 2
        assert mock_agent_server.agents[AgentId("agent-1")] is mock_agent1
        assert mock_agent_server.agents[AgentId("agent-2")] is mock_agent2

    def test_find_agent_by_kernel_id_single_match(self, mock_agent_server: AgentRPCServer) -> None:
        kernel_id = KernelId(uuid4())
        mock_agent1 = Mock()
        mock_agent1.known_kernel_ids = {kernel_id}
        mock_agent2 = Mock()
        mock_agent2.known_kernel_ids = set()

        mock_agent_server.agents = {
            AgentId("agent-1"): mock_agent1,
            AgentId("agent-2"): mock_agent2,
        }

        result = mock_agent_server._find_agent(kernel_id=kernel_id, throw_error=False)

        assert result is mock_agent1

    def test_find_agent_by_kernel_id_no_match_returns_none(
        self, mock_agent_server: AgentRPCServer
    ) -> None:
        kernel_id = KernelId(uuid4())
        mock_agent1 = Mock()
        mock_agent1.known_kernel_ids = set()
        mock_agent2 = Mock()
        mock_agent2.known_kernel_ids = set()

        mock_agent_server.agents = {
            AgentId("agent-1"): mock_agent1,
            AgentId("agent-2"): mock_agent2,
        }

        result = mock_agent_server._find_agent(kernel_id=kernel_id, throw_error=False)

        assert result is None

    def test_find_agent_by_kernel_id_no_match_raises_error(
        self, mock_agent_server: AgentRPCServer
    ) -> None:
        kernel_id = KernelId(uuid4())
        mock_agent1 = Mock()
        mock_agent1.known_kernel_ids = set()
        mock_agent2 = Mock()
        mock_agent2.known_kernel_ids = set()

        mock_agent_server.agents = {
            AgentId("agent-1"): mock_agent1,
            AgentId("agent-2"): mock_agent2,
        }

        with pytest.raises(RuntimeError, match="No agent found"):
            mock_agent_server._find_agent(kernel_id=kernel_id, throw_error=True)

    def test_find_agent_by_kernel_id_multiple_matches_raises_error(
        self, mock_agent_server: AgentRPCServer
    ) -> None:
        kernel_id = KernelId(uuid4())
        mock_agent1 = Mock()
        mock_agent1.known_kernel_ids = {kernel_id}
        mock_agent2 = Mock()
        mock_agent2.known_kernel_ids = {kernel_id}

        mock_agent_server.agents = {
            AgentId("agent-1"): mock_agent1,
            AgentId("agent-2"): mock_agent2,
        }

        with pytest.raises(RuntimeError, match="More than one agent found"):
            mock_agent_server._find_agent(kernel_id=kernel_id, throw_error=False)

    def test_find_agent_by_image_name_single_match(self, mock_agent_server: AgentRPCServer) -> None:
        mock_agent1 = Mock()
        mock_agent1.known_kernel_ids = set()
        mock_agent1.known_image_names = {"test-image"}
        mock_agent2 = Mock()
        mock_agent2.known_kernel_ids = set()
        mock_agent2.known_image_names = set()

        mock_agent_server.agents = {
            AgentId("agent-1"): mock_agent1,
            AgentId("agent-2"): mock_agent2,
        }

        result = mock_agent_server._find_agent(image_name="test-image", throw_error=False)

        assert result is mock_agent1

    def test_find_agent_by_multiple_kernel_ids(self, mock_agent_server: AgentRPCServer) -> None:
        kernel_id1 = KernelId(uuid4())
        kernel_id2 = KernelId(uuid4())
        mock_agent1 = Mock()
        mock_agent1.known_kernel_ids = {kernel_id1, kernel_id2}
        mock_agent2 = Mock()
        mock_agent2.known_kernel_ids = {kernel_id1}

        mock_agent_server.agents = {
            AgentId("agent-1"): mock_agent1,
            AgentId("agent-2"): mock_agent2,
        }

        result = mock_agent_server._find_agent(
            kernel_id={kernel_id1, kernel_id2}, throw_error=False
        )

        assert result is mock_agent1

    def test_find_agent_by_kernel_and_image_filters_correctly(
        self, mock_agent_server: AgentRPCServer
    ) -> None:
        kernel_id = KernelId(uuid4())
        mock_agent1 = Mock()
        mock_agent1.known_kernel_ids = {kernel_id}
        mock_agent1.known_image_names = {"test-image"}
        mock_agent2 = Mock()
        mock_agent2.known_kernel_ids = {kernel_id}
        mock_agent2.known_image_names = set()

        mock_agent_server.agents = {
            AgentId("agent-1"): mock_agent1,
            AgentId("agent-2"): mock_agent2,
        }

        result = mock_agent_server._find_agent(
            kernel_id=kernel_id, image_name="test-image", throw_error=False
        )

        assert result is mock_agent1


class TestAgentRPCServerConfigInheritance:
    def test_single_agent_inherits_global_config(
        self,
        single_agent_config: AgentUnifiedConfig,
    ) -> None:
        assert len(single_agent_config.agent_configs) == 1
        config = single_agent_config.agent_configs[0]
        assert config.agent.backend == AgentBackend.DOCKER
        assert config.container.port_range == (30000, 31000)

    def test_multi_agent_configs_use_overrides(
        self,
        multi_agent_config: AgentUnifiedConfig,
    ) -> None:
        assert len(multi_agent_config.agent_configs) == 2

        config1 = multi_agent_config.agent_configs[0]
        assert config1.agent.id == "agent-1"
        assert config1.agent.kernel_creation_concurrency == 8
        assert config1.agent.agent_sock_port == 6008
        assert config1.container.port_range == (31000, 32000)
        assert config1.resource.reserved_cpu == 2
        assert config1.resource.reserved_mem == 2 * (1024**3)
        assert config1.resource.reserved_disk == 16 * (1024**3)

        config2 = multi_agent_config.agent_configs[1]
        assert config2.agent.id == "agent-2"
        assert config2.agent.kernel_creation_concurrency == 6
        assert config2.agent.agent_sock_port == 6009
        assert config2.container.port_range == (32000, 33000)
        assert config2.resource.reserved_cpu == 1
        assert config2.resource.reserved_mem == 512 * (1024**2)
        assert config2.resource.reserved_disk == 4 * (1024**3)
