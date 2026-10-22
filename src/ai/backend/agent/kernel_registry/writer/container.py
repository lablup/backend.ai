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
from ai.backend.logging.structured import StructuredLogger

from .abc import AbstractKernelRegistryWriter
from .types import KernelRegistrySaveMetadata

if TYPE_CHECKING:
    from ai.backend.agent.kernel import AbstractKernel

log = StructuredLogger(logging.getLogger(__spec__.name))


class ContainerBasedKernelRegistryWriter(AbstractKernelRegistryWriter):
    def __init__(
        self,
        scratch_root: Path,
    ) -> None:
        self._scratch_root = scratch_root

    def _parse_recovery_data_from_kernel(
        self,
        kernel: AbstractKernel,
    ) -> KernelRecoveryData | None:
        from ai.backend.agent.docker.kernel import DockerKernel

        match kernel:
            case DockerKernel():
                try:
                    return KernelRecoveryData.from_docker_kernel(kernel)
                except KeyError as e:
                    raise KernelRecoveryDataParseError from e
            case _:
                return None

    @override
    async def save_kernel_registry(
        self, data: MutableMapping[KernelId, AbstractKernel], metadata: KernelRegistrySaveMetadata
    ) -> None:
        for kernel_id, kernel in data.items():
            config_path = ScratchUtils.get_scratch_kernel_config_dir(self._scratch_root, kernel_id)
            config_mgr = ScratchConfig(config_path)
            try:
                original_recovery_data = self._parse_recovery_data_from_kernel(kernel)
            except KernelRecoveryDataParseError as e:
                log.exception(
                    "kernel recovery data parse failed",
                    kernel_id=kernel.kernel_id,
                    error_repr=repr(e),
                )
                continue
            if original_recovery_data is None:
                continue
            recovery_data = KernelRecoveryScratchData.from_kernel_recovery_data(
                original_recovery_data
            )
            await config_mgr.save_json_recovery_data(recovery_data)
            # resource spec and environ are not saved here, as they are saved when the kernel is created.
        log.debug("kernel registry saved to scratch", scratch_root=self._scratch_root)
