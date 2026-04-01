from __future__ import annotations

from ai.backend.common.dependencies import NonMonitorableDependencyProvider, ResourceT, SetupInputT


class DomainDependency(NonMonitorableDependencyProvider[SetupInputT, ResourceT]):
    """Base class for domain dependencies.

    Domain dependencies are higher-level objects (repositories, services, lock factories)
    that depend on infrastructure (db, valkey, etcd) and component (storage_manager) resources.
    They use composite input dataclasses rather than a single config object.
    """

    pass
