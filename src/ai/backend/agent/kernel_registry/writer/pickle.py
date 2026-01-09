from __future__ import annotations

import logging
import os
import pickle
import time
from collections.abc import MutableMapping
from pathlib import Path
from typing import TYPE_CHECKING, override

from ai.backend.common.types import KernelId
from ai.backend.logging import BraceStyleAdapter

from .abc import AbstractKernelRegistryWriter
from .types import KernelRegistrySaveMetadata

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

if TYPE_CHECKING:
    from ai.backend.agent.kernel import AbstractKernel

SAVE_COOL_DOWN_SECONDS = 60


class PickleBasedKernelRegistryWriter(AbstractKernelRegistryWriter):
    def __init__(self, last_registry_file_path: Path) -> None:
        self._last_registry_file_path = last_registry_file_path
        self._last_saved_time = time.monotonic()

    @override
    async def save_kernel_registry(
        self, data: MutableMapping[KernelId, AbstractKernel], metadata: KernelRegistrySaveMetadata
    ) -> None:
        now = time.monotonic()
        if (not metadata.force) and (now <= self._last_saved_time + SAVE_COOL_DOWN_SECONDS):
            return  # don't save too frequently
        last_registry_file = self._last_registry_file_path
        try:
            with open(last_registry_file, "wb") as f:
                pickle.dump(dict(data), f)
            self._last_saved_time = now
            log.debug("Saved kernel registry to {}", str(last_registry_file))
        except Exception as e:
            log.exception(
                "Failed to save kernel registry to {} (error: {})",
                str(last_registry_file),
                str(e),
            )
            try:
                os.remove(last_registry_file)
            except FileNotFoundError:
                pass
