from __future__ import annotations

from typing import Any

import pytest

from ai.backend.agent.config.unified import AgentUnifiedConfig
from ai.backend.agent.etcd import AgentEtcdClientView
from ai.backend.common import config
from ai.backend.common.etcd import AsyncEtcd, ConfigScopes


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
async def agent_etcd_view(
    etcd: AsyncEtcd,
    agent_config: AgentUnifiedConfig,
) -> AgentEtcdClientView:
    """Create an AgentEtcdClientView instance with real etcd for integration tests."""
    return AgentEtcdClientView(etcd, agent_config)


class TestAgentEtcdClientViewInitialization:
    def test_initialization(
        self,
        etcd: AsyncEtcd,
        agent_config: AgentUnifiedConfig,
    ) -> None:
        """Test that AgentEtcdClientView initializes correctly."""
        view = AgentEtcdClientView(etcd, agent_config)

        assert view._etcd is etcd
        assert view._config is agent_config


class TestPutOperations:
    @pytest.mark.asyncio
    async def test_put(
        self,
        agent_etcd_view: AgentEtcdClientView,
    ) -> None:
        """Test that put works and scope augmentation is applied correctly."""
        key = "test/put/key"
        val = "test-value"
        scope = ConfigScopes.GLOBAL

        await agent_etcd_view.put(key, val, scope=scope)

        # Verify the value was stored
        result = await agent_etcd_view.get(key, scope=scope)
        assert result == val

    @pytest.mark.asyncio
    async def test_put_with_different_scopes(
        self,
        agent_etcd_view: AgentEtcdClientView,
    ) -> None:
        """Test that put works with different scopes."""
        key = "test/put/scoped"
        global_val = "global-value"
        sgroup_val = "sgroup-value"
        node_val = "node-value"

        # Put in different scopes
        await agent_etcd_view.put(key, global_val, scope=ConfigScopes.GLOBAL)
        await agent_etcd_view.put(key, sgroup_val, scope=ConfigScopes.SGROUP)
        await agent_etcd_view.put(key, node_val, scope=ConfigScopes.NODE)

        # Verify each scope has its own value
        assert await agent_etcd_view.get(key, scope=ConfigScopes.GLOBAL) == global_val
        assert await agent_etcd_view.get(key, scope=ConfigScopes.SGROUP) == sgroup_val
        assert await agent_etcd_view.get(key, scope=ConfigScopes.NODE) == node_val

    @pytest.mark.asyncio
    async def test_put_prefix(
        self,
        agent_etcd_view: AgentEtcdClientView,
    ) -> None:
        """Test that put_prefix works correctly."""
        key = "test/putprefix"
        dict_obj: dict[str, Any] = {"nested": {"key": "value"}, "another": "data"}
        scope = ConfigScopes.SGROUP

        await agent_etcd_view.put_prefix(key, dict_obj, scope=scope)

        # Verify the nested structure was stored
        # get_prefix returns keys without the prefix, and nested dicts remain nested
        result = await agent_etcd_view.get_prefix(key, scope=scope)
        assert result.get("another") == "data"
        nested = result.get("nested")
        assert isinstance(nested, dict)
        assert nested.get("key") == "value"

    @pytest.mark.asyncio
    async def test_put_dict(
        self,
        agent_etcd_view: AgentEtcdClientView,
    ) -> None:
        """Test that put_dict works correctly."""
        flattened_dict = {"key1": "val1", "key2": "val2"}
        scope = ConfigScopes.NODE

        await agent_etcd_view.put_dict(flattened_dict, scope=scope)

        # Verify the values were stored
        assert await agent_etcd_view.get("key1", scope=scope) == "val1"
        assert await agent_etcd_view.get("key2", scope=scope) == "val2"


class TestGetOperations:
    @pytest.mark.asyncio
    async def test_get(
        self,
        agent_etcd_view: AgentEtcdClientView,
    ) -> None:
        """Test that get retrieves stored values."""
        key = "test/get/key"
        expected_value = "test-value"

        await agent_etcd_view.put(key, expected_value)
        result = await agent_etcd_view.get(key)

        assert result == expected_value

    @pytest.mark.asyncio
    async def test_get_with_scope(
        self,
        agent_etcd_view: AgentEtcdClientView,
    ) -> None:
        """Test that get respects scope hierarchy (NODE scope inherits from SGROUP and GLOBAL)."""
        key = "test/get/scoped"
        sgroup_value = "sgroup-value"
        node_value = "node-value"

        # Put value in SGROUP scope
        await agent_etcd_view.put(key, sgroup_value, scope=ConfigScopes.SGROUP)

        # Reading from SGROUP should get SGROUP value
        result_sgroup = await agent_etcd_view.get(key, scope=ConfigScopes.SGROUP)
        assert result_sgroup == sgroup_value

        # Reading from NODE should inherit from SGROUP (NODE inherits SGROUP + GLOBAL)
        result_node_inherited = await agent_etcd_view.get(key, scope=ConfigScopes.NODE)
        assert result_node_inherited == sgroup_value

        # Put a value in NODE scope - it should override the SGROUP value
        await agent_etcd_view.put(key, node_value, scope=ConfigScopes.NODE)

        # Reading from NODE should now get NODE value (higher priority)
        result_node = await agent_etcd_view.get(key, scope=ConfigScopes.NODE)
        assert result_node == node_value

        # Reading from SGROUP should still get SGROUP value (unaffected by NODE)
        result_sgroup_after = await agent_etcd_view.get(key, scope=ConfigScopes.SGROUP)
        assert result_sgroup_after == sgroup_value

    @pytest.mark.asyncio
    async def test_get_prefix(
        self,
        agent_etcd_view: AgentEtcdClientView,
    ) -> None:
        """Test that get_prefix retrieves all matching keys."""
        key_prefix = "test/getprefix"

        await agent_etcd_view.put(f"{key_prefix}/key1", "value1")
        await agent_etcd_view.put(f"{key_prefix}/key2", "value2")
        await agent_etcd_view.put("test/other", "other")

        result = await agent_etcd_view.get_prefix(key_prefix)

        assert len(result) == 2
        # get_prefix returns keys without the prefix
        assert result.get("key1") == "value1"
        assert result.get("key2") == "value2"
        assert "test/other" not in result
        assert "other" not in result


class TestReplaceOperation:
    @pytest.mark.asyncio
    async def test_replace(
        self,
        agent_etcd_view: AgentEtcdClientView,
    ) -> None:
        """Test that replace works correctly."""
        key = "test/replace/key"
        initial_val = "old-value"
        new_val = "new-value"

        await agent_etcd_view.put(key, initial_val)
        result = await agent_etcd_view.replace(key, initial_val, new_val)

        assert result is True
        assert await agent_etcd_view.get(key) == new_val

    @pytest.mark.asyncio
    async def test_replace_with_scope(
        self,
        agent_etcd_view: AgentEtcdClientView,
    ) -> None:
        """Test that replace respects scope."""
        key = "test/replace/scoped"
        initial_val = "old"
        new_val = "new"
        scope = ConfigScopes.NODE

        await agent_etcd_view.put(key, initial_val, scope=scope)
        result = await agent_etcd_view.replace(key, initial_val, new_val, scope=scope)

        assert result is True
        assert await agent_etcd_view.get(key, scope=scope) == new_val

    @pytest.mark.asyncio
    async def test_replace_with_wrong_initial_value(
        self,
        agent_etcd_view: AgentEtcdClientView,
    ) -> None:
        """Test that replace fails when initial value doesn't match."""
        key = "test/replace/fail"
        initial_val = "correct"
        wrong_val = "wrong"
        new_val = "new"

        await agent_etcd_view.put(key, initial_val)
        result = await agent_etcd_view.replace(key, wrong_val, new_val)

        assert result is False
        # Value should remain unchanged
        assert await agent_etcd_view.get(key) == initial_val


class TestDeleteOperations:
    @pytest.mark.asyncio
    async def test_delete(
        self,
        agent_etcd_view: AgentEtcdClientView,
    ) -> None:
        """Test that delete removes values."""
        key = "test/delete/key"
        value = "to-delete"

        await agent_etcd_view.put(key, value)
        await agent_etcd_view.delete(key)

        result = await agent_etcd_view.get(key)
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_with_scope(
        self,
        agent_etcd_view: AgentEtcdClientView,
    ) -> None:
        """Test that delete respects scope."""
        key = "test/delete/scoped"
        scope = ConfigScopes.SGROUP
        value = "scoped-value"

        await agent_etcd_view.put(key, value, scope=scope)
        await agent_etcd_view.delete(key, scope=scope)

        result = await agent_etcd_view.get(key, scope=scope)
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_multi(
        self,
        agent_etcd_view: AgentEtcdClientView,
    ) -> None:
        """Test that delete_multi removes multiple values."""
        keys = ["test/delmulti/key1", "test/delmulti/key2", "test/delmulti/key3"]

        for key in keys:
            await agent_etcd_view.put(key, "value")

        await agent_etcd_view.delete_multi(keys)

        for key in keys:
            result = await agent_etcd_view.get(key)
            assert result is None

    @pytest.mark.asyncio
    async def test_delete_prefix(
        self,
        agent_etcd_view: AgentEtcdClientView,
    ) -> None:
        """Test that delete_prefix removes all matching keys."""
        key_prefix = "test/delprefix"

        await agent_etcd_view.put(f"{key_prefix}/key1", "value1")
        await agent_etcd_view.put(f"{key_prefix}/key2", "value2")
        await agent_etcd_view.put("test/keep", "keep-value")

        await agent_etcd_view.delete_prefix(key_prefix)

        result = await agent_etcd_view.get_prefix(key_prefix)
        assert len(result) == 0

        # Verify other key is kept
        kept = await agent_etcd_view.get("test/keep")
        assert kept == "keep-value"


class TestConfigContainerUpdates:
    @pytest.mark.asyncio
    async def test_config_container_updates_reflect_in_scope_prefix_map(
        self,
        etcd: AsyncEtcd,
        agent_config: AgentUnifiedConfig,
    ) -> None:
        """Test that changes to config container are reflected in scope prefix map."""
        # Create initial config container
        agent_config.update(agent_update={"id": "agent-1", "scaling_group": "sgroup-1"})
        view = AgentEtcdClientView(etcd, agent_config)

        # First call
        key1 = "test/config/key1"
        await view.put(key1, "value1", scope=ConfigScopes.SGROUP)
        result1 = await view.get(key1, scope=ConfigScopes.SGROUP)
        assert result1 == "value1"

        # Update config container (simulating config reload with new config object)
        agent_config.update(agent_update={"scaling_group": "sgroup-2"})

        # Second call should use new scope prefix
        key2 = "test/config/key2"
        await view.put(key2, "value2", scope=ConfigScopes.SGROUP)
        result2 = await view.get(key2, scope=ConfigScopes.SGROUP)
        assert result2 == "value2"

        # The first key should not be accessible under the new scope
        result1_new_scope = await view.get(key1, scope=ConfigScopes.SGROUP)
        assert result1_new_scope is None
