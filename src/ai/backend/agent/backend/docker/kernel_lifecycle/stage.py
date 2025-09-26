import asyncio
import itertools
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional, Self, override

from ai.backend.agent.affinity_map import AffinityMap
from ai.backend.agent.config.unified import AgentUnifiedConfig
from ai.backend.agent.data.kernel.creator import (
    ClusterInfo,
    DotfileInfo,
    KernelCreationInfo,
)
from ai.backend.agent.plugin.network import NetworkPluginContext
from ai.backend.agent.proxy import DomainSocketProxy
from ai.backend.agent.resources import ComputerContext
from ai.backend.agent.types import KernelOwnershipData
from ai.backend.agent.utils import get_arch_name
from ai.backend.common.clients.valkey_client.valkey_stat.client import ValkeyStatClient
from ai.backend.common.docker import (
    ImageRef,
    LabelName,
)
from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.stage.types import (
    ArgsSpecGenerator,
    Provisioner,
    ProvisionStage,
)
from ai.backend.common.types import (
    AutoPullBehavior,
    ContainerSSHKeyPair,
    DeviceName,
    ImageRegistry,
    KernelCreationConfig,
    KernelId,
    ResourceSlot,
    VFolderMount,
)

# Import all substage modules
from .substage.bootstrap import (
    BootstrapProvisioner,
    BootstrapResult,
    BootstrapSpec,
    BootstrapSpecGenerator,
    BootstrapStage,
)
from .substage.cluster_ssh import (
    ClusterSSHProvisioner,
    ClusterSSHResult,
    ClusterSSHSpec,
    ClusterSSHSpecGenerator,
    ClusterSSHStage,
)
from .substage.cmdarg import (
    CmdArgProvisioner,
    CmdArgResult,
    CmdArgSpec,
    CmdArgSpecGenerator,
    CmdArgStage,
)
from .substage.config_files import (
    ConfigFileProvisioner,
    ConfigFileResult,
    ConfigFileSpec,
    ConfigFileSpecGenerator,
    ConfigFileStage,
)
from .substage.container.check import (
    ContainerCheckProvisioner,
    ContainerCheckResult,
    ContainerCheckSpec,
    ContainerCheckSpecGenerator,
    ContainerCheckStage,
)
from .substage.container.config import (
    ContainerConfigProvisioner,
    ContainerConfigResult,
    ContainerConfigSpec,
    ContainerConfigSpecGenerator,
    ContainerConfigStage,
)
from .substage.container.create import (
    ContainerCreateProvisioner,
    ContainerCreateResult,
    ContainerCreateSpec,
    ContainerCreateSpecGenerator,
    ContainerCreateStage,
)
from .substage.container.start import (
    ContainerStartProvisioner,
    ContainerStartResult,
    ContainerStartSpec,
    ContainerStartSpecGenerator,
    ContainerStartStage,
)
from .substage.container_ssh import (
    ContainerSSHProvisioner,
    ContainerSSHResult,
    ContainerSSHSpec,
    ContainerSSHSpecGenerator,
    ContainerSSHStage,
)
from .substage.credentials import (
    CredentialsProvisioner,
    CredentialsResult,
    CredentialsSpec,
    CredentialsSpecGenerator,
    CredentialsStage,
)
from .substage.defs import DEFAULT_CONTAINER_LOG_FILE_COUNT
from .substage.dotfiles import (
    DotfilesProvisioner,
    DotfilesResult,
    DotfilesSpec,
    DotfilesSpecGenerator,
    DotfilesStage,
)
from .substage.environ import (
    AgentInfo,
    EnvironProvisioner,
    EnvironResult,
    EnvironSpec,
    EnvironSpecGenerator,
    EnvironStage,
    KernelInfo,
)
from .substage.image.metadata import (
    ImageMetadataProvisioner,
    ImageMetadataResult,
    ImageMetadataSpec,
    ImageMetadataSpecGenerator,
    ImageMetadataStage,
)
from .substage.image.pull import (
    ImagePullCheckSpec,
    ImagePullProvisioner,
    ImagePullResult,
    ImagePullSpecGenerator,
    ImagePullStage,
)
from .substage.kernel_object import (
    KernelObjectProvisioner,
    KernelObjectResult,
    KernelObjectSpec,
    KernelObjectSpecGenerator,
    KernelObjectStage,
)
from .substage.mount.intrinsic import (
    CoreDumpConfig,
    IntrinsicMountProvisioner,
    IntrinsicMountResult,
    IntrinsicMountSpec,
    IntrinsicMountSpecGenerator,
    IntrinsicMountStage,
)
from .substage.mount.krunner import (
    KernelRunnerMountProvisioner,
    KernelRunnerMountResult,
    KernelRunnerMountSpec,
    KernelRunnerMountSpecGenerator,
    KernelRunnerMountStage,
)
from .substage.mount.vfolder import (
    VFolderMountProvisioner,
    VFolderMountResult,
    VFolderMountSpec,
    VFolderMountSpecGenerator,
    VFolderMountStage,
)
from .substage.network.post_start import (
    NetworkPostSetupProvisioner,
    NetworkPostSetupResult,
    NetworkPostSetupSpec,
    NetworkPostSetupSpecGenerator,
    NetworkPostSetupStage,
)
from .substage.network.pre_start import (
    NetworkPreSetupProvisioner,
    NetworkPreSetupResult,
    NetworkPreSetupSpec,
    NetworkPreSetupSpecGenerator,
    NetworkPreSetupStage,
)
from .substage.resource import (
    ResourceProvisioner,
    ResourceResult,
    ResourceSpec,
    ResourceSpecGenerator,
    ResourceStage,
)
from .substage.scratch.create import (
    ScratchCreateProvisioner,
    ScratchCreateResult,
    ScratchCreateSpec,
    ScratchCreateSpecGenerator,
    ScratchCreateStage,
)
from .substage.scratch.path import (
    ScratchPathProvisioner,
    ScratchPathResult,
    ScratchPathSpec,
    ScratchPathSpecGenerator,
    ScratchPathStage,
)
from .substage.service_port import (
    ServicePortProvisioner,
    ServicePortResult,
    ServicePortSpec,
    ServicePortSpecGenerator,
    ServicePortStage,
)
from .substage.types import ContainerOwnershipData, NetworkConfig
from .substage.utils import is_mount_ssh


@dataclass
class KernelCreationSpec:
    kernel_id: KernelId
    kernel_creation_config: KernelCreationConfig  # TODO: Remove this field after refactoring

    ownership: KernelOwnershipData

    image_ref: ImageRef
    image_labels: Mapping[LabelName, str]
    image_registry: ImageRegistry
    image_digest: str
    image_auto_pull: AutoPullBehavior

    uid: Optional[int]
    main_gid: Optional[int]
    supplementary_gids: list[int]

    vfolder_mounts: list[VFolderMount]
    dotfiles: list[DotfileInfo]

    cluster_info: ClusterInfo
    resource_slots: ResourceSlot
    resource_opts: dict[str, Any]

    environ: dict[str, str]
    bootstrap_script: Optional[str]
    startup_command: Optional[str]
    internal_data: dict[str, Any]
    preopen_ports: list[int]
    allocated_host_ports: list[int]
    block_service_ports: bool

    docker_credentials: Optional[dict[str, Any]]
    container_ssh_keypair: ContainerSSHKeyPair

    # Is this field used in real?
    prevent_vfolder_mount: bool = False
    domain_socket_proxies: list[DomainSocketProxy] = field(default_factory=list)

    @classmethod
    def from_creation_info(cls, creation_info: KernelCreationInfo) -> Self:
        return cls(
            kernel_id=creation_info.kernel_id,
            kernel_creation_config=creation_info.kernel_creation_config,
            ownership=creation_info.ownership,
            image_ref=creation_info.image_ref,
            image_labels=creation_info.image_labels,
            image_registry=creation_info.image_registry,
            image_digest=creation_info.image_digest,
            image_auto_pull=creation_info.image_auto_pull,
            uid=creation_info.uid,
            main_gid=creation_info.main_gid,
            supplementary_gids=creation_info.supplementary_gids,
            vfolder_mounts=creation_info.vfolder_mounts,
            dotfiles=creation_info.dotfiles,
            cluster_info=creation_info.cluster_info,
            resource_slots=creation_info.resource_slots,
            resource_opts=creation_info.resource_opts,
            environ=creation_info.environ,
            bootstrap_script=creation_info.bootstrap_script,
            startup_command=creation_info.startup_command,
            internal_data=creation_info.internal_data,
            preopen_ports=creation_info.preopen_ports,
            allocated_host_ports=creation_info.allocated_host_ports,
            block_service_ports=creation_info.block_service_ports,
            docker_credentials=creation_info.docker_credentials,
            container_ssh_keypair=creation_info.container_ssh_keypair,
        )


@dataclass
class KernelCreationResult:
    image_metadata: ImageMetadataResult
    scratch_path: ScratchPathResult
    resource: ResourceResult
    environ: EnvironResult
    image_pull: ImagePullResult
    scratch_create: ScratchCreateResult
    network_pre_setup: NetworkPreSetupResult
    network_post_setup: NetworkPostSetupResult
    cluster_ssh: ClusterSSHResult
    intrinsic_mount: IntrinsicMountResult
    krunner_mount: KernelRunnerMountResult
    vfolder_mount: VFolderMountResult
    service_port: ServicePortResult
    cmdarg: CmdArgResult
    bootstrap: BootstrapResult
    config_file: ConfigFileResult
    credentials: CredentialsResult
    container_ssh: ContainerSSHResult
    dotfiles: DotfilesResult
    kernel_object: KernelObjectResult
    container_config: ContainerConfigResult
    container_create: ContainerCreateResult
    container_start: ContainerStartResult
    container_check: ContainerCheckResult


class KernelCreationSpecGenerator(ArgsSpecGenerator[KernelCreationSpec]):
    pass


@dataclass
class KernelLifecycleStages:
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


class KernelCreationProvisioner(Provisioner[KernelCreationSpec, KernelCreationResult]):
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

        self._kernel_lifecycle_stage = KernelLifecycleStages(
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
            kernel_object=KernelObjectStage(KernelObjectProvisioner()),
            container_config=ContainerConfigStage(ContainerConfigProvisioner()),
            container_create=ContainerCreateStage(ContainerCreateProvisioner()),
            container_start=ContainerStartStage(ContainerStartProvisioner()),
            container_check=ContainerCheckStage(ContainerCheckProvisioner()),
        )

    @property
    @override
    def name(self) -> str:
        return "docker-kernel-creation"

    @override
    async def setup(self, spec: KernelCreationSpec) -> KernelCreationResult:
        image_metadata_spec = ImageMetadataSpec(
            labels=spec.image_labels,
            digest=spec.image_digest,
            canonical=spec.image_ref.canonical,
        )
        await self._kernel_lifecycle_stage.image_metadata.setup(
            ImageMetadataSpecGenerator(image_metadata_spec)
        )
        image_metadata = await self._kernel_lifecycle_stage.image_metadata.wait_for_resource()
        distro = image_metadata.distro
        kernel_features = image_metadata.kernel_features
        container_ownership = ContainerOwnershipData(
            uid_override=spec.uid,
            gid_override=spec.main_gid,
            kernel_features=kernel_features,
            kernel_uid=self._config.container.kernel_uid,
            kernel_gid=self._config.container.kernel_gid,
        )

        # Scratch path setup
        scratch_path_spec = ScratchPathSpec(
            kernel_id=spec.kernel_id,
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
            resource_slots=spec.resource_slots,
            resource_opts=spec.resource_opts,
            computers=self._computers,
            allocation_order=list(spec.resource_slots.keys()),
            affinity_map=self._affinity_map,
            affinity_policy=self._config.resource.affinity_policy,
            allow_fractional_resource_fragmentation=spec.resource_opts.get(
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
            image_ref=spec.image_ref,
            coredump=CoreDumpConfig(
                self._config.debug.coredump.enabled,
                self._config.debug.coredump.path,
                self._config.debug.coredump.core_path,
            ),
            ipc_base_path=self._config.agent.ipc_base_path,
            domain_socket_proxies=spec.domain_socket_proxies,
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
                kernel_creation_config=spec.kernel_creation_config,
                distro=distro,
                kernel_features=kernel_features,
                resource_spec=resource_result.resource_spec,
                overriding_uid=spec.uid,
                overriding_gid=spec.main_gid,
                supplementary_gids=set(spec.supplementary_gids),
            ),
        )
        await self._kernel_lifecycle_stage.environ.setup(EnvironSpecGenerator(environ_spec))
        environ = await self._kernel_lifecycle_stage.environ.wait_for_resource()

        # Image pull
        image_pull_check_spec = ImagePullCheckSpec(
            image_ref=spec.image_ref,
            image_digest=spec.image_digest,
            registry_conf=spec.image_registry,
            pull_timeout=self._config.api.pull_timeout,
            auto_pull_behavior=spec.image_auto_pull,
        )
        await self._kernel_lifecycle_stage.image_pull.setup(
            ImagePullSpecGenerator(image_pull_check_spec)
        )
        image_pull_result = await self._kernel_lifecycle_stage.image_pull.wait_for_resource()

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
        scratch_create_result = (
            await self._kernel_lifecycle_stage.scratch_create.wait_for_resource()
        )

        # Cluster SSH setup
        cluster_ssh_spec = ClusterSSHSpec(
            config_dir=scratch_path_result.config_dir,
            ssh_keypair=spec.cluster_info.ssh_keypair,
            cluster_ssh_port_mapping=spec.cluster_info.cluster_ssh_port_mapping,
            container_ownership=container_ownership,
        )
        await self._kernel_lifecycle_stage.cluster_ssh.setup(
            ClusterSSHSpecGenerator(cluster_ssh_spec)
        )
        cluster_ssh_result = await self._kernel_lifecycle_stage.cluster_ssh.wait_for_resource()

        # Mount vfolders
        vfolder_mount_spec = VFolderMountSpec(
            mounts=spec.vfolder_mounts,
            prevent_vfolder_mount=spec.prevent_vfolder_mount,
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
            preopen_ports=spec.preopen_ports,
            cluster_role=spec.cluster_info.cluster_role,
            cluster_hostname=spec.cluster_info.cluster_hostname,
            image_labels=spec.image_labels,
            allocated_host_ports=spec.allocated_host_ports,
            container_bind_host=self._config.container.bind_host,
            resource_group_type=self._config.agent.scaling_group_type,
            cluster_ssh_port_mapping=spec.cluster_info.cluster_ssh_port_mapping,
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
            bootstrap_script=spec.bootstrap_script,
            container_ownership=container_ownership,
        )
        await self._kernel_lifecycle_stage.bootstrap_create.setup(
            BootstrapSpecGenerator(bootstrap_spec)
        )
        bootstrap_result = await self._kernel_lifecycle_stage.bootstrap_create.wait_for_resource()

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
        config_file_result = await self._kernel_lifecycle_stage.config_file.wait_for_resource()

        # Credentials setup
        credentials_spec = CredentialsSpec(
            config_dir=scratch_path_result.config_dir,
            docker_credentials=spec.docker_credentials,
        )
        await self._kernel_lifecycle_stage.credential.setup(
            CredentialsSpecGenerator(credentials_spec)
        )
        credentials_result = await self._kernel_lifecycle_stage.credential.wait_for_resource()

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
            ssh_keypair=spec.container_ssh_keypair,
            ssh_already_mounted=ssh_already_mounted,
            container_ownership=container_ownership,
        )
        await self._kernel_lifecycle_stage.container_ssh.setup(
            ContainerSSHSpecGenerator(container_ssh_spec)
        )
        container_ssh_result = await self._kernel_lifecycle_stage.container_ssh.wait_for_resource()

        # Dotfiles setup
        dotfiles_spec = DotfilesSpec(
            dotfiles=spec.dotfiles,
            scratch_dir=scratch_path_result.scratch_dir,
            work_dir=scratch_path_result.work_dir,
            container_ownership=container_ownership,
        )
        await self._kernel_lifecycle_stage.dotfile.setup(DotfilesSpecGenerator(dotfiles_spec))
        dotfiles_result = await self._kernel_lifecycle_stage.dotfile.wait_for_resource()

        # Network setup
        # Networking setup should be done after all container ports mapped to host ports
        network_spec = NetworkPreSetupSpec(
            kernel_config=spec.kernel_creation_config,
            cluster_size=spec.cluster_info.cluster_size,
            replicas=spec.cluster_info.replicas,
            network_config=NetworkConfig(
                spec.cluster_info.cluster_mode, spec.cluster_info.network_id
            ),
            ssh_keypair=spec.cluster_info.ssh_keypair,
            cluster_ssh_port_mapping=spec.cluster_info.cluster_ssh_port_mapping,
            gwbridge_subnet=self._gwbridge_subnet,
            alternative_bridge=self._config.container.alternative_bridge,
        )
        await self._kernel_lifecycle_stage.network_pre_setup.setup(
            NetworkPreSetupSpecGenerator(network_spec)
        )
        network_result = await self._kernel_lifecycle_stage.network_pre_setup.wait_for_resource()

        # Update container config with compute plugin config
        container_config_spec = ContainerConfigSpec(
            ownership_data=spec.ownership,
            image=spec.image_ref,
            image_labels=spec.image_labels,
            container_log_size=self._config.container_logs.max_length,
            container_log_file_count=DEFAULT_CONTAINER_LOG_FILE_COUNT,
            port_mappings=service_port_result.port_mapping_result,
            service_port_container_label=service_port_result.service_port_container_label,
            block_service_ports=spec.block_service_ports,
            environ=environ.environ,
            cmdargs=cmdarg_result.cmdargs,
            cluster_hostname=spec.cluster_info.cluster_hostname,
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
            image=spec.image_ref,
            ownership_data=spec.ownership,
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
        container_start_result = (
            await self._kernel_lifecycle_stage.container_start.wait_for_resource()
        )

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
            ownership_data=spec.ownership,
            image_ref=spec.image_ref,
            repl_in_port=network_post_setup_result.repl_in_port,
            repl_out_port=network_post_setup_result.repl_out_port,
            network_id=spec.cluster_info.network_id,
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
            ownership_data=spec.ownership,
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
        container_check_result = (
            await self._kernel_lifecycle_stage.container_check.wait_for_resource()
        )

        # Return all substage results
        return KernelCreationResult(
            image_metadata=image_metadata,
            scratch_path=scratch_path_result,
            resource=resource_result,
            environ=environ,
            image_pull=image_pull_result,
            scratch_create=scratch_create_result,
            network_pre_setup=network_result,
            network_post_setup=network_post_setup_result,
            cluster_ssh=cluster_ssh_result,
            intrinsic_mount=intrinsic_mount_result,
            krunner_mount=krunner_mount_result,
            vfolder_mount=vfolder_mount_result,
            service_port=service_port_result,
            cmdarg=cmdarg_result,
            bootstrap=bootstrap_result,
            config_file=config_file_result,
            credentials=credentials_result,
            container_ssh=container_ssh_result,
            dotfiles=dotfiles_result,
            kernel_object=kernel_object_result,
            container_config=container_config_result,
            container_create=container_create_result,
            container_start=container_start_result,
            container_check=container_check_result,
        )

    @override
    async def teardown(self, resource: KernelCreationResult) -> None:
        # Teardown in reverse order of setup
        await self._kernel_lifecycle_stage.container_check.teardown()
        await self._kernel_lifecycle_stage.kernel_object.teardown()
        await self._kernel_lifecycle_stage.network_post_setup.teardown()
        await self._kernel_lifecycle_stage.container_start.teardown()
        await self._kernel_lifecycle_stage.container_create.teardown()
        await self._kernel_lifecycle_stage.container_config.teardown()
        await self._kernel_lifecycle_stage.network_pre_setup.teardown()
        await self._kernel_lifecycle_stage.dotfile.teardown()
        await self._kernel_lifecycle_stage.container_ssh.teardown()
        await self._kernel_lifecycle_stage.credential.teardown()
        await self._kernel_lifecycle_stage.config_file.teardown()
        await self._kernel_lifecycle_stage.bootstrap_create.teardown()
        await self._kernel_lifecycle_stage.cmdarg.teardown()
        await self._kernel_lifecycle_stage.service_port.teardown()
        await self._kernel_lifecycle_stage.krunner_mount.teardown()
        await self._kernel_lifecycle_stage.vfolder_mount.teardown()
        await self._kernel_lifecycle_stage.cluster_ssh.teardown()
        await self._kernel_lifecycle_stage.scratch_create.teardown()
        await self._kernel_lifecycle_stage.image_pull.teardown()
        await self._kernel_lifecycle_stage.environ.teardown()
        await self._kernel_lifecycle_stage.intrinsic_mount.teardown()
        await self._kernel_lifecycle_stage.resource.teardown()
        await self._kernel_lifecycle_stage.scratch_path.teardown()
        await self._kernel_lifecycle_stage.image_metadata.teardown()


class KernelCreationStage(ProvisionStage[KernelCreationSpec, KernelCreationResult]):
    pass
