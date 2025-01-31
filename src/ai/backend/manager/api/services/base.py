from ai.backend.manager.models.utils import ExtendedAsyncSAEngine

from .container_registries.base import PerProjectRegistryQuotaRepository
from .container_registries.harbor import (
    PerProjectContainerRegistryQuotaProtocol,
    PerProjectContainerRegistryQuotaService,
)


class ServicesContext:
    """
    In the API layer, requests are processed through the ServicesContext and
    its subordinate layers, including the DB, Client, and Repository layers.
    Each layer separates the responsibilities specific to its respective level.
    """

    db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self.db = db

    @property
    def per_project_container_registries_quota(self) -> PerProjectContainerRegistryQuotaProtocol:
        repository = PerProjectRegistryQuotaRepository(db=self.db)
        return PerProjectContainerRegistryQuotaService(repository=repository)
