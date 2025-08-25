"""Storage source implementation for deployment repository."""

from typing import Optional

import tomli

from ai.backend.manager.models.storage import StorageSessionManager
from ai.backend.manager.models.vfolder import VFolderRow
from ai.backend.manager.services.model_serving.types import ModelServiceDefinition


class DeploymentStorageSource:
    """Storage source for deployment-related file operations."""

    _storage_manager: StorageSessionManager

    def __init__(self, storage_manager: StorageSessionManager) -> None:
        self._storage_manager = storage_manager

    async def fetch_service_config(
        self,
        model_vfolder_row: VFolderRow,
    ) -> Optional[ModelServiceDefinition]:
        """
        Fetch and parse service-definition.toml from model vfolder.

        Args:
            model_vfolder_row: The model vfolder containing service definition

        Returns:
            Parsed service definition as ModelServiceDefinition, or None if not found
        """
        try:
            vfid = model_vfolder_row.vfid
            folder_host = model_vfolder_row.host

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

    async def check_model_definition_exists(
        self,
        model_vfolder_row: VFolderRow,
        model_definition_path: str,
    ) -> bool:
        """
        Check if model definition file exists in the model vfolder.

        Args:
            model_vfolder_row: The model vfolder to check
            model_definition_path: Path to the model definition file (e.g., "model-definition.py")

        Returns:
            True if the file exists, False otherwise
        """
        try:
            vfid = model_vfolder_row.vfid
            folder_host = model_vfolder_row.host

            proxy_name, volume_name = self._storage_manager.get_proxy_and_volume(folder_host)
            manager_client = self._storage_manager.get_manager_facing_client(proxy_name)

            # Try to fetch the file to check if it exists
            chunks = await manager_client.fetch_file_content(
                volume_name,
                str(vfid),
                f"./{model_definition_path}",
            )

            return chunks is not None

        except Exception:
            # Model definition file not found
            return False
