"""Storage source implementation for deployment repository."""

from collections.abc import Mapping
from typing import Any, override

import tomli
from ruamel.yaml import YAML

from ai.backend.common.config import ModelDefinitionDraft
from ai.backend.common.exception import BackendAIError, InvalidAPIParameters
from ai.backend.common.types import BackendAISchema, ModelValidationFailureInfo, VFolderID
from ai.backend.manager.data.vfolder.types import VFolderLocation
from ai.backend.manager.models.storage import StorageSessionManager


class DeploymentConfigInput(BackendAISchema):
    """Validated ``deployment-config.yaml`` / ``service-definition.toml`` payload.

    Shared shape across the new yaml name and the legacy toml name — storage
    resolves either one, validates it against this schema, and returns it
    to the repository, which then resolves ``image`` / ``architecture`` into
    an ``image_id`` at its own boundary.
    """

    model_config = {"extra": "ignore"}

    image: str | None = None
    architecture: str | None = None
    resource_slots: dict[str, Any] | None = None
    resource_opts: dict[str, Any] | None = None
    environ: dict[str, str] | None = None

    @override
    @classmethod
    def build_validation_error(cls, info: ModelValidationFailureInfo) -> BackendAIError:
        return InvalidAPIParameters(
            f"Invalid deployment config: {info.summary}",
            extra_data={"errors": info.errors},
        )


class DeploymentStorageSource:
    """Storage source for deployment-related file operations."""

    _storage_manager: StorageSessionManager

    def __init__(self, storage_manager: StorageSessionManager) -> None:
        self._storage_manager = storage_manager

    async def fetch_deployment_config(
        self,
        vfolder_location: VFolderLocation,
        candidates: list[str],
    ) -> DeploymentConfigInput | None:
        """Fetch the first existing deployment config among ``candidates``.

        Parses toml/yaml by extension and validates against
        ``DeploymentConfigInput``. Returns ``None`` when none exist.
        """
        raw = await self._fetch_config_file_in_candidates(vfolder_location, candidates)
        if raw is None:
            return None
        return DeploymentConfigInput.model_validate(dict(raw))

    async def fetch_model_definition(
        self,
        vfolder_location: VFolderLocation,
        candidates: list[str],
    ) -> ModelDefinitionDraft | None:
        """Fetch the first existing model-definition file among ``candidates``.

        Uses the draft type because user-authored files may supply only a
        partial set of fields — required-field validation happens downstream
        when the merged result is resolved to the strict
        ``ModelDefinition``.
        """
        raw = await self._fetch_config_file_in_candidates(vfolder_location, candidates)
        if raw is None:
            return None
        return ModelDefinitionDraft.model_validate(dict(raw))

    async def _fetch_config_file_in_candidates(
        self,
        vfolder_location: VFolderLocation,
        candidates: list[str],
    ) -> Mapping[str, Any] | None:
        """Return the first parsed ``Mapping`` among the candidates.

        Candidates are tried in priority order (new name first, legacy
        fallback second). Parser is selected by filename extension:
        ``.toml`` → tomli, anything else → YAML. ``None`` means no candidate
        existed or the file was empty.
        """
        vfid = VFolderID(vfolder_location.quota_scope_id, vfolder_location.id)
        folder_host = vfolder_location.host

        proxy_name, volume_name = self._storage_manager.get_proxy_and_volume(folder_host)
        manager_client = self._storage_manager.get_manager_facing_client(proxy_name)

        for filename in candidates:
            try:
                raw_bytes = await manager_client.fetch_file_content(
                    volume_name, str(vfid), filename
                )
            except Exception:
                continue
            if not raw_bytes:
                continue
            loaded: Any
            if filename.endswith(".toml"):
                loaded = tomli.loads(raw_bytes.decode("utf-8"))
            elif filename.endswith((".yaml", ".yml")):
                loaded = YAML().load(raw_bytes)
            else:
                raise InvalidAPIParameters(
                    f"Unsupported config file extension for '{filename}': "
                    "only .toml, .yaml, .yml are accepted."
                )
            if loaded is None:
                continue
            if not isinstance(loaded, Mapping):
                raise InvalidAPIParameters(
                    f"Invalid config file '{filename}': top-level value must be a mapping."
                )
            return loaded
        return None
