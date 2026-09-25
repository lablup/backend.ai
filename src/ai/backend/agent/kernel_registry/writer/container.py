from __future__ import annotations

import logging
from collections.abc import MutableMapping
from pathlib import Path
from typing import TYPE_CHECKING, override

from ai.backend.agent.kernel_registry.exception import KernelRecoveryDataParseError
from ai.backend.agent.kernel_registry.types import KernelRecoveryData
from ai.backend.agent.scratch.types import KernelRecoveryScratchData
from ai.backend.agent.scratch.utils import ScratchConfig, ScratchUtils
from ai.backend.agent.types import KernelLifecycleStatus
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
        # `data` is the live registry and the loop awaits per kernel; a create or destroy on
        # this node meanwhile would change its size under the iteration.
        snapshot = list(data.items())
        for kernel_id, kernel in snapshot:
            config_path = ScratchUtils.get_scratch_kernel_config_dir(self._scratch_root, kernel_id)
            config_mgr = ScratchConfig(config_path)
            try:
                original_recovery_data = self._parse_recovery_data_from_kernel(kernel)
            except KernelRecoveryDataParseError as e:
                if kernel.state is KernelLifecycleStatus.PREPARING:
                    # Registered a step before its REPL ports exist; its own start writes it.
                    log.warning(
                        "Skipped saving kernel {}: not started yet ({})",
                        kernel.kernel_id,
                        e.__cause__ or e,
                    )
                else:
                    log.exception(
                        "Failed to parse recovery data from kernel {} in state {}: {}",
                        kernel.kernel_id,
                        kernel.state,
                        e.__cause__ or e,
                    )
                continue
            if original_recovery_data is None:
                continue
            recovery_data = KernelRecoveryScratchData.from_kernel_recovery_data(
                original_recovery_data
            )
            try:
                staged = await config_mgr.stage_json_recovery_data(recovery_data)
                # A restart re-registers the same id with a new kernel object and keeps the
                # directory: the snapshot's object must still be the registered one, checked
                # with no await between the check and the rename.
                if data.get(kernel_id) is kernel:
                    staged.commit()
                else:
                    staged.discard()
                    log.debug("Skipped saving kernel {}: replaced while being saved", kernel_id)
            except FileNotFoundError:
                log.debug("Skipped saving kernel {}: its scratch directory is gone", kernel_id)
            # resource spec and environ are not saved here, as they are saved when the kernel is created.
        log.debug("Saved kernel registry to scratch root {}", str(self._scratch_root))
