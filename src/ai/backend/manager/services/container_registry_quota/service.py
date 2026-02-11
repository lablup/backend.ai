import logging

from ai.backend.common.container_registry import ContainerRegistryType
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.clients.container_registry.harbor import (
    AbstractPerProjectRegistryQuotaClient,
    HarborAuthArgs,
    HarborProjectInfo,
    PerProjectHarborQuotaClient,
)
from ai.backend.manager.data.container_registry.types import PerProjectContainerRegistryInfo
from ai.backend.manager.errors.common import GenericBadRequest
from ai.backend.manager.repositories.container_registry_quota.repository import (
    PerProjectRegistryQuotaRepository,
)
from ai.backend.manager.services.container_registry_quota.actions.create_quota import (
    CreateQuotaAction,
    CreateQuotaActionResult,
)
from ai.backend.manager.services.container_registry_quota.actions.delete_quota import (
    DeleteQuotaAction,
    DeleteQuotaActionResult,
)
from ai.backend.manager.services.container_registry_quota.actions.read_quota import (
    ReadQuotaAction,
    ReadQuotaActionResult,
)
from ai.backend.manager.services.container_registry_quota.actions.update_quota import (
    UpdateQuotaAction,
    UpdateQuotaActionResult,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


def make_registry_quota_client(
    type_: ContainerRegistryType,
) -> AbstractPerProjectRegistryQuotaClient:
    match type_:
        case ContainerRegistryType.HARBOR2:
            return PerProjectHarborQuotaClient()
        case _:
            raise GenericBadRequest(
                f"{type_} does not support registry quota per project management."
            )


class ContainerRegistryQuotaService:
    _repository: PerProjectRegistryQuotaRepository

    def __init__(
        self,
        repository: PerProjectRegistryQuotaRepository,
    ) -> None:
        self._repository = repository

    def _registry_info_to_harbor_project_info(
        self, registry_info: PerProjectContainerRegistryInfo
    ) -> HarborProjectInfo:
        return HarborProjectInfo(
            url=registry_info.url,
            project=registry_info.project,
            ssl_verify=registry_info.ssl_verify,
        )

    def _registry_info_to_credential(
        self, registry_info: PerProjectContainerRegistryInfo
    ) -> HarborAuthArgs:
        return HarborAuthArgs(username=registry_info.username, password=registry_info.password)

    async def create_quota(self, action: CreateQuotaAction) -> CreateQuotaActionResult:
        log.info("Creating container registry quota for project {}", action.scope_id.project_id)

        registry_info = await self._repository.fetch_container_registry_row(action.scope_id)
        client = make_registry_quota_client(registry_info.type)
        project_info = self._registry_info_to_harbor_project_info(registry_info)
        credential = self._registry_info_to_credential(registry_info)

        await client.create_quota(project_info, action.quota, credential)
        return CreateQuotaActionResult(scope_id=action.scope_id)

    async def update_quota(self, action: UpdateQuotaAction) -> UpdateQuotaActionResult:
        log.info("Updating container registry quota for project {}", action.scope_id.project_id)

        registry_info = await self._repository.fetch_container_registry_row(action.scope_id)
        client = make_registry_quota_client(registry_info.type)
        project_info = self._registry_info_to_harbor_project_info(registry_info)
        credential = self._registry_info_to_credential(registry_info)

        await client.update_quota(project_info, action.quota, credential)
        return UpdateQuotaActionResult(scope_id=action.scope_id)

    async def delete_quota(self, action: DeleteQuotaAction) -> DeleteQuotaActionResult:
        log.info("Deleting container registry quota for project {}", action.scope_id.project_id)

        registry_info = await self._repository.fetch_container_registry_row(action.scope_id)
        client = make_registry_quota_client(registry_info.type)
        project_info = self._registry_info_to_harbor_project_info(registry_info)
        credential = self._registry_info_to_credential(registry_info)

        await client.delete_quota(project_info, credential)
        return DeleteQuotaActionResult(scope_id=action.scope_id)

    async def read_quota(self, action: ReadQuotaAction) -> ReadQuotaActionResult:
        log.info("Reading container registry quota for project {}", action.scope_id.project_id)

        registry_info = await self._repository.fetch_container_registry_row(action.scope_id)
        client = make_registry_quota_client(registry_info.type)
        project_info = self._registry_info_to_harbor_project_info(registry_info)
        credential = self._registry_info_to_credential(registry_info)

        quota = await client.read_quota(project_info, credential)
        return ReadQuotaActionResult(scope_id=action.scope_id, quota=quota)
