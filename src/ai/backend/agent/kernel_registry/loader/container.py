from __future__ import annotations

import logging
from collections.abc import MutableMapping
from pathlib import Path
from typing import TYPE_CHECKING, override

from ai.backend.common.types import KernelId
from ai.backend.logging import BraceStyleAdapter

from ...scratch.utils import ScratchConfig, ScratchUtils
from ..exception import KernelRegistryNotFound
from ..types import KernelRecoveryData
from .abc import AbstractKernelRegistryLoader

if TYPE_CHECKING:
    from ai.backend.agent.agent import AbstractAgent
    from ai.backend.agent.kernel import AbstractKernel

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class ContainerBasedKernelRegistryLoader(AbstractKernelRegistryLoader):
    def __init__(
        self,
        scratch_root: Path,
        agent: AbstractAgent,
    ) -> None:
        self._scratch_root = scratch_root
        self._agent = agent

    async def _load_kernel_recovery_from_scratch(self, config_path: Path) -> KernelRecoveryData:
        config = ScratchConfig(config_path)
        json_data = await config.get_json_recovery_data()
        if json_data is None:
            raise KernelRegistryNotFound
        environ = await config.get_kernel_environ()
        resource_spec = await config.get_kernel_resource_spec()
        recovery_data = json_data.to_kernel_recovery_data(
            resource_spec,
            environ,
        )
        return recovery_data

    @override
    async def load_kernel_registry(self) -> MutableMapping[KernelId, AbstractKernel]:
        result: dict[KernelId, AbstractKernel] = {}
        containers = await self._agent.enumerate_containers()
        for kernel_id, _ in containers:
            config_path = ScratchUtils.get_scratch_kernel_config_dir(
                self._scratch_root,
                kernel_id,
            )
            if not config_path.is_dir():
                continue
            try:
                recovery_data = await self._load_kernel_recovery_from_scratch(config_path)
                result[kernel_id] = recovery_data.to_docker_kernel()
            except KernelRegistryNotFound:
                log.warning(
                    "Failed to load kernel recovery data for kernel id {} from scratch path {}",
                    str(kernel_id),
                    str(config_path),
                )
                continue
        log.debug("Loaded kernel registry from scratch root {}", str(self._scratch_root))
        return result
