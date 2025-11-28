import logging
from pathlib import Path

from ai.backend.logging import BraceStyleAdapter

from ..scratch.types import KernelRecoveryDataSchema
from ..scratch.utils import ScratchConfigManager, ScratchUtils
from .types import KernelRegistryType

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class KernelRecoveryDataAdapter:
    """
    Adapter for writing kernel recovery data to scratch directory.
    """

    def __init__(self, scratch_root: Path) -> None:
        self._scratch_root = scratch_root

    async def write_recovery_data(self, data: KernelRegistryType) -> None:
        for kernel_id, kernel in data.items():
            config_dir = ScratchUtils.get_scratch_kernel_config_dir(self._scratch_root, kernel_id)
            config_mgr = ScratchConfigManager(config_dir)

            if config_mgr.recovery_file_exists():
                # Recovery data already exists, skip writing
                continue
            recovery_data = kernel.to_recovery_data()
            await config_mgr.save_json_recovery_data(
                KernelRecoveryDataSchema.from_kernel_recovery_data(recovery_data)
            )
            log.debug("Written recovery data for kernel {} to scratch", str(kernel_id))
