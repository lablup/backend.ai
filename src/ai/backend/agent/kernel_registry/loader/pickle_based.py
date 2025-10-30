import logging
import os
import pickle
import shutil
import time
from dataclasses import dataclass
from pathlib import Path
from typing import override

from ai.backend.logging import BraceStyleAdapter

from ...exception import KernelRegistryLoadError, KernelRegistryNotFound
from ..kernel_registry import KernelRegistry
from .abc import AbstractKernelRegistryRecovery, KernelRegistrySaveMetadata

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


SAVE_COOL_DOWN_SECONDS = 60


@dataclass
class KernelRegistryPickleRecoveryArgs:
    ipc_base_path: Path
    var_base_path: Path
    local_instance_id: str


class KernelRegistryPickleRecovery(AbstractKernelRegistryRecovery):
    def __init__(self, args: KernelRegistryPickleRecoveryArgs) -> None:
        self._ipc_base_path = args.ipc_base_path
        self._var_base_path = args.var_base_path
        self._local_instance_id = args.local_instance_id
        self._last_saved_time = time.monotonic()

    def _registry_file_name(self) -> str:
        return f"kernel_registry.{self._local_instance_id}.dat"

    def _get_legacy_registry_file_path(self) -> Path:
        return self._ipc_base_path / f"last_registry.{self._registry_file_name()}.dat"

    def _get_last_registry_file_path(self) -> Path:
        return self._var_base_path / f"last_registry.{self._registry_file_name()}.dat"

    @override
    async def load_kernel_registry(self) -> KernelRegistry:
        legacy_registry_file = self._get_legacy_registry_file_path()
        last_registry_file = self._get_last_registry_file_path()
        if os.path.isfile(legacy_registry_file):
            shutil.move(legacy_registry_file, last_registry_file)
        try:
            with open(last_registry_file, "rb") as f:
                return pickle.load(f)
        except EOFError as e:
            log.warning("Failed to load the last kernel registry: {}", (last_registry_file))
            raise KernelRegistryLoadError from e
        except FileNotFoundError as e:
            raise KernelRegistryNotFound from e

    @override
    async def save_kernel_registry(
        self, registry: KernelRegistry, metadata: KernelRegistrySaveMetadata
    ) -> None:
        now = time.monotonic()
        if (not metadata.force) and (now <= self._last_saved_time + SAVE_COOL_DOWN_SECONDS):
            return  # don't save too frequently
        last_registry_file = self._get_last_registry_file_path()
        try:
            with open(last_registry_file, "wb") as f:
                pickle.dump(registry, f)
            self._last_saved_time = now
            log.debug("saved {}", last_registry_file)
        except Exception as e:
            log.exception("unable to save {}", last_registry_file, exc_info=e)
            try:
                os.remove(last_registry_file)
            except FileNotFoundError:
                pass
