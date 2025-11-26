import logging
import os
import pickle
import shutil
from pathlib import Path
from typing import override

from ai.backend.logging import BraceStyleAdapter

from ...exception import KernelRegistryLoadError, KernelRegistryNotFound
from ...kernel import KernelRegistry
from .abc import AbstractKernelRegistryLoader

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class PickleBasedKernelRegistryLoader(AbstractKernelRegistryLoader[KernelRegistry]):
    def __init__(self, last_registry_file_path: Path, legacy_registry_file_path: Path) -> None:
        self._last_registry_file_path = last_registry_file_path
        self._legacy_registry_file_path = legacy_registry_file_path

    @override
    async def load_kernel_registry(self) -> KernelRegistry:
        legacy_registry_file = self._legacy_registry_file_path
        last_registry_file = self._last_registry_file_path
        try:
            if os.path.isfile(legacy_registry_file):
                shutil.move(legacy_registry_file, last_registry_file)
        except Exception as e:
            log.warning(
                "Failed to move legacy kernel registry file {} to {} (err: {})",
                str(legacy_registry_file),
                str(last_registry_file),
                str(e),
            )
        try:
            with open(last_registry_file, "rb") as f:
                return pickle.load(f)
        except EOFError as e:
            log.warning("Failed to load the last kernel registry: {}", str(last_registry_file))
            raise KernelRegistryLoadError from e
        except FileNotFoundError as e:
            raise KernelRegistryNotFound from e
