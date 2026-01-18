"""Base classes for session state transition hooks."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass

from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.clients.agent.pool import AgentClientPool
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.plugin.network import NetworkPluginContext
from ai.backend.manager.sokovan.scheduler.types import SessionWithKernels

log = BraceStyleAdapter(logging.getLogger(__name__))


class AbstractSessionHook(ABC):
    """
    Abstract base class for session state transition hooks.
    Subclasses implement session-type specific logic.
    """

    @abstractmethod
    async def on_transition(
        self,
        session: SessionWithKernels,
        status: SessionStatus,
    ) -> None:
        """
        Called when a session is about to transition to a new status.

        :param session: SessionWithKernels with session and kernel information
        :param status: The target status the session is transitioning to
        :raises Exception: If the hook fails (behavior depends on blocking config)
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

    async def on_transition(
        self,
        session: SessionWithKernels,
        status: SessionStatus,
    ) -> None:
        """Execute session hook with SessionWithKernels data.

        Note: Notifications are not yet supported.
        This will be implemented when SessionWithKernels has all required fields.
        """
        await self._session_hook.on_transition(session, status)
        # TODO: Add notification support when SessionWithKernels has required fields
        log.debug(
            "Executed on_transition to {} for session {}",
            status,
            session.session_info.identity.id,
        )


class NoOpSessionHook(AbstractSessionHook):
    """Default no-op hook for session types that don't need special handling."""

    async def on_transition(
        self,
        session: SessionWithKernels,
        status: SessionStatus,
    ) -> None:
        log.debug(
            "No-op hook for session {} (type: {}) transitioning to {}",
            session.session_info.identity.id,
            session.session_info.identity.session_type,
            status,
        )
