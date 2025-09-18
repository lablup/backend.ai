"""Storage source implementation for deployment repository."""

from typing import Optional

import tomli

from ai.backend.common.types import VFolderID
from ai.backend.manager.data.model_serving.types import ModelServiceDefinition
from ai.backend.manager.data.vfolder.types import VFolderLocation
from ai.backend.manager.errors.deployment import DefinitionFileNotFound
from ai.backend.manager.models.storage import StorageSessionManager


class DeploymentStorageSource:
    """Storage source for deployment-related file operations."""

    _storage_manager: StorageSessionManager

    def __init__(self, storage_manager: StorageSessionManager) -> None:
        self._storage_manager = storage_manager

    async def fetch_service_config(
        self,
        model_vfolder: VFolderLocation,
    ) -> Optional[ModelServiceDefinition]:
        """
        Fetch and parse service-definition.toml from model vfolder.

        Args:
            model_vfolder: The model vfolder location information

        Returns:
            Parsed service definition as ModelServiceDefinition, or None if not found
        """
        try:
            vfid = VFolderID(model_vfolder.quota_scope_id, model_vfolder.id)
            folder_host = model_vfolder.host

            proxy_name, volume_name = self._storage_manager.get_proxy_and_volume(folder_host)
            manager_client = self._storage_manager.get_manager_facing_client(proxy_name)

            chunks = await manager_client.fetch_file_content(
                volume_name,
                str(vfid),
                "./service-definition.toml",
            )

            if chunks:
                raw_content = chunks.decode("utf-8")
                parsed_toml = tomli.loads(raw_content)
                return ModelServiceDefinition(**parsed_toml)

        except Exception:
            # Service definition file not found or parse error
            pass

        return None

    async def fetch_definition_file(
        self,
        vfolder_location: VFolderLocation,
        definition_candidates: list[str],
    ) -> bytes:
        """
        Fetch definition file from model vfolder.
        Args:
            vfolder_location: The model vfolder location information
            definition_candidates: List of candidate file paths to look for
        """
        vfid = VFolderID(vfolder_location.quota_scope_id, vfolder_location.id)
        folder_host = vfolder_location.host

        proxy_name, volume_name = self._storage_manager.get_proxy_and_volume(folder_host)
        manager_client = self._storage_manager.get_manager_facing_client(proxy_name)

        for definition_file_path in definition_candidates:
            try:
                # Try to fetch the file to check if it exists
                file_content = await manager_client.fetch_file_content(
                    volume_name,
                    str(vfid),
                    f"{definition_file_path}",
                )
                if file_content:
                    return file_content
            except Exception:
                continue
        raise DefinitionFileNotFound(
            f"definition file not found in vfolder {vfid} for candidates {definition_candidates}"
        )
