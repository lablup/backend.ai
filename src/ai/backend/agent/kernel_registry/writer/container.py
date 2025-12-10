from __future__ import annotations

import logging
from collections.abc import MutableMapping
from pathlib import Path
from typing import TYPE_CHECKING, Optional, override

from ai.backend.common.types import KernelId
from ai.backend.logging import BraceStyleAdapter

from ...scratch.types import KernelRecoveryScratchData
from ...scratch.utils import ScratchConfig, ScratchUtils
from ..types import KernelRecoveryData
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
    ) -> Optional[KernelRecoveryData]:
        from ai.backend.agent.docker.kernel import DockerKernel

        match kernel:
            case DockerKernel():
                return KernelRecoveryData.from_docker_kernel(kernel)
            case _:
                return None

    @override
    async def save_kernel_registry(
        self, data: MutableMapping[KernelId, AbstractKernel], metadata: KernelRegistrySaveMetadata
    ) -> None:
        for kernel_id, kernel in data.items():
            config_path = ScratchUtils.get_scratch_kernel_config_dir(self._scratch_root, kernel_id)
            config_mgr = ScratchConfig(config_path)
            original_recovery_data = self._parse_recovery_data_from_kernel(kernel)
            if original_recovery_data is None:
                continue
            recovery_data = KernelRecoveryScratchData.from_kernel_recovery_data(
                original_recovery_data
            )
            await config_mgr.save_json_recovery_data(recovery_data)
            # resource spec and environ are not saved here, as they are saved when the kernel is created.
        log.debug("Saved kernel registry to scratch root {}", str(self._scratch_root))
