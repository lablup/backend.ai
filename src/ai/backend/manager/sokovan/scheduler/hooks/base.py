"""Base classes for session state transition hooks."""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass

from ai.backend.common.types import ClusterMode
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.clients.agent.pool import AgentPool
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.models.network import NetworkType
from ai.backend.manager.plugin.network import NetworkPluginContext

from ..types import SessionTransitionData

log = BraceStyleAdapter(logging.getLogger(__name__))


class AbstractSessionHook(ABC):
    """
    Abstract base class for session state transition hooks.
    Subclasses implement session-type specific logic.
    """

    @abstractmethod
    async def on_transition_to_running(self, session: SessionTransitionData) -> None:
        """
        Called when a session is about to transition from CREATING to RUNNING.
        Raises exception if the transition should not proceed.

        :param session: Session transition data with all necessary information
        :raises Exception: If the hook fails and transition should not proceed
        """
        raise NotImplementedError

    @abstractmethod
    async def on_transition_to_terminated(self, session: SessionTransitionData) -> None:
        """
        Called when a session is about to transition from TERMINATING to TERMINATED.
        Best-effort cleanup - exceptions are logged but don't prevent termination.

        :param session: Session transition data with all necessary information
        :raises Exception: If cleanup fails (will be logged but ignored)
        """
        raise NotImplementedError


@dataclass
class SessionHookArgs:
    network_plugin_ctx: NetworkPluginContext
    config_provider: ManagerConfigProvider
    agent_pool: AgentPool


class SessionHook(AbstractSessionHook):
    _session_hook: AbstractSessionHook
    _network_plugin_ctx: NetworkPluginContext
    _config_provider: ManagerConfigProvider
    _agent_pool: AgentPool

    def __init__(self, session_hook: AbstractSessionHook, args: SessionHookArgs) -> None:
        self._session_hook = session_hook
        self._network_plugin_ctx = args.network_plugin_ctx
        self._config_provider = args.config_provider
        self._agent_pool = args.agent_pool

    async def on_transition_to_running(self, session: SessionTransitionData) -> None:
        # Bypass to the actual hook implementation
        await self._session_hook.on_transition_to_running(session)

    async def on_transition_to_terminated(self, session: SessionTransitionData) -> None:
        try:
            await self._session_hook.on_transition_to_terminated(session)
        except Exception as e:
            log.error(
                "Error during cleanup for session {}: {}",
                session.session_id,
                str(e),
            )
        finally:
            log.info(
                "Running default cleanup for session transition data {}",
                session,
            )
            if session.network_type == NetworkType.VOLATILE:
                await self._destroy_network(session)

    async def _destroy_network(self, session: SessionTransitionData) -> None:
        log.info(
            "Destroying network {} for session {} ...",
            session.network_id,
            session.session_id,
        )
        network_id = session.network_id
        if network_id is None:
            log.debug(
                "No network to destroy for session {} (network_id is None)",
                session.session_id,
            )
            return
        match session.cluster_mode:
            case ClusterMode.SINGLE_NODE:
                try:
                    agent_client = self._agent_pool.get_agent_client(
                        session.main_kernel.agent_id,
                        order_key=str(session.session_id),
                    )
                    await agent_client.destroy_local_network(network_id)
                except Exception:
                    log.exception(f"Failed to destroy the agent-local network {network_id}")
            case ClusterMode.MULTI_NODE:
                if self._config_provider.config.network.inter_container.default_driver is None:
                    raise ValueError("No inter-container network driver is configured.")

                network_plugin = self._network_plugin_ctx.plugins[
                    self._config_provider.config.network.inter_container.default_driver
                ]
                try:
                    await network_plugin.destroy_network(network_id=network_id)
                except Exception:
                    log.exception(f"Failed to destroy the overlay network {network_id}.")


class NoOpSessionHook(AbstractSessionHook):
    """Default no-op hook for session types that don't need special handling."""

    async def on_transition_to_running(self, session: SessionTransitionData) -> None:
        log.debug(
            "No-op hook for session {} (type: {})",
            session.session_id,
            session.session_type,
        )

    async def on_transition_to_terminated(self, session: SessionTransitionData) -> None:
        log.debug(
            "No-op cleanup for session {} (type: {})",
            session.session_id,
            session.session_type,
        )
