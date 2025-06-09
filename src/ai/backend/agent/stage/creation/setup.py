import asyncio
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, override

from ai.backend.common.docker import ImageRef
from ai.backend.common.stage.types import Provisioner, ProvisionStage, SpecGenerator
from ai.backend.common.types import BinarySize, KernelId, SessionId

from .types import KernelCreationArgs


@dataclass
class ScrathInfo:
    scrath_type: str
    scrath_root: Path
    scrath_size: BinarySize


@dataclass
class KernelCreationSetupSpec:
    # throttle_semaphore: asyncio.Semaphore

    agent_architecture: str
    overriding_uid: Optional[int]
    overriding_gid: Optional[int]
    supplementary_gids: set[int]

    kernel_id: KernelId
    session_id: SessionId

    environ: Mapping[str, str]
    image_ref: ImageRef
    resource_allocation_order: list[str]

    scarth_info: ScrathInfo

    is_debug: bool


class KernelCreationSetupSpecGenerator(SpecGenerator[KernelCreationSetupSpec]):
    def __init__(
        self,
        args: KernelCreationArgs,
    ) -> None:
        self._spec = KernelCreationSetupSpec(
            throttle_semaphore=asyncio.Semaphore(1),  # Example semaphore, adjust as
            kernel_id=args.kernel_id,
            session_id=args.session_id,
            environ=args.environ,
            image_ref=args.image_ref,
            resource_allocation_order=[],  # This should be filled with actual resource allocation order
            # scarth_info=ScrathInfo(
            #     scrath_type="default",
            #     scrath_root=Path("/tmp/scrath"),
            #     scrath_size=BinarySize(1024 * 1024 * 1024)  # Example size, adjust as needed
            # ),
            is_debug=args.is_debug,
        )

    @override
    async def wait_for_spec(self) -> KernelCreationSetupSpec:
        return self._spec


@dataclass
class KernelCreationSetupResult:
    kernel_id: KernelId
    session_id: SessionId

    environ: Mapping[str, str]
    image_ref: ImageRef
    resource_allocation_order: list[str]

    scarth_info: ScrathInfo

    is_debug: bool


class KernelCreationSetupProvisioner(
    Provisioner[KernelCreationSetupSpec, KernelCreationSetupResult]
):
    @property
    @override
    def name(self) -> str:
        return "kernel_creation_setup"

    @override
    async def setup(self, spec: KernelCreationSetupSpec) -> KernelCreationSetupResult:
        """
        compare agent architecture with image architecture
        setup environment variables
        """

    @override
    async def teardown(self, resource: None) -> None:
        pass


class KernelCreationSetupStage(ProvisionStage[KernelCreationSetupSpec, KernelCreationSetupResult]):
    pass
