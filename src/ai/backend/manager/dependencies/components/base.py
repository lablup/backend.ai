from __future__ import annotations

from typing import Generic

from ai.backend.common.dependencies import DependencyProvider, ResourceT
from ai.backend.manager.config.unified import ManagerUnifiedConfig


class ComponentDependency(DependencyProvider[ManagerUnifiedConfig, ResourceT], Generic[ResourceT]):
    """Base class for component dependencies that require unified config."""

    pass
