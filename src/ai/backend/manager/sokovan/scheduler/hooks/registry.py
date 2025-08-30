"""
Registry for session state transition hooks.
Maps session types to their corresponding hook implementations.
"""

import logging
from collections import defaultdict

from ai.backend.common.types import SessionTypes
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.clients.agent.pool import AgentPool
from ai.backend.manager.repositories.deployment.repository import DeploymentRepository

from .base import NoOpSessionHook, SessionHook
from .batch import BatchSessionHook
from .inference import InferenceSessionHook
from .interactive import InteractiveSessionHook
from .system import SystemSessionHook

log = BraceStyleAdapter(logging.getLogger(__name__))


class HookRegistry:
    _repository: DeploymentRepository
    _agent_pool: AgentPool
    _hooks: defaultdict[SessionTypes, SessionHook]

    def __init__(self, repository: DeploymentRepository, agent_pool: AgentPool) -> None:
        self._repository = repository
        self._agent_pool = agent_pool
        self._hooks = defaultdict(NoOpSessionHook)
        self._initialize_hooks()

    def _initialize_hooks(self) -> None:
        self._hooks[SessionTypes.INTERACTIVE] = InteractiveSessionHook()
        self._hooks[SessionTypes.BATCH] = BatchSessionHook(self._agent_pool)
        self._hooks[SessionTypes.INFERENCE] = InferenceSessionHook(self._repository)
        self._hooks[SessionTypes.SYSTEM] = SystemSessionHook()

    def get_hook(self, session_type: SessionTypes) -> SessionHook:
        hook = self._hooks[session_type]
        log.trace("Using hook {} for session type {}", hook.__class__.__name__, session_type)
        return hook
