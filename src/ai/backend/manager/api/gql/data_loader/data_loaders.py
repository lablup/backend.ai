from __future__ import annotations

from ai.backend.manager.services.processors import Processors


class DataLoaders:
    """
    Manages domain-specific DataLoader instances for GraphQL resolvers.

    This class is the central registry for all DataLoaders used in the GraphQL API.
    Each domain (notification, model_deployment, model_replica, etc.) will have
    its own loader instances initialized here.
    """

    _processors: Processors

    def __init__(self, processors: Processors) -> None:
        self._processors = processors
        # Domain-specific loaders will be initialized here as needed.
        # Example:
        # self._notification_loader = NotificationLoader(processors.notification)
        # self._model_deployment_loader = ModelDeploymentLoader(...)
