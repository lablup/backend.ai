from __future__ import annotations

from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.bulk.result import (
    PartialBulkEntityResult,
    PartialBulkResult,
)
from ai.backend.manager.data.service_catalog.types import ServiceCatalogData
from ai.backend.manager.errors.base.entity import EntityNotFoundError
from ai.backend.manager.repositories.service_catalog.repository import ServiceCatalogRepository
from ai.backend.manager.services.service_catalog.actions.bulk_get import (
    BulkGetServiceCatalogsAction,
)


class ServiceCatalogService:
    _repository: ServiceCatalogRepository

    def __init__(self, repository: ServiceCatalogRepository) -> None:
        self._repository = repository

    async def bulk_get(
        self, action: BulkGetServiceCatalogsAction
    ) -> PartialBulkResult[ServiceCatalogData]:
        found = await self._repository.bulk_get(action.ids)
        return PartialBulkResult(
            items=[
                PartialBulkEntityResult[ServiceCatalogData].succeeded(service_id, found[service_id])
                if service_id in found
                else PartialBulkEntityResult[ServiceCatalogData].failed(
                    service_id,
                    EntityNotFoundError(
                        entity_type=service_id.entity_type(),
                        operation=ActionOperationType.GET,
                        extra_msg=f"Service catalog {service_id} not found",
                    ),
                )
                for service_id in action.ids
            ]
        )
