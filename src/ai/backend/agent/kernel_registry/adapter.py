from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable, Collection
from dataclasses import dataclass

from ai.backend.common.types import KernelId
from ai.backend.logging import BraceStyleAdapter

from .exception import KernelRegistryNotFound
from .loader.abc import AbstractKernelRegistryLoader
from .writer.abc import AbstractKernelRegistryWriter
from .writer.types import KernelRegistrySaveMetadata

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

type LiveKernelIdsProvider = Callable[[], Awaitable[Collection[KernelId]]]


@dataclass
class KernelRecoveryDataAdapterTarget:
    loader: AbstractKernelRegistryLoader
    writer: AbstractKernelRegistryWriter


class KernelRecoveryDataAdapter:
    """
    Adapts Docker kernel recovery data.
    1. Loads recovery data using the source loader.
    2. Loads recovery data using the target loader to ensure compatibility.
    3. Saves the recovery data using the target writer.

    The source is a snapshot, so it is reconciled against the kernels the runtime actually has
    before anything is written.
    """

    _source_loader: AbstractKernelRegistryLoader
    _targets: list[KernelRecoveryDataAdapterTarget]
    _live_kernel_ids: LiveKernelIdsProvider

    def __init__(
        self,
        source_loader: AbstractKernelRegistryLoader,
        targets: list[KernelRecoveryDataAdapterTarget],
        live_kernel_ids: LiveKernelIdsProvider,
    ) -> None:
        self._source_loader = source_loader
        self._targets = targets
        self._live_kernel_ids = live_kernel_ids

    async def adapt_recovery_data(self) -> None:
        try:
            source_data = await self._source_loader.load_kernel_registry()
        except KernelRegistryNotFound:
            log.info("No source kernel registry found to adapt.")
            return
        live_kernel_ids = await self._live_kernel_ids()
        for target in self._targets:
            data = await target.loader.load_kernel_registry()
            for kernel_id, kernel in source_data.items():
                if kernel_id in data:
                    continue
                if kernel_id not in live_kernel_ids:
                    # The snapshot can still name a kernel that has terminated and had its scratch
                    # removed. Adapting it writes the scratch back for a kernel that no longer
                    # exists, and nothing ever reclaims that directory.
                    log.debug(
                        "not adapting kernel {}: this runtime no longer has its container",
                        kernel_id,
                    )
                    continue
                data[kernel_id] = kernel
            metadata = KernelRegistrySaveMetadata(force=True)
            await target.writer.save_kernel_registry(data, metadata)
