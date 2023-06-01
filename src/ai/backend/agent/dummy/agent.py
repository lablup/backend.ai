
from ..agent import AbstractAgent, AbstractKernelCreationContext
from .kernel import DummyKernel

class DummyKernelCreationContext(AbstractKernelCreationContext[DummyKernel]):
    async def get_extra_envs(self) -> Mapping[str, str]:
        return {}
    
    async def prepare_resource_spec(
        self,
    ) -> Tuple[KernelResourceSpec, Optional[Mapping[str, Any]]]:
        pass

    async def prepare_scratch(self) -> None:
        pass

    async def get_intrinsic_mounts(self) -> Sequence[Mount]:
        return []
    
    async def apply_network(self, cluster_info: ClusterInfo) -> None:
        pass

    async def prepare_ssh(self, cluster_info: ClusterInfo) -> None:
        pass

    async def process_mounts(self, mounts: Sequence[Mount]):
        pass

    async def apply_accelerator_allocation(
        self,
        computer: AbstractComputePlugin,
        device_alloc: Mapping[SlotName, Mapping[DeviceId, Decimal]],
    ) -> None:
        pass

    async def generate_accelerator_mounts(
        self,
        computer: AbstractComputePlugin,
        device_alloc: Mapping[SlotName, Mapping[DeviceId, Decimal]],
    ) -> List[MountInfo]:
        pass

    def resolve_krunner_filepath(self, filename) -> Path:
        pass

    def get_runner_mount(
        self,
        type: MountTypes,
        src: Union[str, Path],
        target: Union[str, Path],
        perm: Literal["ro", "rw"] = "ro",
        opts: Mapping[str, Any] = None,
    ):
        pass

    async def spawn(
        self,
        resource_spec: KernelResourceSpec,
        environ: Mapping[str, str],
        service_ports,
    ) -> KernelObjectType:
        pass

    async def start_container(
        self,
        kernel_obj: AbstractKernel,
        cmdargs: List[str],
        resource_opts,
        preopen_ports,
    ) -> Mapping[str, Any]:
        pass

    


class DummyAgent(
    AbstractAgent[DummyKernel, DummyKernelCreationContext],
):
    async def enumerate_containers(
        self,
        status_filter: FrozenSet[ContainerStatus] = ACTIVE_STATUS_SET,
    ) -> Sequence[Tuple[KernelId, Container]]:
        pass

    async def detect_resources(
        self,
    ) -> Tuple[Mapping[DeviceName, AbstractComputePlugin], Mapping[SlotName, Decimal]]:
        pass

    async def scan_images(self) -> Mapping[str, str]:
        pass

    async def pull_image(self, image_ref: ImageRef, registry_conf: ImageRegistry) -> None:
        pass

    async def check_image(
        self, image_ref: ImageRef, image_id: str, auto_pull: AutoPullBehavior
    ) -> bool:
        pass

    async def init_kernel_context(
        self,
        kernel_id: KernelId,
        session_id: SessionId,
        kernel_config: KernelCreationConfig,
        *,
        restarting: bool = False,
        cluster_ssh_port_mapping: Optional[ClusterSSHPortMapping] = None,
    ) -> AbstractKernelCreationContext:
        pass

    async def destroy_kernel(
        self,
        kernel_id: KernelId,
        container_id: Optional[ContainerId],
    ) -> None:
        pass

    async def clean_kernel(
        self,
        kernel_id: KernelId,
        container_id: Optional[ContainerId],
        restarting: bool,
    ) -> None:
        pass

    async def create_local_network(self, network_name: str) -> None:
        pass

    async def destroy_local_network(self, network_name: str) -> None:
        pass

    async def restart_kernel__load_config(
        self,
        kernel_id: KernelId,
        name: str,
    ) -> bytes:
        pass

    async def restart_kernel__store_config(
        self,
        kernel_id: KernelId,
        name: str,
        data: bytes,
    ) -> None:
        pass


