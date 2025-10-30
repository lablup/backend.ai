from ai.backend.common.types import KernelId

from ..kernel import AbstractKernel


class KernelRegistry(dict[KernelId, AbstractKernel]):
    pass
