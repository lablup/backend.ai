import asyncio
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import override

from ai.backend.common.docker import ImageRef
from ai.backend.common.stage.types import Provisioner, ProvisionStage, SpecGenerator
from ai.backend.common.types import BinarySize, KernelId, SessionId

from ...resources import KernelResourceSpec


@dataclass
class ScrathInfo:
    scrath_type: str
    scrath_root: Path
    scrath_size: BinarySize


@dataclass
class KernelCreationPrepareSpec:
    throttle_semaphore: asyncio.Semaphore
    kernel_id: KernelId
    session_id: SessionId

    environ: Mapping[str, str]
    image_ref: ImageRef
    resource_spec: KernelResourceSpec
    resource_opts: Mapping[str, str]
    resource_allocation_order: list[str]

    scarth_info: ScrathInfo

    is_debug: bool


class KernelCreationPrepareSpecGenerator(SpecGenerator[KernelCreationPrepareSpec]):
    @override
    async def wait_for_spec(self) -> KernelCreationPrepareSpec:
        """
        Waits for the spec to be ready.
        """
        # In a real implementation, this would wait for some condition to be met.
        return KernelCreationPrepareSpec()


@dataclass
class KernelCreationPrepareResult:
    resource_spec: KernelResourceSpec
    resource_opts: Mapping[str, str]


class KernelCreationPrepareProvisioner(
    Provisioner[KernelCreationPrepareSpec, KernelCreationPrepareResult]
):
    """
    Provisioner for the kernel creation setup stage.
    This is a no-op provisioner as it does not create any resources.
    """

    @property
    @override
    def name(self) -> str:
        return "kernel_creation_prepare"

    @override
    async def setup(self, spec: KernelCreationPrepareSpec) -> KernelCreationPrepareResult:
        """
        prepare resource spec
        allocate resource
        prepare scratch
        apply network
        prepare ssh
        """

    @override
    async def teardown(self, resource: None) -> None:
        pass


class KernelCreationPrepareStage(
    ProvisionStage[KernelCreationPrepareSpec, KernelCreationPrepareResult]
):
    pass
