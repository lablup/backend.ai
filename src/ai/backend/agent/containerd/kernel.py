from collections.abc import Mapping
from typing import Any

from ai.backend.agent.agent import AbstractKernelCreationContext
from ai.backend.agent.kernel import AbstractKernel


class ContainerdKernel(AbstractKernel):
    """Containerd-backed kernel (prototype scaffold).

    Abstract methods from `AbstractKernel` are not yet overridden;
    instantiation will fail until the CRI-based implementation lands.
    """


class ContainerdKernelCreationContext(AbstractKernelCreationContext[ContainerdKernel]):
    """Containerd kernel creation context (prototype scaffold)."""


async def prepare_krunner_env(local_config: Mapping[str, Any]) -> Mapping[str, str]:
    # TODO(containerd-prototype): provision krunner image into containerd's
    # content store via CRI ImageService.PullImage and return the env mapping
    # consumed by AbstractAgent.
    del local_config
    return {}
