from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from ai.backend.agent.dependencies.bootstrap.config import (
    AgentConfigLoaderDependency,
    AgentConfigLoaderInput,
)
from ai.backend.logging.types import LogLevel


class TestAgentConfigLoaderDependency:
    @pytest.mark.asyncio
    async def test_config_loader_loads_valid_config(self, tmp_path: Path) -> None:
        """Test that config loader can load a valid config file."""
        config_path = tmp_path / "agent.toml"
        config_path.write_text("""
[agent]
id = "test-agent-123"
scaling-group = "test-group"
backend = "docker"

[etcd]
namespace = "test"
addr = { host = "127.0.0.1", port = 2379 }

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
            assert config.agent.scaling_group == "test-group"
            assert config.etcd.namespace == "test"
            assert config.container.scratch_root.resolve() == Path("/tmp/test").resolve()

    @pytest.mark.asyncio
    async def test_config_loader_applies_env_overrides(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test that config loader applies environment variable overrides."""
        config_path = tmp_path / "agent.toml"
        config_path.write_text("""
[agent]
id = "original-id"
scaling-group = "original-group"
backend = "docker"

[etcd]
namespace = "original"
addr = { host = "127.0.0.1", port = 2379 }

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

    @pytest.mark.asyncio
    async def test_config_loader_raises_on_invalid_config(self, tmp_path: Path) -> None:
        """Test that config loader raises ValidationError on invalid config."""
        config_path = tmp_path / "agent.toml"
        # Missing required fields
        config_path.write_text("""
[agent]
# Missing id and scaling-group
""")

        loader = AgentConfigLoaderDependency()
        input_data = AgentConfigLoaderInput(
            config_path=config_path,
            log_level=LogLevel.WARNING,
        )

        with pytest.raises(ValidationError):
            async with loader.provide(input_data):
                pass

    @pytest.mark.asyncio
    async def test_config_loader_with_debug_log_level(self, tmp_path: Path) -> None:
        """Test that config loader respects log level in validation context."""
        config_path = tmp_path / "agent.toml"
        config_path.write_text("""
[agent]
id = "debug-test"
scaling-group = "default"
backend = "docker"

[etcd]
namespace = "local"
addr = { host = "127.0.0.1", port = 2379 }

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
