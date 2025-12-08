"""Model definition source for health check configuration."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Optional

from typing_extensions import override

from ai.backend.common.config import ModelHealthCheck
from ai.backend.common.types import RuntimeVariant
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.models.endpoint import ModelServiceHelper
from ai.backend.manager.repositories.deployment.types.health_check_source import HealthCheckSource

if TYPE_CHECKING:
    from ai.backend.manager.models.storage import StorageSessionManager

__all__ = ["ModelDefinitionSource"]

log = BraceStyleAdapter(logging.getLogger(__name__))


class ModelDefinitionSource(HealthCheckSource):
    """Load health check config from model-definition.yaml file."""

    def __init__(
        self,
        storage_manager: "StorageSessionManager",
        host: str,
        vfid: Any,
        model_definition_path: Optional[str],
        runtime_variant: RuntimeVariant,
    ) -> None:
        self._storage_manager = storage_manager
        self._host = host
        self._vfid = vfid
        self._model_definition_path = model_definition_path
        self._runtime_variant = runtime_variant

    @override
    async def load(self) -> Optional[ModelHealthCheck]:
        if self._runtime_variant != RuntimeVariant.CUSTOM:
            return None

        try:
            resolved_path = await ModelServiceHelper.validate_model_definition_file_exists(
                self._storage_manager,
                self._host,
                self._vfid,
                self._model_definition_path,
            )
            model_definition = await ModelServiceHelper.validate_model_definition(
                self._storage_manager,
                self._host,
                self._vfid,
                resolved_path,
            )

            for model_info in model_definition.get("models", []):
                health_check_info = model_info.get("service", {}).get("health_check")
                if health_check_info:
                    return ModelHealthCheck(
                        path=health_check_info["path"],
                        interval=health_check_info["interval"],
                        max_retries=health_check_info["max_retries"],
                        max_wait_time=health_check_info["max_wait_time"],
                        expected_status_code=health_check_info["expected_status_code"],
                        initial_delay=health_check_info.get("initial_delay"),
                    )
        except Exception:
            log.debug("Failed to load health check config from model-definition.yaml")
        return None
