from __future__ import annotations

from ai.backend.common.dependencies import DependencyProvider, ResourceT
from ai.backend.manager.config.bootstrap import BootstrapConfig


class BootstrapDependency(DependencyProvider[BootstrapConfig, ResourceT]):
    """Base class for bootstrap dependencies that only need BootstrapConfig."""

    pass
