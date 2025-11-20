"""Base classes for session state transition hooks."""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass

from ai.backend.common.events.dispatcher import EventProducer
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
    event_producer: EventProducer


class SessionHook(AbstractSessionHook):
    _session_hook: AbstractSessionHook
    _network_plugin_ctx: NetworkPluginContext
    _config_provider: ManagerConfigProvider
    _agent_pool: AgentPool
    _event_producer: EventProducer

    def __init__(self, session_hook: AbstractSessionHook, args: SessionHookArgs) -> None:
        self._session_hook = session_hook
        self._network_plugin_ctx = args.network_plugin_ctx
        self._config_provider = args.config_provider
        self._agent_pool = args.agent_pool
        self._event_producer = args.event_producer

    async def _produce_session_started_notification(self, session: SessionTransitionData) -> None:
        """Produce notification event for session start."""
        from datetime import datetime, timezone

        from ai.backend.common.data.notification import NotificationRuleType
        from ai.backend.common.data.notification.messages import SessionStartedMessage
        from ai.backend.common.events.event_types.notification import NotificationTriggeredEvent

        try:
            message = SessionStartedMessage(
                session_id=str(session.session_id),
                session_name=session.session_name,
                session_type=str(session.session_type),
                cluster_mode=str(session.cluster_mode),
                status="RUNNING",
            )
            event = NotificationTriggeredEvent(
                rule_type=NotificationRuleType.SESSION_STARTED.value,
                timestamp=datetime.now(timezone.utc),
                notification_data=message.model_dump(),
            )
            await self._event_producer.anycast_event(event)
            log.debug("Produced session started notification for {}", session.session_id)
        except Exception as e:
            log.error(
                "Failed to produce session started notification for {}: {}",
                session.session_id,
                e,
            )

    async def _produce_session_terminated_notification(
        self, session: SessionTransitionData
    ) -> None:
        """Produce notification event for session termination."""
        from datetime import datetime, timezone

        from ai.backend.common.data.notification import NotificationRuleType
        from ai.backend.common.data.notification.messages import SessionTerminatedMessage
        from ai.backend.common.events.event_types.notification import NotificationTriggeredEvent

        try:
            message = SessionTerminatedMessage(
                session_id=str(session.session_id),
                session_name=session.session_name,
                session_type=str(session.session_type),
                cluster_mode=str(session.cluster_mode),
                status="TERMINATED",
                termination_reason=session.status_info,
            )
            event = NotificationTriggeredEvent(
                rule_type=NotificationRuleType.SESSION_TERMINATED.value,
                timestamp=datetime.now(timezone.utc),
                notification_data=message.model_dump(),
            )
            await self._event_producer.anycast_event(event)
            log.debug("Produced session terminated notification for {}", session.session_id)
        except Exception as e:
            log.error(
                "Failed to produce session terminated notification for {}: {}",
                session.session_id,
                e,
            )

    async def on_transition_to_running(self, session: SessionTransitionData) -> None:
        # Execute session-type specific hook first
        await self._session_hook.on_transition_to_running(session)
        # Produce notification event AFTER successful hook execution
        await self._produce_session_started_notification(session)

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
            # Produce notification BEFORE network cleanup
            await self._produce_session_terminated_notification(session)

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
