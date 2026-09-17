from __future__ import annotations

import logging
from collections.abc import MutableMapping
from pathlib import Path
from typing import TYPE_CHECKING, override

from ai.backend.agent.kernel_registry.exception import KernelRecoveryDataParseError
from ai.backend.agent.kernel_registry.types import KernelRecoveryData
from ai.backend.agent.scratch.types import KernelRecoveryScratchData
from ai.backend.agent.scratch.utils import ScratchConfig, ScratchUtils
from ai.backend.common.types import KernelId
from ai.backend.logging import BraceStyleAdapter

from .abc import AbstractKernelRegistryWriter
from .types import KernelRegistrySaveMetadata

if TYPE_CHECKING:
    from ai.backend.agent.kernel import AbstractKernel

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class ContainerBasedKernelRegistryWriter(AbstractKernelRegistryWriter):
    def __init__(
        self,
        scratch_root: Path,
    ) -> None:
        self._scratch_root = scratch_root

    def _parse_recovery_data_from_kernel(
        self,
        kernel: AbstractKernel,
    ) -> KernelRecoveryData:
        try:
            return KernelRecoveryData.from_kernel(kernel)
        except KeyError as e:
            raise KernelRecoveryDataParseError from e

    @override
    async def save_kernel_registry(
        self, data: MutableMapping[KernelId, AbstractKernel], metadata: KernelRegistrySaveMetadata
    ) -> None:
        # `data` is the live registry and the loop awaits per kernel; a create or destroy on
        # this node meanwhile would change its size under the iteration.
        snapshot = list(data.items())
        for kernel_id, kernel in snapshot:
            config_path = ScratchUtils.get_scratch_kernel_config_dir(self._scratch_root, kernel_id)
            config_mgr = ScratchConfig(config_path)
            try:
                original_recovery_data = self._parse_recovery_data_from_kernel(kernel)
            except KernelRecoveryDataParseError as e:
                # A kernel that is registered but not yet fully built -- its REPL ports arrive a
                # step later -- has nothing to record yet, and its own start writes it. Ordinary
                # under concurrent creates; a traceback here reported a race as a fault.
                log.warning(
                    "Skipped saving kernel {}: its recovery data is not complete yet ({})",
                    kernel.kernel_id,
                    e.__cause__ or e,
                )
                continue
            recovery_data = KernelRecoveryScratchData.from_kernel_recovery_data(
                original_recovery_data
            )
            # The config directory is the kernel's own, made when it was created and removed with
            # it. Never re-made here: a save that outran a destroy would otherwise leave an empty
            # scratch directory behind for a kernel that is gone.
            try:
                await config_mgr.save_json_recovery_data(recovery_data, create_config_dir=False)
            except FileNotFoundError:
                log.debug(
                    "Skipped saving kernel {}: its scratch config directory was removed",
                    kernel_id,
                )
            # resource spec and environ are not saved here, as they are saved when the kernel is created.
        log.debug("Saved kernel registry to scratch root {}", str(self._scratch_root))
