"""
Registry for session state transition hooks.
Maps session types to their corresponding hook implementations.
"""

import logging
from collections import defaultdict
from dataclasses import dataclass

from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.types import SessionTypes
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.clients.agent.pool import AgentPool
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.plugin.network import NetworkPluginContext
from ai.backend.manager.repositories.deployment.repository import DeploymentRepository

from .base import AbstractSessionHook, NoOpSessionHook, SessionHook, SessionHookArgs
from .batch import BatchSessionHook
from .inference import InferenceSessionHook
from .interactive import InteractiveSessionHook
from .system import SystemSessionHook

log = BraceStyleAdapter(logging.getLogger(__name__))


@dataclass
class HookRegistryArgs:
    repository: DeploymentRepository
    agent_pool: AgentPool
    network_plugin_ctx: NetworkPluginContext
    config_provider: ManagerConfigProvider
    event_producer: EventProducer


class HookRegistry:
    _repository: DeploymentRepository
    _agent_pool: AgentPool
    _network_plugin_ctx: NetworkPluginContext
    _config_provider: ManagerConfigProvider
    _event_producer: EventProducer
    _hooks: defaultdict[SessionTypes, AbstractSessionHook]

    def __init__(self, args: HookRegistryArgs) -> None:
        self._repository = args.repository
        self._agent_pool = args.agent_pool
        self._network_plugin_ctx = args.network_plugin_ctx
        self._config_provider = args.config_provider
        self._event_producer = args.event_producer
        self._hooks = defaultdict(NoOpSessionHook)
        self._initialize_hooks()

    def _initialize_hooks(self) -> None:
        args = SessionHookArgs(
            network_plugin_ctx=self._network_plugin_ctx,
            config_provider=self._config_provider,
            agent_pool=self._agent_pool,
        )
        self._hooks[SessionTypes.INTERACTIVE] = SessionHook(InteractiveSessionHook(), args)
        self._hooks[SessionTypes.BATCH] = SessionHook(BatchSessionHook(self._agent_pool), args)
        self._hooks[SessionTypes.INFERENCE] = SessionHook(
            InferenceSessionHook(self._repository, self._event_producer), args
        )
        self._hooks[SessionTypes.SYSTEM] = SessionHook(SystemSessionHook(), args)

    def get_hook(self, session_type: SessionTypes) -> AbstractSessionHook:
        hook = self._hooks[session_type]
        log.trace("Using hook {} for session type {}", hook.__class__.__name__, session_type)
        return hook
