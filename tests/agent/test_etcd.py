from __future__ import annotations

from typing import AsyncGenerator
from unittest.mock import AsyncMock, Mock

import pytest

from ai.backend.agent.config.unified import AgentUnifiedConfig
from ai.backend.agent.etcd import AgentEtcdClientView
from ai.backend.common import config
from ai.backend.common.etcd import AsyncEtcd, ConfigScopes, Event, GetPrefixValue
from ai.backend.common.types import QueueSentinel


@pytest.fixture
def mock_etcd() -> AsyncMock:
    """Create a mock AsyncEtcd instance."""
    mock = AsyncMock(spec=AsyncEtcd)
    return mock


@pytest.fixture
def agent_config() -> AgentUnifiedConfig:
    raw_config = {
        "agent": {
            "id": "test-agent-id",
            "scaling-group": "test-sgroup",
            "region": "test-region",
            "ipc-base-path": "/tmp/test-ipc",
            "var-base-path": "/tmp/test-var",
            "mount-path": "/tmp/test-mount",
            "backend": "docker",
            "rpc-listen-addr": "127.0.0.1:6001",
            "agent-sock-port": 6002,
        },
        "container": {
            "scratch-type": "hostdir",
            "stats-type": "docker",
            "port-range": [10000, 11000],
        },
        "resource": {
            "reserved-cpu": 1,
            "reserved-mem": "256M",
            "reserved-disk": "1G",
        },
        "logging": {
            "level": "INFO",
            "drivers": ["console"],
        },
        "etcd": {
            "addr": "127.0.0.1:2379",
            "namespace": "test-ns",
        },
        "redis": {
            "addr": "127.0.0.1:6379",
            "sentinel": None,
            "service_name": None,
            "password": None,
            "redis_helper_config": config.redis_helper_default_config,
        },
    }
    return AgentUnifiedConfig.model_validate(raw_config)


@pytest.fixture
def etcd_view(mock_etcd: AsyncMock, agent_config: AgentUnifiedConfig) -> AgentEtcdClientView:
    """Create an AgentEtcdClientView instance."""
    return AgentEtcdClientView(mock_etcd, agent_config)


class TestAgentEtcdClientViewInitialization:
    def test_initialization(
        self,
        mock_etcd: AsyncMock,
        agent_config: AgentUnifiedConfig,
    ) -> None:
        """Test that AgentEtcdClientView initializes correctly."""
        view = AgentEtcdClientView(mock_etcd, agent_config)

        assert view._etcd is mock_etcd
        assert view._config is agent_config


class TestPutOperations:
    @pytest.mark.asyncio
    async def test_put(
        self,
        etcd_view: AgentEtcdClientView,
        mock_etcd: AsyncMock,
        agent_config: AgentUnifiedConfig,
    ) -> None:
        """Test that put augments scope_prefix_map and delegates to underlying etcd."""
        key = "test/key"
        val = "test-value"
        scope = ConfigScopes.GLOBAL

        await etcd_view.put(key, val, scope=scope)

        mock_etcd.put.assert_called_once()
        call_args = mock_etcd.put.call_args
        assert call_args.args == (key, val)
        assert call_args.kwargs["scope"] == scope

        scope_prefix_map = call_args.kwargs["scope_prefix_map"]
        assert ConfigScopes.SGROUP in scope_prefix_map
        assert ConfigScopes.NODE in scope_prefix_map
        assert scope_prefix_map[ConfigScopes.SGROUP] == f"sgroup/{agent_config.agent.scaling_group}"
        assert scope_prefix_map[ConfigScopes.NODE] == f"nodes/agents/{agent_config.agent.id}"

    @pytest.mark.asyncio
    async def test_put_with_custom_scope_prefix_map(
        self,
        etcd_view: AgentEtcdClientView,
        mock_etcd: AsyncMock,
    ) -> None:
        """Test that put preserves custom scope_prefix_map entries."""
        key = "test/key"
        val = "test-value"
        custom_map = {ConfigScopes.GLOBAL: "custom/global"}

        await etcd_view.put(key, val, scope_prefix_map=custom_map)

        mock_etcd.put.assert_called_once()
        call_args = mock_etcd.put.call_args
        scope_prefix_map = call_args.kwargs["scope_prefix_map"]
        assert scope_prefix_map[ConfigScopes.GLOBAL] == "custom/global"
        assert ConfigScopes.SGROUP in scope_prefix_map
        assert ConfigScopes.NODE in scope_prefix_map

    @pytest.mark.asyncio
    async def test_put_prefix(
        self,
        etcd_view: AgentEtcdClientView,
        mock_etcd: AsyncMock,
    ) -> None:
        """Test that put_prefix augments scope_prefix_map and delegates to underlying etcd."""
        key = "test/prefix"
        dict_obj = {"nested": {"key": "value"}}
        scope = ConfigScopes.SGROUP

        await etcd_view.put_prefix(key, dict_obj, scope=scope)

        mock_etcd.put_prefix.assert_called_once()
        call_args = mock_etcd.put_prefix.call_args
        assert call_args.args == (key, dict_obj)
        assert call_args.kwargs["scope"] == scope

        scope_prefix_map = call_args.kwargs["scope_prefix_map"]
        assert ConfigScopes.SGROUP in scope_prefix_map
        assert ConfigScopes.NODE in scope_prefix_map

    @pytest.mark.asyncio
    async def test_put_dict(
        self,
        etcd_view: AgentEtcdClientView,
        mock_etcd: AsyncMock,
    ) -> None:
        """Test that put_dict augments scope_prefix_map and delegates to underlying etcd."""
        flattened_dict = {"key1": "val1", "key2": "val2"}
        scope = ConfigScopes.NODE

        await etcd_view.put_dict(flattened_dict, scope=scope)

        mock_etcd.put_dict.assert_called_once()
        call_args = mock_etcd.put_dict.call_args
        assert call_args.args == (flattened_dict,)
        assert call_args.kwargs["scope"] == scope

        scope_prefix_map = call_args.kwargs["scope_prefix_map"]
        assert ConfigScopes.SGROUP in scope_prefix_map
        assert ConfigScopes.NODE in scope_prefix_map


class TestGetOperations:
    @pytest.mark.asyncio
    async def test_get(
        self,
        etcd_view: AgentEtcdClientView,
        mock_etcd: AsyncMock,
    ) -> None:
        """Test that get augments scope_prefix_map and delegates to underlying etcd."""
        key = "test/key"
        expected_value = "test-value"
        mock_etcd.get.return_value = expected_value

        result = await etcd_view.get(key)

        assert result == expected_value
        mock_etcd.get.assert_called_once()
        call_args = mock_etcd.get.call_args
        assert call_args.args == (key,)

        scope_prefix_map = call_args.kwargs["scope_prefix_map"]
        assert ConfigScopes.SGROUP in scope_prefix_map
        assert ConfigScopes.NODE in scope_prefix_map

    @pytest.mark.asyncio
    async def test_get_with_scope(
        self,
        etcd_view: AgentEtcdClientView,
        mock_etcd: AsyncMock,
    ) -> None:
        """Test that get passes scope correctly."""
        key = "test/key"
        scope = ConfigScopes.SGROUP
        mock_etcd.get.return_value = "value"

        await etcd_view.get(key, scope=scope)

        call_args = mock_etcd.get.call_args
        assert call_args.kwargs["scope"] == scope

    @pytest.mark.asyncio
    async def test_get_prefix(
        self,
        etcd_view: AgentEtcdClientView,
        mock_etcd: AsyncMock,
    ) -> None:
        """Test that get_prefix augments scope_prefix_map and delegates to underlying etcd."""
        key_prefix = "test/prefix"
        expected_result: GetPrefixValue = {}
        mock_etcd.get_prefix.return_value = expected_result

        result = await etcd_view.get_prefix(key_prefix)

        assert result == expected_result
        mock_etcd.get_prefix.assert_called_once()
        call_args = mock_etcd.get_prefix.call_args
        assert call_args.args == (key_prefix,)

        scope_prefix_map = call_args.kwargs["scope_prefix_map"]
        assert ConfigScopes.SGROUP in scope_prefix_map
        assert ConfigScopes.NODE in scope_prefix_map


class TestReplaceOperation:
    @pytest.mark.asyncio
    async def test_replace(
        self,
        etcd_view: AgentEtcdClientView,
        mock_etcd: AsyncMock,
    ) -> None:
        """Test that replace augments scope_prefix_map and delegates to underlying etcd."""
        key = "test/key"
        initial_val = "old-value"
        new_val = "new-value"
        mock_etcd.replace.return_value = True

        result = await etcd_view.replace(key, initial_val, new_val)

        assert result is True
        mock_etcd.replace.assert_called_once()
        call_args = mock_etcd.replace.call_args
        assert call_args.args == (key, initial_val, new_val)

        scope_prefix_map = call_args.kwargs["scope_prefix_map"]
        assert ConfigScopes.SGROUP in scope_prefix_map
        assert ConfigScopes.NODE in scope_prefix_map

    @pytest.mark.asyncio
    async def test_replace_with_scope(
        self,
        etcd_view: AgentEtcdClientView,
        mock_etcd: AsyncMock,
    ) -> None:
        """Test that replace passes scope correctly."""
        key = "test/key"
        initial_val = "old"
        new_val = "new"
        scope = ConfigScopes.NODE
        mock_etcd.replace.return_value = False

        result = await etcd_view.replace(key, initial_val, new_val, scope=scope)

        assert result is False
        call_args = mock_etcd.replace.call_args
        assert call_args.kwargs["scope"] == scope


class TestDeleteOperations:
    @pytest.mark.asyncio
    async def test_delete(
        self,
        etcd_view: AgentEtcdClientView,
        mock_etcd: AsyncMock,
    ) -> None:
        """Test that delete augments scope_prefix_map and delegates to underlying etcd."""
        key = "test/key"

        await etcd_view.delete(key)

        mock_etcd.delete.assert_called_once()
        call_args = mock_etcd.delete.call_args
        assert call_args.args == (key,)

        scope_prefix_map = call_args.kwargs["scope_prefix_map"]
        assert ConfigScopes.SGROUP in scope_prefix_map
        assert ConfigScopes.NODE in scope_prefix_map

    @pytest.mark.asyncio
    async def test_delete_with_scope(
        self,
        etcd_view: AgentEtcdClientView,
        mock_etcd: AsyncMock,
    ) -> None:
        """Test that delete passes scope correctly."""
        key = "test/key"
        scope = ConfigScopes.SGROUP

        await etcd_view.delete(key, scope=scope)

        call_args = mock_etcd.delete.call_args
        assert call_args.kwargs["scope"] == scope

    @pytest.mark.asyncio
    async def test_delete_multi(
        self,
        etcd_view: AgentEtcdClientView,
        mock_etcd: AsyncMock,
    ) -> None:
        """Test that delete_multi augments scope_prefix_map and delegates to underlying etcd."""
        keys = ["key1", "key2", "key3"]

        await etcd_view.delete_multi(keys)

        mock_etcd.delete_multi.assert_called_once()
        call_args = mock_etcd.delete_multi.call_args
        assert call_args.args == (keys,)

        scope_prefix_map = call_args.kwargs["scope_prefix_map"]
        assert ConfigScopes.SGROUP in scope_prefix_map
        assert ConfigScopes.NODE in scope_prefix_map

    @pytest.mark.asyncio
    async def test_delete_prefix(
        self,
        etcd_view: AgentEtcdClientView,
        mock_etcd: AsyncMock,
    ) -> None:
        """Test that delete_prefix augments scope_prefix_map and delegates to underlying etcd."""
        key_prefix = "test/prefix"

        await etcd_view.delete_prefix(key_prefix)

        mock_etcd.delete_prefix.assert_called_once()
        call_args = mock_etcd.delete_prefix.call_args
        assert call_args.args == (key_prefix,)

        scope_prefix_map = call_args.kwargs["scope_prefix_map"]
        assert ConfigScopes.SGROUP in scope_prefix_map
        assert ConfigScopes.NODE in scope_prefix_map


class TestWatchOperations:
    @pytest.mark.asyncio
    async def test_watch(
        self,
        etcd_view: AgentEtcdClientView,
        mock_etcd: AsyncMock,
    ) -> None:
        """Test that watch augments scope_prefix_map and delegates to underlying etcd."""
        key = "test/key"

        # Create a mock async generator
        async def mock_watch_generator() -> AsyncGenerator[QueueSentinel | Event, None]:
            yield Mock(spec=Event)

        mock_etcd.watch.return_value = mock_watch_generator()

        # Consume the generator
        events = []
        async for event in etcd_view.watch(key):
            events.append(event)

        mock_etcd.watch.assert_called_once()
        call_args = mock_etcd.watch.call_args
        assert call_args.args == (key,)

        scope_prefix_map = call_args.kwargs["scope_prefix_map"]
        assert ConfigScopes.SGROUP in scope_prefix_map
        assert ConfigScopes.NODE in scope_prefix_map
        assert len(events) == 1

    @pytest.mark.asyncio
    async def test_watch_with_options(
        self,
        etcd_view: AgentEtcdClientView,
        mock_etcd: AsyncMock,
    ) -> None:
        """Test that watch passes all options correctly."""
        key = "test/key"
        scope = ConfigScopes.NODE

        async def mock_watch_generator() -> AsyncGenerator[QueueSentinel | Event, None]:
            return
            yield  # Make this a generator

        mock_etcd.watch.return_value = mock_watch_generator()

        async for _ in etcd_view.watch(
            key,
            scope=scope,
            once=True,
            wait_timeout=5.0,
        ):
            pass

        call_args = mock_etcd.watch.call_args
        assert call_args.kwargs["scope"] == scope
        assert call_args.kwargs["once"] is True
        assert call_args.kwargs["wait_timeout"] == 5.0

    @pytest.mark.asyncio
    async def test_watch_prefix(
        self,
        etcd_view: AgentEtcdClientView,
        mock_etcd: AsyncMock,
    ) -> None:
        """Test that watch_prefix augments scope_prefix_map and delegates to underlying etcd."""
        key_prefix = "test/prefix"

        # Create a mock async generator
        async def mock_watch_prefix_generator() -> AsyncGenerator[QueueSentinel | Event, None]:
            yield Mock(spec=Event)
            yield Mock(spec=Event)

        mock_etcd.watch_prefix.return_value = mock_watch_prefix_generator()

        # Consume the generator
        events = []
        async for event in etcd_view.watch_prefix(key_prefix):
            events.append(event)

        mock_etcd.watch_prefix.assert_called_once()
        call_args = mock_etcd.watch_prefix.call_args
        assert call_args.args == (key_prefix,)

        scope_prefix_map = call_args.kwargs["scope_prefix_map"]
        assert ConfigScopes.SGROUP in scope_prefix_map
        assert ConfigScopes.NODE in scope_prefix_map
        assert len(events) == 2

    @pytest.mark.asyncio
    async def test_watch_prefix_with_options(
        self,
        etcd_view: AgentEtcdClientView,
        mock_etcd: AsyncMock,
    ) -> None:
        """Test that watch_prefix passes all options correctly."""
        key_prefix = "test/prefix"
        scope = ConfigScopes.SGROUP

        async def mock_watch_prefix_generator() -> AsyncGenerator[QueueSentinel | Event, None]:
            return
            yield  # Make this a generator

        mock_etcd.watch_prefix.return_value = mock_watch_prefix_generator()

        async for _ in etcd_view.watch_prefix(
            key_prefix,
            scope=scope,
            once=False,
            wait_timeout=10.0,
        ):
            pass

        call_args = mock_etcd.watch_prefix.call_args
        assert call_args.kwargs["scope"] == scope
        assert call_args.kwargs["once"] is False
        assert call_args.kwargs["wait_timeout"] == 10.0


class TestConfigContainerUpdates:
    @pytest.mark.asyncio
    async def test_config_container_updates_reflect_in_scope_prefix_map(
        self,
        mock_etcd: AsyncMock,
        agent_config: AgentUnifiedConfig,
    ) -> None:
        """Test that changes to config container are reflected in scope prefix map."""
        # Create initial config container
        agent_config.update(agent_update={"id": "agent-1", "scaling_group": "sgroup-1"})
        view = AgentEtcdClientView(mock_etcd, agent_config)

        # First call
        await view.put("key", "value")
        first_call_args = mock_etcd.put.call_args
        first_scope_prefix_map = first_call_args.kwargs["scope_prefix_map"]

        assert first_scope_prefix_map[ConfigScopes.SGROUP] == "sgroup/sgroup-1"
        assert first_scope_prefix_map[ConfigScopes.NODE] == "nodes/agents/agent-1"

        # Update config container (simulating config reload with new config object)
        agent_config.update(agent_update={"scaling_group": "sgroup-2"})

        # Second call should reflect new values
        await view.put("key2", "value2")
        second_call_args = mock_etcd.put.call_args
        second_scope_prefix_map = second_call_args.kwargs["scope_prefix_map"]

        assert second_scope_prefix_map[ConfigScopes.SGROUP] == "sgroup/sgroup-2"
