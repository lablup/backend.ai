import asyncio
import itertools
import sys
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import AsyncIterator, Optional, override

from aiodocker.docker import Docker, DockerError

from ai.backend.agent.config.unified import AgentUnifiedConfig
from ai.backend.agent.data.kernel.kernel import KernelObject
from ai.backend.agent.docker.utils import PersistentServiceContainer
from ai.backend.agent.plugin.network import NetworkPluginContext
from ai.backend.agent.resources import ComputerContext
from ai.backend.agent.stage.kernel_lifecycle.docker.bootstrap import (
    BootstrapProvisioner,
    BootstrapSpec,
    BootstrapSpecGenerator,
    BootstrapStage,
)
from ai.backend.agent.stage.kernel_lifecycle.docker.cluster_ssh import (
    ClusterSSHProvisioner,
    ClusterSSHSpec,
    ClusterSSHSpecGenerator,
    ClusterSSHStage,
)
from ai.backend.agent.stage.kernel_lifecycle.docker.cmdarg import (
    CmdArgProvisioner,
    CmdArgSpec,
    CmdArgSpecGenerator,
    CmdArgStage,
)
from ai.backend.agent.stage.kernel_lifecycle.docker.config_files import (
    ConfigFileProvisioner,
    ConfigFileSpec,
    ConfigFileSpecGenerator,
    ConfigFileStage,
)
from ai.backend.agent.stage.kernel_lifecycle.docker.container.check import (
    ContainerCheckProvisioner,
    ContainerCheckSpec,
    ContainerCheckSpecGenerator,
    ContainerCheckStage,
)
from ai.backend.agent.stage.kernel_lifecycle.docker.container.config import (
    ContainerConfigProvisioner,
    ContainerConfigSpec,
    ContainerConfigSpecGenerator,
    ContainerConfigStage,
)
from ai.backend.agent.stage.kernel_lifecycle.docker.container.create import (
    ContainerCreateProvisioner,
    ContainerCreateSpec,
    ContainerCreateSpecGenerator,
    ContainerCreateStage,
)
from ai.backend.agent.stage.kernel_lifecycle.docker.container.start import (
    ContainerStartProvisioner,
    ContainerStartSpec,
    ContainerStartSpecGenerator,
    ContainerStartStage,
)
from ai.backend.agent.stage.kernel_lifecycle.docker.container_ssh import (
    ContainerSSHProvisioner,
    ContainerSSHSpec,
    ContainerSSHSpecGenerator,
    ContainerSSHStage,
)
from ai.backend.agent.stage.kernel_lifecycle.docker.credentials import (
    CredentialsProvisioner,
    CredentialsSpec,
    CredentialsSpecGenerator,
    CredentialsStage,
)
from ai.backend.agent.stage.kernel_lifecycle.docker.defs import DEFAULT_CONTAINER_LOG_FILE_COUNT
from ai.backend.agent.stage.kernel_lifecycle.docker.dotfiles import (
    DotfilesProvisioner,
    DotfilesSpec,
    DotfilesSpecGenerator,
    DotfilesStage,
)
from ai.backend.agent.stage.kernel_lifecycle.docker.environ import (
    AgentInfo,
    EnvironProvisioner,
    EnvironSpec,
    EnvironSpecGenerator,
    EnvironStage,
    KernelInfo,
)
from ai.backend.agent.stage.kernel_lifecycle.docker.image.metadata import (
    ImageMetadataProvisioner,
    ImageMetadataSpec,
    ImageMetadataSpecGenerator,
    ImageMetadataStage,
)
from ai.backend.agent.stage.kernel_lifecycle.docker.image.pull import (
    ImagePullCheckSpec,
    ImagePullProvisioner,
    ImagePullSpecGenerator,
    ImagePullStage,
)
from ai.backend.agent.stage.kernel_lifecycle.docker.kernel_object import (
    KernelObjectProvisioner,
    KernelObjectSpec,
    KernelObjectSpecGenerator,
    KernelObjectStage,
)
from ai.backend.agent.stage.kernel_lifecycle.docker.mount.intrinsic import (
    CoreDumpConfig,
    IntrinsicMountProvisioner,
    IntrinsicMountSpec,
    IntrinsicMountSpecGenerator,
    IntrinsicMountStage,
)
from ai.backend.agent.stage.kernel_lifecycle.docker.mount.krunner import (
    KernelRunnerMountProvisioner,
    KernelRunnerMountSpec,
    KernelRunnerMountSpecGenerator,
    KernelRunnerMountStage,
)
from ai.backend.agent.stage.kernel_lifecycle.docker.mount.vfolder import (
    VFolderMountProvisioner,
    VFolderMountSpec,
    VFolderMountSpecGenerator,
    VFolderMountStage,
)
from ai.backend.agent.stage.kernel_lifecycle.docker.network.post_start import (
    NetworkPostSetupProvisioner,
    NetworkPostSetupSpec,
    NetworkPostSetupSpecGenerator,
    NetworkPostSetupStage,
)
from ai.backend.agent.stage.kernel_lifecycle.docker.network.pre_start import (
    NetworkPreSetupProvisioner,
    NetworkPreSetupSpec,
    NetworkPreSetupSpecGenerator,
    NetworkPreSetupStage,
)
from ai.backend.agent.stage.kernel_lifecycle.docker.resource import (
    ResourceProvisioner,
    ResourceSpec,
    ResourceSpecGenerator,
    ResourceStage,
)
from ai.backend.agent.stage.kernel_lifecycle.docker.scratch.create import (
    ScratchCreateProvisioner,
    ScratchCreateSpec,
    ScratchCreateSpecGenerator,
    ScratchCreateStage,
)
from ai.backend.agent.stage.kernel_lifecycle.docker.scratch.path import (
    ScratchPathProvisioner,
    ScratchPathSpec,
    ScratchPathSpecGenerator,
    ScratchPathStage,
)
from ai.backend.agent.stage.kernel_lifecycle.docker.service_port import (
    ServicePortProvisioner,
    ServicePortSpec,
    ServicePortSpecGenerator,
    ServicePortStage,
)
from ai.backend.agent.stage.kernel_lifecycle.docker.types import (
    ContainerOwnershipData,
    NetworkConfig,
)
from ai.backend.agent.stage.kernel_lifecycle.docker.utils import (
    is_mount_ssh,
)
from ai.backend.common.clients.valkey_client.valkey_stat.client import ValkeyStatClient
from ai.backend.common.docker import (
    ImageRef,
)
from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.types import (
    AgentId,
    ContainerId,
    ContainerStatus,
    DeviceName,
    ImageRegistry,
    KernelId,
    Sentinel,
)

from ..affinity_map import AffinityMap
from ..data.cgroup import CGroupInfo
from ..data.kernel.creator import KernelCreationInfo
from ..types import Container
from ..utils import get_arch_name
from .abc import AbstractBackend
from .defs import ACTIVE_STATUS_SET


@dataclass
class KernelLifecycleStage:
    image_metadata: ImageMetadataStage
    scratch_path: ScratchPathStage
    resource: ResourceStage
    environ: EnvironStage
    image_pull: ImagePullStage
    scratch_create: ScratchCreateStage
    network_pre_setup: NetworkPreSetupStage
    network_post_setup: NetworkPostSetupStage
    cluster_ssh: ClusterSSHStage
    intrinsic_mount: IntrinsicMountStage
    krunner_mount: KernelRunnerMountStage
    vfolder_mount: VFolderMountStage
    service_port: ServicePortStage
    cmdarg: CmdArgStage
    bootstrap_create: BootstrapStage
    config_file: ConfigFileStage
    credential: CredentialsStage
    container_ssh: ContainerSSHStage
    dotfile: DotfilesStage
    kernel_object: KernelObjectStage

    container_config: ContainerConfigStage
    container_create: ContainerCreateStage
    container_start: ContainerStartStage
    container_check: ContainerCheckStage


class DockerBackend(AbstractBackend):
    def __init__(
        self,
        config: AgentUnifiedConfig,
        computers: Mapping[DeviceName, ComputerContext],
        affinity_map: AffinityMap,
        resource_lock: asyncio.Lock,
        network_plugin_ctx: NetworkPluginContext,
        gwbridge_subnet: Optional[str],
        agent_sockpath: Path,
        *,
        event_producer: EventProducer,
        valkey_stat_client: ValkeyStatClient,
    ) -> None:
        self._config = config
        self._computers = computers
        self._affinity_map = affinity_map
        self._gwbridge_subnet = gwbridge_subnet
        self._agent_sockpath = agent_sockpath

        self._event_producer = event_producer

        self._kernel_registry: dict[KernelId, KernelObject] = {}

        self._kernel_lifecycle_stage = KernelLifecycleStage(
            image_metadata=ImageMetadataStage(ImageMetadataProvisioner(valkey_stat_client)),
            scratch_path=ScratchPathStage(ScratchPathProvisioner()),
            resource=ResourceStage(ResourceProvisioner(resource_lock)),
            environ=EnvironStage(EnvironProvisioner()),
            image_pull=ImagePullStage(ImagePullProvisioner()),
            scratch_create=ScratchCreateStage(ScratchCreateProvisioner()),
            network_pre_setup=NetworkPreSetupStage(NetworkPreSetupProvisioner(network_plugin_ctx)),
            network_post_setup=NetworkPostSetupStage(NetworkPostSetupProvisioner()),
            cluster_ssh=ClusterSSHStage(ClusterSSHProvisioner()),
            intrinsic_mount=IntrinsicMountStage(IntrinsicMountProvisioner()),
            krunner_mount=KernelRunnerMountStage(KernelRunnerMountProvisioner()),
            vfolder_mount=VFolderMountStage(VFolderMountProvisioner()),
            service_port=ServicePortStage(ServicePortProvisioner(config)),
            cmdarg=CmdArgStage(CmdArgProvisioner()),
            bootstrap_create=BootstrapStage(BootstrapProvisioner()),
            config_file=ConfigFileStage(ConfigFileProvisioner()),
            credential=CredentialsStage(CredentialsProvisioner()),
            container_ssh=ContainerSSHStage(ContainerSSHProvisioner()),
            dotfile=DotfilesStage(DotfilesProvisioner()),
            kernel_object=KernelObjectStage(KernelObjectProvisioner(self._kernel_registry)),
            container_config=ContainerConfigStage(ContainerConfigProvisioner()),
            container_create=ContainerCreateStage(ContainerCreateProvisioner()),
            container_start=ContainerStartStage(ContainerStartProvisioner()),
            container_check=ContainerCheckStage(ContainerCheckProvisioner()),
        )

    @override
    async def create_kernel(
        self,
        info: KernelCreationInfo,
        *,
        throttle_sema: Optional[asyncio.Semaphore] = None,
    ) -> None:
        # Image metadata
        image_metadata_spec = ImageMetadataSpec(
            labels=info.image_labels,
            digest=info.image_digest,
            canonical=info.image_ref.canonical,
        )
        await self._kernel_lifecycle_stage.image_metadata.setup(
            ImageMetadataSpecGenerator(image_metadata_spec)
        )
        image_metadata = await self._kernel_lifecycle_stage.image_metadata.wait_for_resource()
        distro = image_metadata.distro
        kernel_features = image_metadata.kernel_features
        container_ownership = ContainerOwnershipData(
            uid_override=info.uid,
            gid_override=info.main_gid,
            kernel_features=kernel_features,
            kernel_uid=self._config.container.kernel_uid,
            kernel_gid=self._config.container.kernel_gid,
        )

        # Scratch path setup
        scratch_path_spec = ScratchPathSpec(
            kernel_id=info.kernel_id,
            scratch_type=self._config.container.scratch_type,
            scratch_root=self._config.container.scratch_root,
            scratch_size=self._config.container.scratch_size,
        )
        await self._kernel_lifecycle_stage.scratch_path.setup(
            ScratchPathSpecGenerator(scratch_path_spec)
        )
        scratch_path_result = await self._kernel_lifecycle_stage.scratch_path.wait_for_resource()

        # Resource setup
        resource_spec = ResourceSpec(
            resource_slots=info.resource_slots,
            resource_opts=info.resource_opts,
            computers=self._computers,
            allocation_order=list(info.resource_slots.keys()),
            affinity_map=self._affinity_map,
            affinity_policy=self._config.resource.affinity_policy,
            allow_fractional_resource_fragmentation=info.resource_opts.get(
                "allow_fractional_resource_fragmentation", True
            ),
            config_dir=scratch_path_result.config_dir,
        )
        await self._kernel_lifecycle_stage.resource.setup(ResourceSpecGenerator(resource_spec))
        resource_result = await self._kernel_lifecycle_stage.resource.wait_for_resource()

        # Mount intrinsic mounts
        intrinsic_mount_spec = IntrinsicMountSpec(
            config_dir=scratch_path_result.config_dir,
            work_dir=scratch_path_result.work_dir,
            tmp_dir=scratch_path_result.tmp_dir,
            scratch_type=scratch_path_result.scratch_type,
            agent_sockpath=self._agent_sockpath,
            image_ref=info.image_ref,
            coredump=CoreDumpConfig(
                self._config.debug.coredump.enabled,
                self._config.debug.coredump.path,
                self._config.debug.coredump.core_path,
            ),
            ipc_base_path=self._config.agent.ipc_base_path,
            domain_socket_proxies=info.domain_socket_proxies,
        )
        await self._kernel_lifecycle_stage.intrinsic_mount.setup(
            IntrinsicMountSpecGenerator(intrinsic_mount_spec)
        )
        intrinsic_mount_result = (
            await self._kernel_lifecycle_stage.intrinsic_mount.wait_for_resource()
        )

        # Environ setup
        environ_spec = EnvironSpec(
            agent_info=AgentInfo(
                computers=self._computers,
                architecture=get_arch_name(),
                kernel_uid=self._config.container.kernel_uid,
                kernel_gid=self._config.container.kernel_gid,
            ),
            kernel_info=KernelInfo(
                kernel_creation_config=info.kernel_creation_config,
                distro=distro,
                kernel_features=kernel_features,
                resource_spec=resource_result.resource_spec,
                overriding_uid=info.uid,
                overriding_gid=info.main_gid,
                supplementary_gids=set(info.supplementary_gids),
            ),
        )
        await self._kernel_lifecycle_stage.environ.setup(EnvironSpecGenerator(environ_spec))
        environ = await self._kernel_lifecycle_stage.environ.wait_for_resource()

        # Image pull
        image_pull_check_spec = ImagePullCheckSpec(
            image_ref=info.image_ref,
            image_digest=info.image_digest,
            registry_conf=info.image_registry,
            pull_timeout=self._config.api.pull_timeout,
            auto_pull_behavior=info.image_auto_pull,
        )
        await self._kernel_lifecycle_stage.image_pull.setup(
            ImagePullSpecGenerator(image_pull_check_spec)
        )
        _ = await self._kernel_lifecycle_stage.image_pull.wait_for_resource()

        # Scratch creation setup
        scartch_spec = ScratchCreateSpec(
            scratch_dir=scratch_path_result.scratch_dir,
            scratch_file=scratch_path_result.scratch_file,
            tmp_dir=scratch_path_result.tmp_dir,
            work_dir=scratch_path_result.work_dir,
            config_dir=scratch_path_result.config_dir,
            scratch_type=scratch_path_result.scratch_type,
            scratch_size=self._config.container.scratch_size,
            container_ownership=container_ownership,
        )
        await self._kernel_lifecycle_stage.scratch_create.setup(
            ScratchCreateSpecGenerator(scartch_spec)
        )
        _ = await self._kernel_lifecycle_stage.scratch_create.wait_for_resource()

        # Cluster SSH setup
        cluster_ssh_spec = ClusterSSHSpec(
            config_dir=scratch_path_result.config_dir,
            ssh_keypair=info.cluster_info.ssh_keypair,
            cluster_ssh_port_mapping=info.cluster_info.cluster_ssh_port_mapping,
            container_ownership=container_ownership,
        )
        await self._kernel_lifecycle_stage.cluster_ssh.setup(
            ClusterSSHSpecGenerator(cluster_ssh_spec)
        )
        _ = await self._kernel_lifecycle_stage.cluster_ssh.wait_for_resource()

        # Mount vfolders
        vfolder_mount_spec = VFolderMountSpec(
            mounts=info.vfolder_mounts,
            prevent_vfolder_mount=info.prevent_vfolder_mount,
        )
        await self._kernel_lifecycle_stage.vfolder_mount.setup(
            VFolderMountSpecGenerator(vfolder_mount_spec)
        )
        vfolder_mount_result = await self._kernel_lifecycle_stage.vfolder_mount.wait_for_resource()

        # Mount kernel runner
        krunner_mount_spec = KernelRunnerMountSpec(
            distro=distro,
            krunner_volumes=self._config.container.krunner_volumes,
            sandbox_type=self._config.container.sandbox_type,
            existing_computers=self._computers,
            resource_spec=resource_result.resource_spec,
        )
        await self._kernel_lifecycle_stage.krunner_mount.setup(
            KernelRunnerMountSpecGenerator(krunner_mount_spec)
        )
        krunner_mount_result = await self._kernel_lifecycle_stage.krunner_mount.wait_for_resource()

        # Service port setup
        service_port_spec = ServicePortSpec(
            preopen_ports=info.preopen_ports,
            cluster_role=info.cluster_info.cluster_role,
            cluster_hostname=info.cluster_info.cluster_hostname,
            image_labels=info.image_labels,
            allocated_host_ports=info.allocated_host_ports,
            container_bind_host=self._config.container.bind_host,
            resource_group_type=self._config.agent.scaling_group_type,
            cluster_ssh_port_mapping=info.cluster_info.cluster_ssh_port_mapping,
        )
        await self._kernel_lifecycle_stage.service_port.setup(
            ServicePortSpecGenerator(service_port_spec)
        )
        service_port_result = await self._kernel_lifecycle_stage.service_port.wait_for_resource()

        # Command argument setup
        cmdarg_spec = CmdArgSpec(
            runtime_type=image_metadata.runtime_type,
            runtime_path=image_metadata.runtime_path,
            sandbox_type=self._config.container.sandbox_type,
            jail_args=self._config.container.jail_args,
            debug_kernel_runner=self._config.debug.kernel_runner,
        )
        await self._kernel_lifecycle_stage.cmdarg.setup(CmdArgSpecGenerator(cmdarg_spec))
        cmdarg_result = await self._kernel_lifecycle_stage.cmdarg.wait_for_resource()

        # Bootstrap files setup
        bootstrap_spec = BootstrapSpec(
            work_dir=scratch_path_result.work_dir,
            bootstrap_script=info.bootstrap_script,
            container_ownership=container_ownership,
        )
        await self._kernel_lifecycle_stage.bootstrap_create.setup(
            BootstrapSpecGenerator(bootstrap_spec)
        )
        _ = await self._kernel_lifecycle_stage.bootstrap_create.wait_for_resource()

        # Config files setup
        config_file_spec = ConfigFileSpec(
            config_dir=scratch_path_result.config_dir,
            environ=environ.environ,
            resource_spec=resource_result.resource_spec,
            computers=self._computers,
            container_arg=resource_result.container_arg,
        )
        await self._kernel_lifecycle_stage.config_file.setup(
            ConfigFileSpecGenerator(config_file_spec)
        )
        _ = await self._kernel_lifecycle_stage.config_file.wait_for_resource()

        # Credentials setup
        credentials_spec = CredentialsSpec(
            config_dir=scratch_path_result.config_dir,
            docker_credentials=info.docker_credentials,
        )
        await self._kernel_lifecycle_stage.credential.setup(
            CredentialsSpecGenerator(credentials_spec)
        )
        _ = await self._kernel_lifecycle_stage.credential.wait_for_resource()

        ssh_already_mounted = any(
            is_mount_ssh(mount)
            for mount in itertools.chain(
                vfolder_mount_result.mounts,
                krunner_mount_result.mounts,
                intrinsic_mount_result.mounts,
            )
        )
        # Container SSH setup
        container_ssh_spec = ContainerSSHSpec(
            work_dir=scratch_path_result.work_dir,
            ssh_keypair=info.container_ssh_keypair,
            ssh_already_mounted=ssh_already_mounted,
            container_ownership=container_ownership,
        )
        await self._kernel_lifecycle_stage.container_ssh.setup(
            ContainerSSHSpecGenerator(container_ssh_spec)
        )
        _ = await self._kernel_lifecycle_stage.container_ssh.wait_for_resource()

        # Dotfiles setup
        dotfiles_spec = DotfilesSpec(
            dotfiles=info.dotfiles,
            scratch_dir=scratch_path_result.scratch_dir,
            work_dir=scratch_path_result.work_dir,
            container_ownership=container_ownership,
        )
        await self._kernel_lifecycle_stage.dotfile.setup(DotfilesSpecGenerator(dotfiles_spec))
        _ = await self._kernel_lifecycle_stage.dotfile.wait_for_resource()

        # Network setup
        # Networking setup should be done after all container ports mapped to host ports
        network_spec = NetworkPreSetupSpec(
            kernel_config=info.kernel_creation_config,
            cluster_size=info.cluster_info.cluster_size,
            replicas=info.cluster_info.replicas,
            network_config=NetworkConfig(
                info.cluster_info.cluster_mode, info.cluster_info.network_id
            ),
            ssh_keypair=info.cluster_info.ssh_keypair,
            cluster_ssh_port_mapping=info.cluster_info.cluster_ssh_port_mapping,
            gwbridge_subnet=self._gwbridge_subnet,
            alternative_bridge=self._config.container.alternative_bridge,
        )
        await self._kernel_lifecycle_stage.network_pre_setup.setup(
            NetworkPreSetupSpecGenerator(network_spec)
        )
        network_result = await self._kernel_lifecycle_stage.network_pre_setup.wait_for_resource()

        # Update container config with compute plugin config
        container_config_spec = ContainerConfigSpec(
            ownership_data=info.ownership,
            image=info.image_ref,
            image_labels=info.image_labels,
            container_log_size=self._config.container_logs.max_length,
            container_log_file_count=DEFAULT_CONTAINER_LOG_FILE_COUNT,
            port_mappings=service_port_result.port_mapping_result,
            service_port_container_label=service_port_result.service_port_container_label,
            block_service_ports=info.block_service_ports,
            environ=environ.environ,
            cmdargs=cmdarg_result.cmdargs,
            cluster_hostname=info.cluster_info.cluster_hostname,
            resource_container_args=resource_result.container_arg,
            network_container_args=network_result.container_arg,
        )
        await self._kernel_lifecycle_stage.container_config.setup(
            ContainerConfigSpecGenerator(container_config_spec)
        )
        container_config_result = (
            await self._kernel_lifecycle_stage.container_config.wait_for_resource()
        )

        # Create container
        container_create_spec = ContainerCreateSpec(
            container_config_result.raw_config,
            image=info.image_ref,
            ownership_data=info.ownership,
        )
        await self._kernel_lifecycle_stage.container_create.setup(
            ContainerCreateSpecGenerator(container_create_spec)
        )
        container_create_result = (
            await self._kernel_lifecycle_stage.container_create.wait_for_resource()
        )

        # Write resource.txt & Start container & set sudo session
        container_start_spec = ContainerStartSpec(
            container_id=container_create_result.container_id,
            service_ports=service_port_result.service_ports,
            config_dir=scratch_path_result.config_dir,
        )
        await self._kernel_lifecycle_stage.container_start.setup(
            ContainerStartSpecGenerator(container_start_spec)
        )
        _ = await self._kernel_lifecycle_stage.container_start.wait_for_resource()

        network_post_setup_spec = NetworkPostSetupSpec(
            container_id=container_create_result.container_id,
            mode=network_result.mode,
            network_plugin=network_result.network_plugin,
            container_bind_host=self._config.container.bind_host,
            additional_network_names=resource_result.additional_network_names,
            service_ports=service_port_result.service_ports,
            port_mappings=service_port_result.port_mapping_result,
            advertised_kernel_host=self._config.container.advertised_host,
        )
        await self._kernel_lifecycle_stage.network_post_setup.setup(
            NetworkPostSetupSpecGenerator(network_post_setup_spec)
        )
        network_post_setup_result = (
            await self._kernel_lifecycle_stage.network_post_setup.wait_for_resource()
        )

        # Kernel object setup
        kernel_object_spec = KernelObjectSpec(
            ownership_data=info.ownership,
            image_ref=info.image_ref,
            repl_in_port=network_post_setup_result.repl_in_port,
            repl_out_port=network_post_setup_result.repl_out_port,
            network_id=info.cluster_info.network_id,
            network_mode=network_result.mode,
            service_ports=service_port_result.service_ports,
            resource_spec=resource_result.resource_spec,
            environ=environ.environ,
            event_producer=self._event_producer,
        )
        await self._kernel_lifecycle_stage.kernel_object.setup(
            KernelObjectSpecGenerator(kernel_object_spec)
        )
        kernel_object_result = await self._kernel_lifecycle_stage.kernel_object.wait_for_resource()

        container_check_spec = ContainerCheckSpec(
            ownership_data=info.ownership,
            container_id=container_create_result.container_id,
            kernel_init_polling_attempt=self._config.kernel_lifecycles.init_polling_attempt,
            kernel_init_polling_timeout=self._config.kernel_lifecycles.init_polling_timeout_sec,
            kernel_init_timeout=self._config.kernel_lifecycles.init_timeout_sec,
            kernel_object=kernel_object_result.kernel,
            service_ports=service_port_result.service_ports,
        )
        await self._kernel_lifecycle_stage.container_check.setup(
            ContainerCheckSpecGenerator(container_check_spec)
        )
        _ = await self._kernel_lifecycle_stage.container_check.wait_for_resource()

    @override
    async def create_local_network(self, network_name: str) -> None:
        """
        Create a local bridge network for a single-node multicontainer session, where containers in the
        same agent can connect to each other using cluster hostnames without explicit port mapping.

        This is called by the manager before kernel creation.
        It may raise :exc:`NotImplementedError` and then the manager
        will cancel creation of the session.
        """
        raise NotImplementedError

    @override
    async def destroy_kernel(self, kernel_id: KernelId) -> None:
        raise NotImplementedError

    @override
    async def destroy_local_network(self, network_name: str) -> None:
        """
        Destroy a local bridge network used for a single-node multi-container session.

        This is called by the manager after kernel destruction.
        """
        raise NotImplementedError

    @override
    async def clean_kernel(self, kernel_id: KernelId) -> None:
        raise NotImplementedError

    @override
    async def restart_kernel(self, kernel_id: KernelId) -> None:
        # TODO: Implement kernel restart logic
        raise NotImplementedError

    @override
    async def yield_temp_container(self, image: ImageRef) -> AsyncIterator[Container]:
        """
        Yield a temporary container from given image.
        This is used to run backend-specific tasks that require a container.
        The container should be cleaned up after use.
        """
        raise NotImplementedError

    @override
    async def get_container_logs(self, container_id: ContainerId) -> list[str]:
        """
        Get the logs of the container.
        This method should return a list of log lines as strings.
        """
        raise NotImplementedError

    @override
    async def get_managed_images(self) -> tuple[ImageRef]:
        raise NotImplementedError

    @override
    async def get_managed_containers(
        self,
        agent_id: Optional[AgentId] = None,
        status_filter: frozenset[ContainerStatus] = ACTIVE_STATUS_SET,
    ) -> tuple[Container]:
        """
        Get all containers managed by this backend.
        This method should return a tuple of Container objects.
        """
        raise NotImplementedError

    @override
    def get_cgroup_info(self, container_id: ContainerId, controller: str) -> CGroupInfo:
        """
        Get the cgroup path for the given controller and container ID, and the cgroup version.
        This is used to read/write cgroup files for resource management.
        """
        raise NotImplementedError

    @override
    async def push_image(
        self,
        image_ref: ImageRef,
        registry_conf: ImageRegistry,
        *,
        timeout: float | None | Sentinel = Sentinel.TOKEN,
    ) -> None:
        """
        Push the image.
        This method should be implemented by the backend to handle image pushing.
        """
        raise NotImplementedError

    @override
    async def pull_image(
        self,
        image_ref: ImageRef,
        registry_conf: ImageRegistry,
        *,
        timeout: float | None | Sentinel = Sentinel.TOKEN,
    ) -> None:
        """
        Pull the image.
        This method should be implemented by the backend to handle image pulling.
        """
        raise NotImplementedError


async def make_docker_backend(
    config: AgentUnifiedConfig,
    local_instance_id: str,
    computers: Mapping[DeviceName, ComputerContext],
    affinity_map: AffinityMap,
    resource_lock: asyncio.Lock,
    network_plugin_ctx: NetworkPluginContext,
    *,
    event_producer: EventProducer,
    valkey_stat_client: ValkeyStatClient,
) -> DockerBackend:
    gwbridge_subnet: Optional[str] = None
    try:
        async with Docker() as docker:
            gwbridge = await docker.networks.get("docker_gwbridge")
            gwbridge_info = await gwbridge.show()
            gwbridge_subnet = gwbridge_info["IPAM"]["Config"][0]["Subnet"]
    except (DockerError, KeyError, IndexError):
        pass

    ipc_base_path = config.agent.ipc_base_path
    agent_sockpath = ipc_base_path / "container" / f"agent.{local_instance_id}.sock"
    if sys.platform != "darwin":
        socket_relay_name = f"backendai-socket-relay.{local_instance_id}"
        socket_relay_container = PersistentServiceContainer(
            "backendai-socket-relay:latest",
            {
                "Cmd": [
                    f"UNIX-LISTEN:/ipc/{agent_sockpath.name},unlink-early,fork,mode=777",
                    f"TCP-CONNECT:127.0.0.1:{config.agent.agent_sock_port}",
                ],
                "HostConfig": {
                    "Mounts": [
                        {
                            "Type": "bind",
                            "Source": str(ipc_base_path / "container"),
                            "Target": "/ipc",
                        },
                    ],
                    "NetworkMode": "host",
                },
            },
            name=socket_relay_name,
        )
        await socket_relay_container.ensure_running_latest()
    return DockerBackend(
        config,
        computers,
        affinity_map,
        resource_lock,
        network_plugin_ctx,
        gwbridge_subnet,
        agent_sockpath,
        event_producer=event_producer,
        valkey_stat_client=valkey_stat_client,
    )
