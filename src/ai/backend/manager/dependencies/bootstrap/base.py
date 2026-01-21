from __future__ import annotations

from typing import Generic

from ai.backend.common.dependencies import DependencyProvider, ResourceT
from ai.backend.manager.config.bootstrap import BootstrapConfig


class BootstrapDependency(DependencyProvider[BootstrapConfig, ResourceT], Generic[ResourceT]):
    """Base class for bootstrap dependencies that only need BootstrapConfig."""

    pass
