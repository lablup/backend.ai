from collections.abc import Mapping
from typing import Any

from ai.backend.agent.kernel import AbstractKernel


class ContainerdKernel(AbstractKernel):
    """Containerd-backed kernel (prototype scaffold).

    Abstract methods from `AbstractKernel` are not yet overridden;
    instantiation will fail until the native-API implementation lands
    (see the containerd-agent wiring plan).
    """


async def prepare_krunner_env(local_config: Mapping[str, Any]) -> Mapping[str, str]:
    # TODO(containerd-prototype): provision the krunner image into containerd's
    # content store via the Transfer service and return the env mapping
    # consumed by AbstractAgent.
    del local_config
    return {}
