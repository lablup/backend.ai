from .container_registry.harbor import (
    AbstractPerProjectContainerRegistryQuotaService,
)


class ServicesContext:
    """
    Deprecated: This class is being replaced by the new service layer
    (services/container_registry_quota/). Once GraphQL mutations are migrated
    to use processors, this class and service/container_registry/harbor.py
    can be removed.
    """

    per_project_container_registries_quota: AbstractPerProjectContainerRegistryQuotaService

    def __init__(
        self,
        per_project_container_registries_quota: AbstractPerProjectContainerRegistryQuotaService,
    ) -> None:
        self.per_project_container_registries_quota = per_project_container_registries_quota
