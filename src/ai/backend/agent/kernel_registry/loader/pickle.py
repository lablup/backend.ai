from __future__ import annotations

import logging
import os
import pickle
import shutil
from collections.abc import MutableMapping
from pathlib import Path
from typing import TYPE_CHECKING, override

from ai.backend.common.types import KernelId
from ai.backend.logging import BraceStyleAdapter

from ..exception import KernelRegistryLoadError, KernelRegistryNotFound
from .abc import AbstractKernelRegistryLoader

if TYPE_CHECKING:
    from ai.backend.agent.kernel import AbstractKernel

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class PickleBasedKernelRegistryLoader(AbstractKernelRegistryLoader):
    def __init__(
        self,
        last_registry_file_path: Path,
        legacy_registry_file_path: Path,
    ) -> None:
        self._last_registry_file_path = last_registry_file_path
        self._legacy_registry_file_path = legacy_registry_file_path

    @override
    async def load_kernel_registry(self) -> MutableMapping[KernelId, AbstractKernel]:
        legacy_registry_file = self._legacy_registry_file_path
        final_file_path = self._last_registry_file_path
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
                result = pickle.load(f)
                return result
        except EOFError as e:
            log.warning("Failed to load the last kernel registry: {}", str(final_file_path))
            raise KernelRegistryLoadError from e
        except FileNotFoundError as e:
            raise KernelRegistryNotFound from e
