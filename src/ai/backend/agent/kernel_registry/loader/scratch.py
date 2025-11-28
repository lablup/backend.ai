import logging
from pathlib import Path
from typing import override

from ai.backend.common.types import KernelId
from ai.backend.logging import BraceStyleAdapter

from ...docker.kernel import DockerKernel
from ...dummy.kernel import DummyKernel
from ...kernel import AbstractKernel
from ...kubernetes.kernel import KubernetesKernel
from ...scratch.utils import ScratchConfigManager, ScratchUtils
from ...types import AgentBackend
from ..exception import KernelRegistryNotFound
from ..types import KernelRecoveryData, KernelRegistryType
from .abc import AbstractKernelRegistryLoader

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class ScratchBasedKernelRegistryLoader(AbstractKernelRegistryLoader):
    def __init__(
        self,
        scratch_root: Path,
    ) -> None:
        self._scratch_root = scratch_root

    def _parse_kernel_obj_from_recovery_data(
        self,
        data: KernelRecoveryData,
    ) -> AbstractKernel:
        kernel_cls: type[DockerKernel] | type[KubernetesKernel] | type[DummyKernel]
        match data.kernel_backend:
            case AgentBackend.DOCKER:
                kernel_cls = DockerKernel
            case AgentBackend.KUBERNETES:
                kernel_cls = KubernetesKernel
            case AgentBackend.DUMMY:
                kernel_cls = DummyKernel
        return kernel_cls.from_recovery_data(data)

    async def _load_kernel_recovery_from_scratch(self, config_path: Path) -> KernelRecoveryData:
        config = ScratchConfigManager(config_path)
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
    async def load_kernel_registry(self) -> KernelRegistryType:
        result: dict[KernelId, AbstractKernel] = {}
        for kernel_id, config_path in ScratchUtils.list_kernel_id_and_config_path(
            self._scratch_root
        ):
            if not config_path.is_dir():
                continue
            try:
                recovery_data = await self._load_kernel_recovery_from_scratch(config_path)
                result[kernel_id] = self._parse_kernel_obj_from_recovery_data(recovery_data)
            except KernelRegistryNotFound:
                log.warning(
                    "Failed to load kernel recovery data for kernel id {} from scratch path {}",
                    str(kernel_id),
                    str(config_path),
                )
                continue
        log.debug("Loaded kernel registry from scratch root {}", str(self._scratch_root))
        return result
