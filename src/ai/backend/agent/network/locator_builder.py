"""Build the ContainerLocator a network plugin's privileged helper uses, from an agent's config."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ai.backend.agent.config.unified import AgentConfigValidationContext, AgentUnifiedConfig
from ai.backend.agent.network.locator import ContainerLocator
from ai.backend.agent.types import get_agent_discovery
from ai.backend.logging.types import LogLevel

__all__ = ("build_container_locator",)


def build_container_locator(agent_config: Mapping[str, Any]) -> ContainerLocator:
    """The locator for the backend the agent config names; it must name one (no default)."""
    local_config = AgentUnifiedConfig.model_validate(
        agent_config,
        context=AgentConfigValidationContext(
            debug=False,
            log_level=LogLevel.NOTSET,
            is_invoked_subcommand=True,
        ),
    )
    discovery = get_agent_discovery(local_config.agent_common.backend)
    return discovery.create_container_locator(local_config)
