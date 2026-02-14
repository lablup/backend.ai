from __future__ import annotations

from ai.backend.common.dependencies import NonMonitorableDependencyProvider, ResourceT


class SystemDependency(NonMonitorableDependencyProvider[object, ResourceT]):
    """Base class for system dependencies that do not require health monitoring."""

    pass
