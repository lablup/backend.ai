from ai.backend.manager.models.container_registry import ContainerRegistryRow
from ai.backend.manager.repositories.base import QueryOrder


class ContainerRegistryOrders:
    @staticmethod
    def project(ascending: bool = True) -> QueryOrder:
        if ascending:
            return ContainerRegistryRow.project.asc()
        else:
            return ContainerRegistryRow.project.desc()

    @staticmethod
    def registry_name(ascending: bool = True) -> QueryOrder:
        if ascending:
            return ContainerRegistryRow.registry_name.asc()
        else:
            return ContainerRegistryRow.registry_name.desc()
