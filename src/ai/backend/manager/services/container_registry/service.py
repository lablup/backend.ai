import logging

from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.models.container_registry import ContainerRegistryRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.services.container_registry.actions.get_container_registries import (
    GetContainerRegistriesAction,
    GetContainerRegistriesActionResult,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class ContainerRegistryService:
    _db: ExtendedAsyncSAEngine

    def __init__(
        self,
        db: ExtendedAsyncSAEngine,
    ) -> None:
        self._db = db

    async def get_container_registries(
        self, action: GetContainerRegistriesAction
    ) -> GetContainerRegistriesActionResult:
        async with self._db.begin_session() as session:
            _registries = await ContainerRegistryRow.get_known_container_registries(session)

        known_registries = {}
        for project, registries in _registries.items():
            for registry_name, url in registries.items():
                if project not in known_registries:
                    known_registries[f"{project}/{registry_name}"] = url.human_repr()
        return GetContainerRegistriesActionResult(registries=known_registries)
