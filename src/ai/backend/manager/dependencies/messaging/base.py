from __future__ import annotations

from ai.backend.common.dependencies import DependencyProvider, ResourceT
from ai.backend.manager.config.unified import ManagerUnifiedConfig


class MessagingDependency(DependencyProvider[ManagerUnifiedConfig, ResourceT]):
    """Base class for messaging dependencies that require unified config."""

    pass
