from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path

from ai.backend.agent.config.unified import AgentConfigValidationContext, AgentUnifiedConfig
from ai.backend.common import config as common_config
from ai.backend.common.dependencies import NonMonitorableDependencyProvider
from ai.backend.logging.types import LogLevel


@dataclass
class AgentConfigLoaderInput:
    """Input required for agent config loading.

    Contains only the essential parameters needed to load the config,
    matching server.py's main() function parameters.
    """

    config_path: Path | None = None
    log_level: LogLevel = LogLevel.NOTSET


class AgentConfigLoaderDependency(
    NonMonitorableDependencyProvider[AgentConfigLoaderInput, AgentUnifiedConfig]
):
    """Loads agent configuration exactly as server.py does.

    Matches the config loading behavior in server.py's main() function (lines 1598-1646):
    1. Read from file using config.read_from_file()
    2. Apply environment variable overrides (11 legacy env vars)
    3. Validate using AgentUnifiedConfig.model_validate()
    """

    @property
    def stage_name(self) -> str:
        return "config-loader"

    @asynccontextmanager
    async def provide(
        self, setup_input: AgentConfigLoaderInput
    ) -> AsyncIterator[AgentUnifiedConfig]:
        """Load and provide agent configuration.

        Args:
            setup_input: Input containing config path and log level

        Yields:
            Loaded and validated AgentUnifiedConfig

        Raises:
            ConfigurationError: If config file cannot be read
            ValidationError: If config fails validation
        """
        # Read config from file (same as server.py line 1600)
        raw_cfg, _cfg_src_path = common_config.read_from_file(setup_input.config_path, "agent")

        # Apply environment variable overrides (same as server.py lines 1610-1622)
        common_config.override_with_env(raw_cfg, ("etcd", "namespace"), "BACKEND_NAMESPACE")
        common_config.override_with_env(raw_cfg, ("etcd", "addr"), "BACKEND_ETCD_ADDR")
        common_config.override_with_env(raw_cfg, ("etcd", "user"), "BACKEND_ETCD_USER")
        common_config.override_with_env(raw_cfg, ("etcd", "password"), "BACKEND_ETCD_PASSWORD")
        common_config.override_with_env(
            raw_cfg, ("agent", "rpc-listen-addr", "host"), "BACKEND_AGENT_HOST_OVERRIDE"
        )
        common_config.override_with_env(
            raw_cfg, ("agent", "rpc-listen-addr", "port"), "BACKEND_AGENT_PORT"
        )
        common_config.override_with_env(raw_cfg, ("agent", "pid-file"), "BACKEND_PID_FILE")
        common_config.override_with_env(
            raw_cfg, ("container", "port-range"), "BACKEND_CONTAINER_PORT_RANGE"
        )
        common_config.override_with_env(
            raw_cfg, ("container", "bind-host"), "BACKEND_BIND_HOST_OVERRIDE"
        )
        common_config.override_with_env(
            raw_cfg, ("container", "sandbox-type"), "BACKEND_SANDBOX_TYPE"
        )
        common_config.override_with_env(
            raw_cfg, ("container", "scratch-root"), "BACKEND_SCRATCH_ROOT"
        )

        # Validate and create AgentUnifiedConfig (same as server.py lines 1628-1635)
        config = AgentUnifiedConfig.model_validate(
            raw_cfg,
            context=AgentConfigValidationContext(
                debug=setup_input.log_level == LogLevel.DEBUG,
                log_level=setup_input.log_level,
                is_invoked_subcommand=True,  # dependencies verify is a subcommand
            ),
        )

        yield config
