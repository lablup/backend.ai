from __future__ import annotations

import logging
import pickle
import shutil
from collections.abc import MutableMapping
from pathlib import Path
from typing import TYPE_CHECKING, cast, override

from ai.backend.agent.kernel_registry.exception import (
    KernelRegistryLoadError,
    KernelRegistryNotFound,
)
from ai.backend.common.asyncio import run_in_executor_with_context
from ai.backend.common.types import KernelId
from ai.backend.logging.structured import StructuredLogger

from .abc import AbstractKernelRegistryLoader

if TYPE_CHECKING:
    from ai.backend.agent.kernel import AbstractKernel

log = StructuredLogger(logging.getLogger(__spec__.name))


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
            if legacy_registry_file.is_file():
                shutil.move(legacy_registry_file, final_file_path)
        except Exception as e:
            log.warning(
                "legacy kernel registry file move failed",
                exc_info=e,
                legacy_registry_path=legacy_registry_file,
                registry_path=final_file_path,
            )
        try:
            with final_file_path.open("rb") as f:
                return cast("MutableMapping[KernelId, AbstractKernel]", pickle.load(f))
        except EOFError as e:
            log.warning("kernel registry load failed", registry_path=final_file_path)
            raise KernelRegistryLoadError from e
        except FileNotFoundError as e:
            raise KernelRegistryNotFound from e

    @override
    async def mark_migrated(self) -> None:
        """Rename the snapshot to `<name>.migrated`: an older agent would re-adapt it, bringing
        back the scratch records of kernels that ended after this migration."""
        final_file_path = self._last_registry_file_path
        migrated_path = final_file_path.with_name(f"{final_file_path.name}.migrated")
        try:
            await run_in_executor_with_context(None, final_file_path.replace, migrated_path)
        except FileNotFoundError:
            pass
