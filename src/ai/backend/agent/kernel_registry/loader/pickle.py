import logging
import os
import pickle
import shutil
from pathlib import Path
from typing import override

from ai.backend.common.types import KernelId
from ai.backend.logging import BraceStyleAdapter

from ....agent.kernel import AbstractKernel
from ...exception import KernelRegistryLoadError, KernelRegistryNotFound
from .abc import AbstractKernelRegistryLoader

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class PickleBasedKernelRegistryLoader(AbstractKernelRegistryLoader):
    def __init__(
        self,
        last_registry_file_path: Path,
        fallback_registry_file_path: Path,
        legacy_registry_file_path: Path,
    ) -> None:
        self._last_registry_file_path = last_registry_file_path
        self._fallback_registry_file_path = fallback_registry_file_path
        self._legacy_registry_file_path = legacy_registry_file_path

    @override
    async def load_kernel_registry(self) -> dict[KernelId, AbstractKernel]:
        legacy_registry_file = self._legacy_registry_file_path
        fallback_registry_file = self._fallback_registry_file_path
        final_file_path = self._last_registry_file_path
        if not final_file_path.is_file():
            log.warning(
                "Registry file with name {} not found. "
                "Falling back to path with local instance id: {}",
                final_file_path,
                fallback_registry_file,
            )
            final_file_path = fallback_registry_file
        try:
            if os.path.isfile(legacy_registry_file):
                shutil.move(legacy_registry_file, final_file_path)
        except Exception as e:
            log.warning(
                "Failed to move legacy kernel registry file {} to {} (err: {})",
                str(legacy_registry_file),
                str(final_file_path),
                str(e),
            )
        try:
            with open(final_file_path, "rb") as f:
                return pickle.load(f)
        except EOFError as e:
            log.warning("Failed to load the last kernel registry: {}", str(final_file_path))
            raise KernelRegistryLoadError from e
        except FileNotFoundError as e:
            raise KernelRegistryNotFound from e
