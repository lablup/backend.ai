import logging
from uuid import UUID

from pydantic import ValidationError
from ruamel.yaml import YAML

from ai.backend.common.config import ModelDefinition
from ai.backend.common.types import VFolderID
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.clients.storage_proxy.session_manager import StorageSessionManager
from ai.backend.manager.data.model_card.types import ResourceRequirementEntry, VFolderScanData
from ai.backend.manager.errors.storage import ModelCardParseError
from ai.backend.manager.repositories.model_card.repository import ModelCardRepository
from ai.backend.manager.repositories.model_card.upserters import ModelCardScanUpserterSpec
from ai.backend.manager.services.model_card.actions.available_presets import (
    AvailablePresetsAction,
    AvailablePresetsActionResult,
)
from ai.backend.manager.services.model_card.actions.create import (
    CreateModelCardAction,
    CreateModelCardActionResult,
)
from ai.backend.manager.services.model_card.actions.delete import (
    DeleteModelCardAction,
    DeleteModelCardActionResult,
)
from ai.backend.manager.services.model_card.actions.scan import (
    ScanProjectModelCardsAction,
    ScanProjectModelCardsActionResult,
)
from ai.backend.manager.services.model_card.actions.search import (
    SearchModelCardsAction,
    SearchModelCardsActionResult,
)
from ai.backend.manager.services.model_card.actions.search_in_project import (
    SearchModelCardsInProjectAction,
    SearchModelCardsInProjectActionResult,
)
from ai.backend.manager.services.model_card.actions.update import (
    UpdateModelCardAction,
    UpdateModelCardActionResult,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


def _is_unmanaged(path: str | None) -> bool:
    return bool(path)


class ModelCardService:
    _repository: ModelCardRepository
    _storage_manager: StorageSessionManager

    def __init__(
        self,
        repository: ModelCardRepository,
        storage_manager: StorageSessionManager,
    ) -> None:
        self._repository = repository
        self._storage_manager = storage_manager

    async def create(self, action: CreateModelCardAction) -> CreateModelCardActionResult:
        data = await self._repository.create(action.creator)
        return CreateModelCardActionResult(model_card=data)

    async def update(self, action: UpdateModelCardAction) -> UpdateModelCardActionResult:
        action.updater.pk_value = action.id
        data = await self._repository.update(action.updater)
        return UpdateModelCardActionResult(model_card=data)

    async def delete(self, action: DeleteModelCardAction) -> DeleteModelCardActionResult:
        data = await self._repository.delete(action.id)
        return DeleteModelCardActionResult(model_card=data)

    async def search(self, action: SearchModelCardsAction) -> SearchModelCardsActionResult:
        result = await self._repository.search(action.querier)
        return SearchModelCardsActionResult(
            items=result.items,
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )

    async def search_in_project(
        self, action: SearchModelCardsInProjectAction
    ) -> SearchModelCardsInProjectActionResult:
        result = await self._repository.search_in_project(action.querier, action.scope)
        return SearchModelCardsInProjectActionResult(
            items=result.items,
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )

    async def available_presets(
        self, action: AvailablePresetsAction
    ) -> AvailablePresetsActionResult:
        result = await self._repository.search_available_presets(
            action.model_card_id, action.search_input
        )
        return AvailablePresetsActionResult(result=result)

    async def scan(self, action: ScanProjectModelCardsAction) -> ScanProjectModelCardsActionResult:
        vfolders = await self._repository.get_scan_target_vfolders(action.project_id)
        if not vfolders:
            return ScanProjectModelCardsActionResult(created_count=0, updated_count=0, errors=[])

        specs: list[ModelCardScanUpserterSpec] = []
        errors: list[str] = []
        seen_names: dict[str, VFolderScanData] = {}

        for vf in vfolders:
            try:
                spec = await self._scan_vfolder(vf, action.requester_id)
                if spec is None:
                    continue
                if spec.name in seen_names:
                    prev = seen_names[spec.name]
                    errors.append(
                        f"vfolder '{vf.name}' ({vf.id}): duplicate model name "
                        f"'{spec.name}' already seen from vfolder '{prev.name}' ({prev.id})"
                    )
                    continue
                seen_names[spec.name] = vf
                specs.append(spec)
            except Exception as e:
                errors.append(f"vfolder '{vf.name}' ({vf.id}): {e}")

        if not specs:
            return ScanProjectModelCardsActionResult(
                created_count=0, updated_count=0, errors=errors
            )

        domain = vfolders[0].domain_name
        existing_names = await self._repository.get_existing_card_names(action.project_id, domain)
        created, updated = await self._repository.bulk_upsert_scan(specs, existing_names)
        return ScanProjectModelCardsActionResult(
            created_count=created, updated_count=updated, errors=errors
        )

    async def _scan_vfolder(
        self, vf: VFolderScanData, requester_id: UUID
    ) -> ModelCardScanUpserterSpec | None:
        vfolder_id = VFolderID(vf.quota_scope_id, vf.id)
        proxy_name, volume_name = StorageSessionManager.get_proxy_and_volume(
            vf.host, _is_unmanaged(vf.unmanaged_path)
        )
        manager_client = self._storage_manager.get_manager_facing_client(proxy_name)

        result = await manager_client.list_files(volume_name, str(vfolder_id), ".")
        vfolder_files = result["items"]

        model_def_filename: str | None = None
        readme_idx: int | None = None
        for idx, item in enumerate(vfolder_files):
            if item["name"] in ("model-definition.yml", "model-definition.yaml"):
                if model_def_filename is None:
                    model_def_filename = item["name"]
            if item["name"].lower().startswith("readme."):
                readme_idx = idx

        if model_def_filename is None:
            return None

        raw_bytes = await manager_client.fetch_file_content(
            volume_name, str(vfolder_id), f"./{model_def_filename}"
        )
        yaml = YAML()
        try:
            parsed = yaml.load(raw_bytes.decode("utf-8"))
        except Exception as e:
            raise ModelCardParseError(extra_msg=f"invalid YAML in {model_def_filename}: {e}") from e

        try:
            model_def = ModelDefinition.model_validate(parsed)
        except ValidationError as e:
            raise ModelCardParseError(
                extra_msg=f"invalid model definition in {model_def_filename}: {e}"
            ) from e
        if not model_def.models:
            raise ModelCardParseError(extra_msg=f"no models defined in {model_def_filename}")

        first_model = model_def.models[0]
        metadata = first_model.metadata
        name = first_model.name

        readme: str | None = None
        if readme_idx is not None:
            readme_filename = vfolder_files[readme_idx]["name"]
            try:
                readme_bytes = await manager_client.fetch_file_content(
                    volume_name, str(vfolder_id), f"./{readme_filename}"
                )
                readme = readme_bytes.decode("utf-8")
            except Exception:
                log.warning("Failed to fetch README from vfolder {}", vf.id)

        min_resource: list[ResourceRequirementEntry] = []
        if metadata and metadata.min_resource:
            min_resource = [
                ResourceRequirementEntry(slot_name=k, min_quantity=str(v))
                for k, v in metadata.min_resource.items()
            ]

        return ModelCardScanUpserterSpec(
            name=name,
            vfolder_id=vf.id,
            domain=vf.domain_name,
            project_id=vf.project_id,
            creator_id=requester_id,
            author=metadata.author if metadata else None,
            title=metadata.title if metadata else None,
            model_version=str(metadata.version)
            if metadata and metadata.version is not None
            else None,
            description=metadata.description if metadata else None,
            task=metadata.task if metadata else None,
            category=metadata.category if metadata else None,
            architecture=metadata.architecture if metadata else None,
            framework=metadata.framework or [] if metadata else [],
            label=metadata.label or [] if metadata else [],
            license=metadata.license if metadata else None,
            min_resource=min_resource,
            readme=readme,
            access_level="internal",
        )
