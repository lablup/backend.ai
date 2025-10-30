import logging
import os
import pickle
import shutil
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import override

from ai.backend.logging import BraceStyleAdapter

from ..exception import KernelRegistryLoadError, KernelRegistryNotFound
from .kernel_registry import KernelRegistry

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


SAVE_COOL_DOWN_SECONDS = 60


@dataclass
class KernelRegistrySaveMetadata:
    force: bool


class AbstractKernelRegistryRecovery(ABC):
    """
    Recovery interface for loading and saving KernelRegistry
    """

    @abstractmethod
    async def load_kernel_registry(self) -> KernelRegistry:
        """
        Load the KernelRegistry from persistent storage.
        Raises:
            KernelRegistryNotFound
            KernelRegistryLoadError
        Returns: The loaded KernelRegistry.
        """
        pass

    @abstractmethod
    async def save_kernel_registry(
        self, registry: KernelRegistry, metadata: KernelRegistrySaveMetadata
    ) -> None:
        """
        Save the KernelRegistry to persistent storage.
        args:
            registry: The KernelRegistry to save.
            metadata: Additional metadata for saving.
        Returns: None
        """
        pass


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

    @override
    async def load_kernel_registry(self) -> KernelRegistry:
        ipc_base_path = self._ipc_base_path
        var_base_path = self._var_base_path
        last_registry_file = f"last_registry.{self._local_instance_id}.dat"
        if os.path.isfile(ipc_base_path / last_registry_file):
            shutil.move(ipc_base_path / last_registry_file, var_base_path / last_registry_file)
        try:
            with open(var_base_path / last_registry_file, "rb") as f:
                return pickle.load(f)
        except EOFError as e:
            log.warning(
                "Failed to load the last kernel registry: {}", (var_base_path / last_registry_file)
            )
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
        var_base_path = self._var_base_path
        last_registry_file = f"last_registry.{self._local_instance_id}.dat"
        try:
            with open(var_base_path / last_registry_file, "wb") as f:
                pickle.dump(registry, f)
            self._last_saved_time = now
            log.debug("saved {}", last_registry_file)
        except Exception as e:
            log.exception("unable to save {}", last_registry_file, exc_info=e)
            try:
                os.remove(var_base_path / last_registry_file)
            except FileNotFoundError:
                pass
