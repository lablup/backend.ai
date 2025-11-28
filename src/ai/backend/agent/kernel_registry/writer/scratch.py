import logging
from collections.abc import MutableMapping
from pathlib import Path
from typing import TYPE_CHECKING, override

from ai.backend.common.types import KernelId
from ai.backend.logging import BraceStyleAdapter

from ...scratch.types import KernelRecoveryDataSchema
from ...scratch.utils import ScratchConfigManager, ScratchUtils
from .abc import AbstractKernelRegistryWriter
from .types import KernelRegistrySaveMetadata

if TYPE_CHECKING:
    from ai.backend.agent.kernel import AbstractKernel

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class ScratchBasedKernelRegistryWriter(AbstractKernelRegistryWriter):
    def __init__(
        self,
        scratch_root: Path,
    ) -> None:
        self._scratch_root = scratch_root

    @override
    async def save_kernel_registry(
        self, data: MutableMapping[KernelId, AbstractKernel], metadata: KernelRegistrySaveMetadata
    ) -> None:
        for kernel_id, kernel in data.items():
            config_path = ScratchUtils.get_scratch_kernel_config_dir(self._scratch_root, kernel_id)
            config_mgr = ScratchConfigManager(config_path)
            recovery_data = KernelRecoveryDataSchema.from_kernel_recovery_data(
                kernel.to_recovery_data()
            )
            await config_mgr.save_json_recovery_data(recovery_data)
            # resource spec and environ are not saved here, as they are saved when the kernel is created.
        log.debug("Saved kernel registry to scratch root {}", str(self._scratch_root))
