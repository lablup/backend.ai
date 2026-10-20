"""
Tests for agent configuration and RPC server functionality.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, Mock

import pytest

from ai.backend.agent.config.unified import (
    AgentConfig,
    AgentUnifiedConfig,
    ContainerConfig,
    ResourceConfig,
    ScratchType,
)
from ai.backend.agent.server import AgentRPCServer
from ai.backend.agent.types import AgentBackend
from ai.backend.common.configs.etcd import EtcdConfig
from ai.backend.common.configs.redis import RedisConfig
from ai.backend.common.typed_validators import HostPortPair


@pytest.fixture
def mock_etcd() -> Mock:
    """Create a mock etcd object with get_prefix method."""
    etcd = Mock()
    etcd.get_prefix = None
    return etcd


@pytest.fixture
def base_agent_config() -> AgentUnifiedConfig:
    """Create a base agent configuration for testing."""
    return AgentUnifiedConfig(  # type: ignore[call-arg]
        agent=AgentConfig(backend=AgentBackend.DOCKER),  # type: ignore[call-arg]
        container=ContainerConfig(scratch_type=ScratchType.HOSTDIR),  # type: ignore[call-arg]
        resource=ResourceConfig(),  # type: ignore[call-arg]
        etcd=EtcdConfig.model_validate({
            "namespace": "test",
            "addrs": [HostPortPair(host="127.0.0.1", port=2379)],
            "user": None,
            "password": None,
        }),
    )


@pytest.fixture
async def agent_rpc_server(
    mock_etcd: Mock, base_agent_config: AgentUnifiedConfig
) -> AgentRPCServer:
    """Create an AgentRPCServer instance for testing without initialization."""
    ars = AgentRPCServer(etcd=mock_etcd, local_config=base_agent_config, skip_detect_manager=True)

    # Mock the runtime object to return the etcd client
    runtime = Mock()
    runtime.get_etcd = lambda agent_id=None: mock_etcd
    ars.runtime = runtime

    return ars


class TestAgentConfigReading:
    """Tests for reading agent configuration from etcd."""

    @pytest.mark.parametrize(
        "etcd_response,expected_gid,expected_uid",
        [
            # Invalid responses - should use defaults
            ({"a": 1, "b": 2}, os.getgid(), os.getuid()),
            ({}, os.getgid(), os.getuid()),
            # Partial valid responses
            ({"kernel-gid": 10}, 10, os.getuid()),
            # Fully valid response
            ({"kernel-gid": 10, "kernel-uid": 20}, 10, 20),
        ],
        ids=["invalid_keys", "empty", "only_gid", "both_valid"],
    )
    async def test_read_agent_config_container(
        self,
        agent_rpc_server: AgentRPCServer,
        mocker: Any,
        etcd_response: dict[str, Any],
        expected_gid: int,
        expected_uid: int,
    ) -> None:
        """Test reading container config from etcd with various responses."""
        inspect_mock = AsyncMock(return_value=etcd_response)
        mocker.patch.object(agent_rpc_server.etcd, "get_prefix", new=inspect_mock)

        await agent_rpc_server.read_agent_config_container()

        assert agent_rpc_server.local_config.container.kernel_gid.real == expected_gid
        assert agent_rpc_server.local_config.container.kernel_uid.real == expected_uid

    @pytest.fixture
    def etcd_values(self, tmp_path: Path) -> dict[str, Any]:
        """Values etcd returns for single-key reads."""
        return {
            "volumes/_mount": str(tmp_path),
            "volumes/_fsprefix": "prefix",
        }

    @pytest.fixture
    def etcd_prefixes(self, tmp_path: Path) -> dict[str, dict[str, Any]]:
        """Subtrees etcd returns for prefix reads; the volumes tree holds a proxy secret."""
        return {
            "config/redis": {"addr": {"host": "etcd-redis", "port": "6379"}},
            "volumes": {
                "_mount": str(tmp_path),
                "_fsprefix": "prefix",
                "proxies": {"local": {"secret": "storage-proxy-secret"}},
            },
        }

    @pytest.fixture
    def etcd_mocks(
        self,
        agent_rpc_server: AgentRPCServer,
        mocker: Any,
        etcd_values: dict[str, Any],
        etcd_prefixes: dict[str, dict[str, Any]],
    ) -> tuple[AsyncMock, AsyncMock]:
        """Mock etcd get()/get_prefix() on the server's etcd; returns (get, get_prefix)."""

        async def get(key: str, **kwargs: Any) -> Any:
            return etcd_values.get(key)

        async def get_prefix(key: str, **kwargs: Any) -> dict[str, Any]:
            return etcd_prefixes.get(key, {})

        etcd_get = AsyncMock(side_effect=get)
        etcd_get_prefix = AsyncMock(side_effect=get_prefix)
        mocker.patch.object(agent_rpc_server.etcd, "get", new=etcd_get)
        mocker.patch.object(agent_rpc_server.etcd, "get_prefix", new=etcd_get_prefix)
        return etcd_get, etcd_get_prefix

    @pytest.fixture
    def local_redis_config(self) -> RedisConfig:
        """Redis config as given by a ``[redis]`` section in the local config."""
        return RedisConfig.model_validate({"addr": "local-redis:6390"})

    @pytest.fixture
    async def agent_rpc_server_with_local_redis(
        self,
        agent_rpc_server: AgentRPCServer,
        base_agent_config: AgentUnifiedConfig,
        local_redis_config: RedisConfig,
        etcd_mocks: tuple[AsyncMock, AsyncMock],
    ) -> AgentRPCServer:
        """Agent server whose local config has a [redis] section."""
        base_agent_config.redis = local_redis_config
        return AgentRPCServer(
            etcd=agent_rpc_server.etcd, local_config=base_agent_config, skip_detect_manager=True
        )

    async def test_vfolder_config_does_not_read_volumes_prefix(
        self,
        agent_rpc_server: AgentRPCServer,
        etcd_mocks: tuple[AsyncMock, AsyncMock],
        tmp_path: Path,
    ) -> None:
        """Test that only volumes/_mount and volumes/_fsprefix are read, never the volumes prefix."""
        etcd_get, etcd_get_prefix = etcd_mocks

        await agent_rpc_server.read_agent_config()

        assert agent_rpc_server._vfolder_config["mount"] == tmp_path.resolve()
        assert agent_rpc_server._vfolder_config["fsprefix"] == Path("prefix")
        assert "proxies" not in agent_rpc_server._vfolder_config
        assert "volumes" not in [call.args[0] for call in etcd_get_prefix.call_args_list]
        assert sorted(call.args[0] for call in etcd_get.call_args_list) == [
            "volumes/_fsprefix",
            "volumes/_mount",
        ]

    @pytest.mark.parametrize("etcd_values", [{}])
    async def test_vfolder_config_defaults_when_keys_missing(
        self,
        agent_rpc_server: AgentRPCServer,
        etcd_mocks: tuple[AsyncMock, AsyncMock],
    ) -> None:
        """Test that a missing mount and fsprefix fall back to the defaults."""
        await agent_rpc_server.read_agent_config()

        assert agent_rpc_server._vfolder_config["mount"] is None
        assert agent_rpc_server._vfolder_config["fsprefix"] == Path(".")

    async def test_redis_config_read_from_etcd_when_not_in_local_config(
        self,
        agent_rpc_server: AgentRPCServer,
        etcd_mocks: tuple[AsyncMock, AsyncMock],
    ) -> None:
        """Test that redis config is read from etcd when the local config has no [redis]."""
        _, etcd_get_prefix = etcd_mocks

        await agent_rpc_server.read_agent_config()

        assert agent_rpc_server.local_config.redis is not None
        assert agent_rpc_server.local_config.redis.addr is not None
        assert agent_rpc_server.local_config.redis.addr.address == "etcd-redis:6379"
        assert "config/redis" in [call.args[0] for call in etcd_get_prefix.call_args_list]

    async def test_local_redis_config_wins_over_etcd_across_repeated_reads(
        self,
        agent_rpc_server_with_local_redis: AgentRPCServer,
        local_redis_config: RedisConfig,
        etcd_mocks: tuple[AsyncMock, AsyncMock],
    ) -> None:
        """Test that a local [redis] section is kept when read_agent_config() runs twice."""
        _, etcd_get_prefix = etcd_mocks

        # read_agent_config() runs twice at startup (also from service_discovery_ctx).
        await agent_rpc_server_with_local_redis.read_agent_config()
        await agent_rpc_server_with_local_redis.read_agent_config()

        assert agent_rpc_server_with_local_redis.local_config.redis is local_redis_config
        assert "config/redis" not in [call.args[0] for call in etcd_get_prefix.call_args_list]
