from .container_registry.harbor import (
    AbstractPerProjectContainerRegistryQuotaService,
)


class ServicesContext:
    """
    In the API layer, requests are processed through the ServicesContext and
    its subordinate layers, including the DB, Client, and Repository layers.
    Each layer separates the responsibilities specific to its respective level.
    """

    per_project_container_registries_quota: AbstractPerProjectContainerRegistryQuotaService

    def __init__(
        self,
        per_project_container_registries_quota: AbstractPerProjectContainerRegistryQuotaService,
    ) -> None:
        self.per_project_container_registries_quota = per_project_container_registries_quota
