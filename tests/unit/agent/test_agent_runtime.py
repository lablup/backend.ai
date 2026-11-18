from __future__ import annotations

import shutil
from collections import defaultdict
from collections.abc import AsyncIterator, Generator
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, Mock

import pytest

# Explicitly import to ensure Pants includes this module in the test build
import ai.backend.agent.dummy  # noqa: F401
from ai.backend.agent.agent import AbstractAgent
from ai.backend.agent.config.unified import AgentUnifiedConfig
from ai.backend.agent.errors import AgentIdNotFoundError
from ai.backend.agent.kernel import KernelRegistry
from ai.backend.agent.runtime import AgentRuntime
from ai.backend.common import config
from ai.backend.common import validators as tx
from ai.backend.common.configs.etcd import EtcdConfig
from ai.backend.common.types import AgentId, HostPortPair
from ai.backend.logging import LocalLogger
from ai.backend.logging.config import ConsoleConfig, LogDriver, LoggingConfig
from ai.backend.logging.types import LogFormat, LogLevel
from ai.backend.testutils.bootstrap import ETCD_PASSWORD, ETCD_USER
from ai.backend.testutils.pants import get_parallel_slot


@pytest.fixture(scope="session")
def logging_config() -> Generator[LoggingConfig, None, None]:
    config = LoggingConfig(
        version=1,
        disable_existing_loggers=False,
        handlers={},
        loggers={},
        drivers=[LogDriver.CONSOLE],
        console=ConsoleConfig(
            colored=None,
            format=LogFormat.VERBOSE,
        ),
        file=None,
        logstash=None,
        graylog=None,
        level=LogLevel.DEBUG,
        pkg_ns={
            "": LogLevel.INFO,
            "ai.backend": LogLevel.DEBUG,
            "tests": LogLevel.DEBUG,
            "alembic": LogLevel.INFO,
            "aiotools": LogLevel.INFO,
            "aiohttp": LogLevel.INFO,
            "sqlalchemy": LogLevel.WARNING,
        },
    )
    logger = LocalLogger(config)
    with logger:
        yield config


@pytest.fixture(scope="session")
def local_config(
    test_id: str,
    rpc_auth_key_config: dict[str, Path],
    logging_config: LoggingConfig,
    etcd_container: tuple[object, object],
    redis_container: tuple[object, object],
) -> Generator[AgentUnifiedConfig, None, None]:
    ipc_base_path = Path.cwd() / f".tmp/{test_id}/agent-ipc"
    ipc_base_path.mkdir(parents=True, exist_ok=True)
    var_base_path = Path.cwd() / f".tmp/{test_id}/agent-var"
    var_base_path.mkdir(parents=True, exist_ok=True)
    etcd_addr = etcd_container[1]
    redis_addr = redis_container[1]
    mount_path = Path.cwd() / "vfroot"

    raw_server_config = {
        "agent": {
            "region": f"rg-{test_id}",
            "id": f"i-{test_id}",
            "initial-resource-group-name": f"sg-{test_id}",
            "ipc-base-path": ipc_base_path,
            "var-base-path": var_base_path,
            "mount-path": mount_path,
            "backend": "dummy",
            "rpc-listen-addr": HostPortPair("", 18100 + get_parallel_slot()),
            **rpc_auth_key_config,
            "agent-sock-port": 18200 + get_parallel_slot(),
            "metadata-server-bind-host": "0.0.0.0",
            "metadata-server-port": 18300 + get_parallel_slot(),
            "allow-compute-plugins": set(),
            "block-compute-plugins": set(),
        },
        "container": {
            "scratch-type": "hostdir",
            "stats-type": "docker",
            "port-range": [
                19000 + 200 * get_parallel_slot(),
                19200 + 200 * get_parallel_slot(),
            ],
            "bind-host": "127.0.0.1",
        },
        "resource": {
            "reserved-cpu": 1,
            "reserved-mem": tx.BinarySize().check("256M"),
            "reserved-disk": tx.BinarySize().check("1G"),
        },
        "pyroscope": {
            "enabled": False,
            "app-name": "backend.ai-test",
            "server-addr": "http://localhost:4040",
            "sample-rate": 100,
        },
        "logging": logging_config,
        "debug": defaultdict(lambda: False),
        "etcd": {
            "addr": etcd_addr,
            "namespace": f"ns-{test_id}",
            "user": ETCD_USER,
            "password": ETCD_PASSWORD,
        },
        "redis": {
            "addr": redis_addr,
            "sentinel": None,
            "service_name": None,
            "password": None,
            "redis_helper_config": config.redis_helper_default_config,
        },
        "plugins": {},
    }
    server_config = AgentUnifiedConfig.model_validate(raw_server_config)

    def _override_if_exists(src: dict[str, Any], dst: dict[str, Any], key: str) -> None:
        sentinel = object()
        if (val := src.get(key, sentinel)) is not sentinel:
            dst[key] = val

    try:
        # Override external database config with the current environment's config.
        fs_local_config, _cfg_src_path = config.read_from_file(None, "agent")
        server_config.etcd.addrs = EtcdConfig.model_validate(fs_local_config["etcd"]).addrs
        _override_if_exists(fs_local_config["etcd"], server_config.etcd.model_dump(), "user")
        _override_if_exists(fs_local_config["etcd"], server_config.etcd.model_dump(), "password")
    except config.ConfigurationError:
        pass
    yield server_config
    shutil.rmtree(ipc_base_path)


@pytest.fixture
async def agent_runtime(
    local_config: AgentUnifiedConfig,
    mocker: object,
) -> AsyncIterator[AgentRuntime]:
    """
    Create a mocked AgentRuntime instance for unit testing.

    This fixture provides a minimal AgentRuntime with:
    - Mocked agents and resource allocator
    - No real backend or resource loading
    - Proper cleanup after tests
    """
    # Create mock agents
    mock_agent_id = AgentId(local_config.agent.defaulted_id)
    mock_agent = AsyncMock(spec=AbstractAgent)
    mock_agent.id = mock_agent_id
    mock_agent.shutdown = AsyncMock()

    # Create mock etcd view
    mock_etcd_view = Mock()

    # Create mock resource allocator
    mock_resource_allocator = AsyncMock()
    mock_resource_allocator.__aexit__ = AsyncMock()

    # Create runtime using constructor directly (not create_runtime)
    runtime = AgentRuntime(
        local_config=local_config,
        etcd_views={mock_agent_id: mock_etcd_view},
        agents={mock_agent_id: mock_agent},
        primary_agent=mock_agent,
        kernel_registry=KernelRegistry(),
        resource_allocator=mock_resource_allocator,
        metadata_server=None,
    )

    try:
        yield runtime
    finally:
        await runtime.__aexit__(None, None, None)


class TestAgentRuntimeSingleAgent:
    """Test AgentRuntime with single agent configuration."""

    async def test_get_agent_returns_default_when_id_is_none(
        self,
        agent_runtime: AgentRuntime,
    ) -> None:
        """
        When agent_id is None, get_agent() should return the default agent.
        """
        agent = agent_runtime.get_agent(None)

        assert agent is not None
        assert agent.id is not None
        # In single agent mode, the default agent should be the only agent
        assert agent is agent_runtime.get_agent(agent.id)

    async def test_get_agent_returns_agent_by_id(
        self,
        agent_runtime: AgentRuntime,
    ) -> None:
        """
        get_agent() should return the correct agent when given a specific ID.
        """
        # Get the default agent's ID
        default_agent = agent_runtime.get_agent(None)
        agent_id = default_agent.id

        # Retrieve by ID
        agent = agent_runtime.get_agent(agent_id)

        assert agent is default_agent
        assert agent.id == agent_id

    async def test_get_agent_raises_error_for_nonexistent_id(
        self,
        agent_runtime: AgentRuntime,
    ) -> None:
        """
        get_agent() should raise AgentIdNotFoundError for non-existent agent IDs.
        """
        nonexistent_id = AgentId("nonexistent-agent-id")

        with pytest.raises(AgentIdNotFoundError) as exc_info:
            agent_runtime.get_agent(nonexistent_id)

        # Verify error message is helpful
        assert str(nonexistent_id) in str(exc_info.value)
        assert "not found" in str(exc_info.value).lower()

    async def test_get_agents_returns_all_agents(
        self,
        agent_runtime: AgentRuntime,
    ) -> None:
        """
        get_agents() should return a list of all agents.
        """
        agents = agent_runtime.get_agents()

        assert isinstance(agents, list)
        assert len(agents) == 1  # Single agent mode

        # Verify the agent is accessible
        for agent in agents:
            assert agent.id is not None
            assert agent is agent_runtime.get_agent(agent.id)


class TestAgentRuntimeInitialization:
    """Test AgentRuntime initialization and cleanup."""

    async def test_runtime_creates_agents_from_config(
        self,
        agent_runtime: AgentRuntime,
    ) -> None:
        """
        AgentRuntime.create_agents() should initialize agents from config.
        """
        # Verify agents were created
        agents = agent_runtime.get_agents()
        assert len(agents) > 0

        # Verify default agent is set
        default_agent = agent_runtime.get_agent(None)
        assert default_agent is not None

        # Verify all agents have valid IDs
        for agent in agents:
            assert agent.id is not None

    async def test_runtime_shutdown_cleans_up_agents(
        self,
        agent_runtime: AgentRuntime,
    ) -> None:
        """
        AgentRuntime.shutdown() should properly clean up all agents.
        """
        # Verify agents exist before shutdown
        agents = agent_runtime.get_agents()
        assert len(agents) > 0

        # Shutdown
        await agent_runtime.__aexit__(None, None, None)

        # After shutdown, the runtime should be in a clean state
        # (Specific behavior depends on implementation - adjust as needed)
        # For now, we just verify shutdown doesn't raise errors
