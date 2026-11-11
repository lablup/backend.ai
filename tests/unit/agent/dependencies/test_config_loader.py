from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from ai.backend.agent.dependencies.bootstrap.config import (
    AgentConfigLoaderDependency,
    AgentConfigLoaderInput,
)
from ai.backend.common.exception import BackendAISchemaValidationFailed
from ai.backend.logging.types import LogLevel


def _rpc_auth_toml(rpc_auth_key_config: dict[str, Path]) -> str:
    return "\n".join(f'{key} = "{path}"' for key, path in rpc_auth_key_config.items())


class TestAgentConfigLoaderDependency:
    async def test_config_loader_loads_valid_config(
        self,
        tmp_path: Path,
        rpc_auth_key_config: dict[str, Path],
    ) -> None:
        """Test that config loader can load a valid config file."""
        config_path = tmp_path / "agent.toml"
        config_path.write_text(f"""
[agent]
id = "test-agent-123"
initial-resource-group-name = "test-group"
backend = "docker"
{_rpc_auth_toml(rpc_auth_key_config)}

[etcd]
namespace = "test"
addr = {{ host = "127.0.0.1", port = 2379 }}
user = "test"
password = "test"

[redis]
addr = {{ host = "127.0.0.1", port = 6379 }}

[container]
scratch-root = "/tmp/test"

[resource]
reserved-cpu = 1
""")

        loader = AgentConfigLoaderDependency()
        input_data = AgentConfigLoaderInput(
            config_path=config_path,
            log_level=LogLevel.DEBUG,
        )

        async with loader.provide(input_data) as config:
            assert config.agent.id == "test-agent-123"
            assert config.agent.initial_resource_group_name == "test-group"
            assert config.etcd.namespace == "test"
            assert config.container.scratch_root.resolve() == Path("/tmp/test").resolve()

    async def test_config_loader_applies_env_overrides(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        rpc_auth_key_config: dict[str, Path],
    ) -> None:
        """Test that config loader applies environment variable overrides."""
        config_path = tmp_path / "agent.toml"
        config_path.write_text(f"""
[agent]
id = "original-id"
initial-resource-group-name = "original-group"
backend = "docker"
{_rpc_auth_toml(rpc_auth_key_config)}

[etcd]
namespace = "original"
addr = {{ host = "127.0.0.1", port = 2379 }}
user = "test"
password = "test"

[redis]
addr = {{ host = "127.0.0.1", port = 6379 }}

[container]
scratch-root = "/tmp/original"

[resource]
reserved-cpu = 1
""")

        # Set environment variables
        monkeypatch.setenv("BACKEND_NAMESPACE", "override-namespace")
        monkeypatch.setenv("BACKEND_SCRATCH_ROOT", "/tmp/override")

        loader = AgentConfigLoaderDependency()
        input_data = AgentConfigLoaderInput(
            config_path=config_path,
            log_level=LogLevel.WARNING,
        )

        async with loader.provide(input_data) as config:
            # Environment overrides should be applied
            assert config.etcd.namespace == "override-namespace"
            assert config.container.scratch_root.resolve() == Path("/tmp/override").resolve()
            # Non-overridden values should remain
            assert config.agent.id == "original-id"

    async def test_config_loader_raises_on_invalid_config(self, tmp_path: Path) -> None:
        """Test that config loader raises ValidationError on invalid config."""
        config_path = tmp_path / "agent.toml"
        # Missing required fields
        config_path.write_text("""
[agent]
# Missing required fields
""")

        loader = AgentConfigLoaderDependency()
        input_data = AgentConfigLoaderInput(
            config_path=config_path,
            log_level=LogLevel.WARNING,
        )

        with pytest.raises((BackendAISchemaValidationFailed, ValidationError)):
            async with loader.provide(input_data):
                pass

    async def test_config_loader_with_debug_log_level(
        self,
        tmp_path: Path,
        rpc_auth_key_config: dict[str, Path],
    ) -> None:
        """Test that config loader respects log level in validation context."""
        config_path = tmp_path / "agent.toml"
        config_path.write_text(f"""
[agent]
id = "debug-test"
initial-resource-group-name = "default"
backend = "docker"
{_rpc_auth_toml(rpc_auth_key_config)}

[etcd]
namespace = "local"
addr = {{ host = "127.0.0.1", port = 2379 }}
user = "test"
password = "test"

[redis]
addr = {{ host = "127.0.0.1", port = 6379 }}

[container]
scratch-root = "/tmp/test"

[resource]
reserved-cpu = 1
""")

        loader = AgentConfigLoaderDependency()

        # Test with DEBUG level
        input_data = AgentConfigLoaderInput(
            config_path=config_path,
            log_level=LogLevel.DEBUG,
        )

        async with loader.provide(input_data) as config:
            # Config should be loaded successfully with debug context
            assert config.agent.id == "debug-test"
