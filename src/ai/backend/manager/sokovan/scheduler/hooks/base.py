"""Base classes for session state transition hooks."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING

from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.types import ResourceSlot
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.clients.agent.pool import AgentClientPool
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.plugin.network import NetworkPluginContext
from ai.backend.manager.sokovan.scheduler.types import SessionRunningData, SessionWithKernels

if TYPE_CHECKING:
    from ai.backend.manager.repositories.scheduler.repository import SchedulerRepository

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
    scheduler_repository: SchedulerRepository


class SessionHook(AbstractSessionHook):
    """Wrapper hook that delegates to session-type specific hooks.

    Also handles common transition logic like occupied_slots update for RUNNING.
    """

    _session_hook: AbstractSessionHook
    _network_plugin_ctx: NetworkPluginContext
    _config_provider: ManagerConfigProvider
    _agent_client_pool: AgentClientPool
    _event_producer: EventProducer
    _scheduler_repository: SchedulerRepository

    def __init__(self, session_hook: AbstractSessionHook, args: SessionHookArgs) -> None:
        self._session_hook = session_hook
        self._network_plugin_ctx = args.network_plugin_ctx
        self._config_provider = args.config_provider
        self._agent_client_pool = args.agent_client_pool
        self._event_producer = args.event_producer
        self._scheduler_repository = args.scheduler_repository

    async def on_transition(
        self,
        session: SessionWithKernels,
        status: SessionStatus,
    ) -> None:
        """Execute session hook with SessionWithKernels data.

        Handles common transition logic:
        - RUNNING: Updates occupied_slots from kernel data

        Note: Notifications are not yet supported.
        This will be implemented when SessionWithKernels has all required fields.
        """
        # Execute session-type specific hook first
        await self._session_hook.on_transition(session, status)

        # Common transition logic
        if status == SessionStatus.RUNNING:
            await self._update_occupied_slots(session)

        log.debug(
            "Executed on_transition to {} for session {}",
            status,
            session.session_info.identity.id,
        )

    async def _update_occupied_slots(self, session: SessionWithKernels) -> None:
        """Calculate and update occupied_slots for a session transitioning to RUNNING."""
        total_occupied_slots = ResourceSlot()
        for kernel_info in session.kernel_infos:
            if kernel_info.resource.occupied_slots:
                total_occupied_slots += kernel_info.resource.occupied_slots

        running_data = [
            SessionRunningData(
                session_id=session.session_info.identity.id,
                occupying_slots=total_occupied_slots,
            )
        ]
        await self._scheduler_repository.update_sessions_to_running(running_data)
        log.debug(
            "Updated occupied_slots for session {} transitioning to RUNNING",
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
