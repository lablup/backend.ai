"""Base classes for session state transition hooks."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass

from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.clients.agent.pool import AgentClientPool
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.plugin.network import NetworkPluginContext
from ai.backend.manager.sokovan.scheduler.types import SessionWithKernels

log = BraceStyleAdapter(logging.getLogger(__name__))


class AbstractSessionHook(ABC):
    """
    Abstract base class for session state transition hooks.
    Subclasses implement session-type specific logic.
    """

    @abstractmethod
    async def on_transition_to_running(self, session: SessionWithKernels) -> None:
        """
        Called when a session is about to transition from CREATING to RUNNING.
        Raises exception if the transition should not proceed.

        :param session: SessionWithKernels with session and kernel information
        :raises Exception: If the hook fails and transition should not proceed
        """
        raise NotImplementedError

    @abstractmethod
    async def on_transition_to_terminated(self, session: SessionWithKernels) -> None:
        """
        Called when a session is about to transition from TERMINATING to TERMINATED.
        Best-effort cleanup - exceptions are logged but don't prevent termination.

        :param session: SessionWithKernels with session and kernel information
        :raises Exception: If cleanup fails (will be logged but ignored)
        """
        raise NotImplementedError


@dataclass
class SessionHookArgs:
    network_plugin_ctx: NetworkPluginContext
    config_provider: ManagerConfigProvider
    agent_client_pool: AgentClientPool
    event_producer: EventProducer


class SessionHook(AbstractSessionHook):
    """Wrapper hook that delegates to session-type specific hooks."""

    _session_hook: AbstractSessionHook
    _network_plugin_ctx: NetworkPluginContext
    _config_provider: ManagerConfigProvider
    _agent_client_pool: AgentClientPool
    _event_producer: EventProducer

    def __init__(self, session_hook: AbstractSessionHook, args: SessionHookArgs) -> None:
        self._session_hook = session_hook
        self._network_plugin_ctx = args.network_plugin_ctx
        self._config_provider = args.config_provider
        self._agent_client_pool = args.agent_client_pool
        self._event_producer = args.event_producer

    async def on_transition_to_running(self, session: SessionWithKernels) -> None:
        """Execute session hook with SessionWithKernels data.

        Note: Notifications are not yet supported.
        This will be implemented when SessionWithKernels has all required fields.
        """
        await self._session_hook.on_transition_to_running(session)
        # TODO: Add notification support when SessionWithKernels has required fields
        log.debug(
            "Executed on_transition_to_running for session {}",
            session.session_info.identity.id,
        )

    async def on_transition_to_terminated(self, session: SessionWithKernels) -> None:
        """Execute session hook with SessionWithKernels data.

        Note: Network cleanup and notifications are not yet supported.
        This will be implemented when SessionWithKernels has all required fields.
        """
        try:
            await self._session_hook.on_transition_to_terminated(session)
        except Exception as e:
            log.error(
                "Error during cleanup for session {}: {}",
                session.session_info.identity.id,
                str(e),
            )
        # TODO: Add notification and network cleanup when SessionWithKernels has required fields
        log.debug(
            "Executed on_transition_to_terminated for session {}",
            session.session_info.identity.id,
        )


class NoOpSessionHook(AbstractSessionHook):
    """Default no-op hook for session types that don't need special handling."""

    async def on_transition_to_running(self, session: SessionWithKernels) -> None:
        log.debug(
            "No-op hook for session {} (type: {})",
            session.session_info.identity.id,
            session.session_info.identity.session_type,
        )

    async def on_transition_to_terminated(self, session: SessionWithKernels) -> None:
        log.debug(
            "No-op cleanup for session {} (type: {})",
            session.session_info.identity.id,
            session.session_info.identity.session_type,
        )
