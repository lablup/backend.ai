import asyncio
import functools
import hashlib
import logging
import os
import random
import shutil
import signal
import sys
import uuid
from decimal import Decimal
from io import StringIO
from pathlib import Path
from typing import (
    TYPE_CHECKING,
    Any,
    FrozenSet,
    List,
    Mapping,
    MutableMapping,
    Optional,
    Sequence,
    Tuple,
    Union,
    override,
)

import aiotools
import cattr
import pkg_resources
from kubernetes.client.models import V1Service, V1ServicePort

from ai.backend.agent.etcd import AgentEtcdClientView
from ai.backend.common.asyncio import current_loop
from ai.backend.common.auth import PublicKey
from ai.backend.common.docker import ImageRef, KernelFeatures, LabelName
from ai.backend.common.dto.agent.response import PurgeImagesResp
from ai.backend.common.dto.manager.rpc_request import PurgeImagesReq
from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.plugin.monitor import ErrorPluginContext, StatsPluginContext
from ai.backend.common.types import (
    AutoPullBehavior,
    ClusterInfo,
    ClusterSSHPortMapping,
    ContainerId,
    ContainerStatus,
    DeviceId,
    DeviceName,
    ImageConfig,
    ImageRegistry,
    KernelCreationConfig,
    KernelId,
    MountPermission,
    MountTypes,
    ResourceSlot,
    Sentinel,
    SlotName,
    VFolderMount,
    current_resource_slots,
)
from ai.backend.logging import BraceStyleAdapter

from ..agent import (
    ACTIVE_STATUS_SET,
    AbstractAgent,
    AbstractKernelCreationContext,
    ScanImagesResult,
)
from ..config.unified import AgentUnifiedConfig, ScratchType
from ..exception import K8sError, UnsupportedResource
from ..kernel import AbstractKernel, KernelRegistry
from ..resources import (
    AbstractComputePlugin,
    ComputerContext,
    KernelResourceSpec,
    Mount,
    known_slot_types,
)
from ..types import Container, KernelOwnershipData, MountInfo, Port
from .kernel import KubernetesKernel
from .kube_object import (
    ConfigMap,
    HostPathPersistentVolume,
    KubernetesAbstractVolume,
    KubernetesConfigMapVolume,
    KubernetesHostPathVolume,
    KubernetesPVCVolume,
    KubernetesVolumeMount,
    NFSPersistentVolume,
    PersistentVolumeClaim,
    Service,
)
from .utils import (
    cleanup_kube_client,
    ensure_kube_client_initialized,
    get_apps_api,
    get_batch_api,
    get_core_api,
)

if TYPE_CHECKING:
    from ai.backend.common.auth import PublicKey

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class KubernetesKernelCreationContext(AbstractKernelCreationContext[KubernetesKernel]):
    config_map_name: str
    deployment_name: str
    scratch_dir: Path
    work_dir: Path
    config_dir: Path
    internal_mounts: List[Mount] = []
    static_pvc_name: str
    workers: Mapping[str, Mapping[str, str]]
    config_maps: List[ConfigMap]
    agent_sockpath: Path
    volume_mounts: List[KubernetesVolumeMount]
    volumes: List[KubernetesAbstractVolume]

    def __init__(
        self,
        ownership_data: KernelOwnershipData,
        event_producer: EventProducer,
        kernel_image: ImageRef,
        kernel_config: KernelCreationConfig,
        distro: str,
        local_config: AgentUnifiedConfig,
        agent_sockpath: Path,
        computers: Mapping[DeviceName, ComputerContext],
        workers: Mapping[str, Mapping[str, str]],
        static_pvc_name: str,
        node_name: str,
        restarting: bool = False,
    ) -> None:
        super().__init__(
            ownership_data,
            event_producer,
            kernel_image,
            kernel_config,
            distro,
            local_config,
            computers,
            restarting=restarting,
        )
        kernel_id = ownership_data.kernel_id
        scratch_dir = (self.local_config.container.scratch_root / str(kernel_id)).resolve()
        rel_scratch_dir = Path(str(kernel_id))  # need relative path for nfs mount

        self.scratch_dir = scratch_dir
        self.rel_scratch_dir = rel_scratch_dir
        self.work_dir = scratch_dir / "work"
        self.config_dir = scratch_dir / "config"
        self.rel_work_dir = self.rel_scratch_dir / "work"
        self.rel_config_dir = self.rel_scratch_dir / "config"

        self.static_pvc_name = static_pvc_name
        self.workers = workers
        self.agent_sockpath = agent_sockpath
        self.node_name = node_name
        self.namespace = os.environ.get("POD_NAMESPACE", "backend-ai-test")

        self.volume_mounts = []
        self.volumes = [
            KubernetesPVCVolume(
                name=f"kernel-{self.kernel_id}-scratches",
                persistentVolumeClaim={
                    "claimName": self.static_pvc_name,
                },
            ),
        ]

        self.config_maps = []

        # Kubernetes-specific attributes for GPU/accelerator allocation
        self.resource_limits: dict[str, str] = {}
        self.resource_requests: dict[str, str] = {}
        self.extra_mounts: list[dict[str, Any]] = []
        self.runtime_class: str | None = None  # Set by plugins via apply_accelerator_allocation()

        # Track symlinks for init container (populated in process_mounts)
        self.symlink_mappings: dict[str, str] = {}

    @override
    async def get_extra_envs(self) -> Mapping[str, str]:
        return {}

    @override
    async def prepare_resource_spec(self) -> Tuple[KernelResourceSpec, Optional[Mapping[str, Any]]]:
        loop = current_loop()
        if self.restarting:
            ensure_kube_client_initialized()

            def _kernel_resource_spec_read():
                with open((self.config_dir / "resource.txt").resolve(), "r") as f:
                    resource_spec = KernelResourceSpec.read_from_file(f)
                return resource_spec

            resource_spec = await loop.run_in_executor(None, _kernel_resource_spec_read)
            resource_opts = None
        else:
            slots = ResourceSlot.from_json(self.kernel_config["resource_slots"])
            # Ensure that we have intrinsic slots.
            assert SlotName("cpu") in slots
            assert SlotName("mem") in slots
            # accept unknown slot type with zero values
            # but reject if they have non-zero values.
            for st, sv in slots.items():
                if st not in known_slot_types and sv != Decimal(0):
                    raise UnsupportedResource(st)
            # sanitize the slots
            current_resource_slots.set(known_slot_types)
            slots = slots.normalize_slots(ignore_unknown=True)
            resource_spec = KernelResourceSpec(
                allocations={},
                slots=slots.copy(),
                mounts=[],
                scratch_disk_size=0,  # TODO: implement (#70)
            )
            resource_opts = self.kernel_config.get("resource_opts", {})
        return resource_spec, resource_opts

    @override
    async def prepare_scratch(self) -> None:
        loop = current_loop()
        ensure_kube_client_initialized()
        core_api = get_core_api()

        # Unlike Docker, static files will be mounted directly to blank folder
        # Check if NFS PVC for static files exists and bound
        nfs_pvc = await core_api.list_namespaced_persistent_volume_claim(
            self.namespace,
            label_selector="backend.ai/backend-ai-scratch-volume",
        )
        if len(nfs_pvc.items) == 0:
            raise K8sError("No PVC for backend.ai static files")
        pvc = nfs_pvc.items[0]
        if pvc.status.phase != "Bound":
            raise K8sError(f"PVC not Bound (current phase: {pvc.status.phase})")
        self.static_pvc_name = pvc.metadata.name

        def _create_scratch_dirs():
            import os

            log.debug(
                "Creating scratch directories: work_dir={}, config_dir={}, scratch_dir={}",
                self.work_dir.resolve(),
                self.config_dir.resolve(),
                self.scratch_dir.resolve(),
            )

            # Create directories
            self.work_dir.resolve().mkdir(parents=True, exist_ok=True)
            self.work_dir.chmod(0o755)
            self.config_dir.resolve().mkdir(parents=True, exist_ok=True)
            self.config_dir.chmod(0o755)

            # Create a placeholder agent.sock file in scratch directory
            # TODO: Implement proper remote agent socket mechanism for K8s
            # For now, create empty file so entrypoint.sh chown doesn't fail
            agent_sock_path = self.scratch_dir / "agent.sock"
            log.debug("Creating agent.sock at: {}", agent_sock_path)
            agent_sock_path.touch(exist_ok=True)
            agent_sock_path.chmod(0o666)  # Allow kernel to access it

            # Set ownership to kernel user (needed for non-root kernel execution)
            # The kernel_config contains the uid/gid that the kernel will run as
            uid = self.kernel_config.get("uid", 0)
            gid = self.kernel_config.get("main_gid", 0)
            log.debug("Setting ownership to uid={}, gid={}", uid, gid)
            if uid != 0:  # Only chown if running as non-root
                os.chown(self.work_dir.resolve(), uid, gid)
                os.chown(self.config_dir.resolve(), uid, gid)
                os.chown(agent_sock_path, uid, gid)
                log.debug("Ownership set successfully")
            else:
                log.warning("Skipping chown because uid is 0 (running as root)")

        # Mount scratch directory as PV
        # Config files can be mounted via ConfigMap
        await loop.run_in_executor(None, _create_scratch_dirs)

        if not self.restarting:
            # Since these files are bind-mounted inside a bind-mounted directory,
            # we need to touch them first to avoid their "ghost" files are created
            # as root in the host-side filesystem, which prevents deletion of scratch
            # directories when the agent is running as non-root.
            def _clone_dotfiles():
                jupyter_custom_css_path = Path(
                    pkg_resources.resource_filename("ai.backend.runner", "jupyter-custom.css")
                )
                logo_path = Path(pkg_resources.resource_filename("ai.backend.runner", "logo.svg"))
                font_path = Path(pkg_resources.resource_filename("ai.backend.runner", "roboto.ttf"))
                font_italic_path = Path(
                    pkg_resources.resource_filename("ai.backend.runner", "roboto-italic.ttf")
                )
                bashrc_path = Path(pkg_resources.resource_filename("ai.backend.runner", ".bashrc"))
                bash_profile_path = Path(
                    pkg_resources.resource_filename("ai.backend.runner", ".bash_profile")
                )
                zshrc_path = Path(pkg_resources.resource_filename("ai.backend.runner", ".zshrc"))
                vimrc_path = Path(pkg_resources.resource_filename("ai.backend.runner", ".vimrc"))
                tmux_conf_path = Path(
                    pkg_resources.resource_filename("ai.backend.runner", ".tmux.conf")
                )
                jupyter_custom_dir = self.work_dir / ".jupyter" / "custom"
                jupyter_custom_dir.mkdir(parents=True, exist_ok=True)
                shutil.copy(jupyter_custom_css_path.resolve(), jupyter_custom_dir / "custom.css")
                shutil.copy(logo_path.resolve(), jupyter_custom_dir / "logo.svg")
                shutil.copy(font_path.resolve(), jupyter_custom_dir / "roboto.ttf")
                shutil.copy(font_italic_path.resolve(), jupyter_custom_dir / "roboto-italic.ttf")
                shutil.copy(bashrc_path.resolve(), self.work_dir / ".bashrc")
                shutil.copy(bash_profile_path.resolve(), self.work_dir / ".bash_profile")
                shutil.copy(zshrc_path.resolve(), self.work_dir / ".zshrc")
                shutil.copy(vimrc_path.resolve(), self.work_dir / ".vimrc")
                shutil.copy(tmux_conf_path.resolve(), self.work_dir / ".tmux.conf")
                if KernelFeatures.UID_MATCH in self.kernel_features:
                    uid = self.local_config.container.kernel_uid
                    gid = self.local_config.container.kernel_gid
                    if os.geteuid() == 0:  # only possible when I am root.
                        os.chown(self.work_dir, uid, gid)
                        os.chown(self.work_dir / ".jupyter", uid, gid)
                        os.chown(self.work_dir / ".jupyter" / "custom", uid, gid)
                        os.chown(self.work_dir / ".bashrc", uid, gid)
                        os.chown(self.work_dir / ".bash_profile", uid, gid)
                        os.chown(self.work_dir / ".zshrc", uid, gid)
                        os.chown(self.work_dir / ".vimrc", uid, gid)
                        os.chown(self.work_dir / ".tmux.conf", uid, gid)

            await loop.run_in_executor(None, _clone_dotfiles)

    @override
    async def get_intrinsic_mounts(self) -> Sequence[Mount]:
        mounts: List[Mount] = [
            # Mount scratch directory
            Mount(
                MountTypes.K8S_GENERIC,
                self.rel_config_dir,
                Path("/home/config"),
                MountPermission.READ_ONLY,
                opts={
                    "name": f"kernel-{self.kernel_id}-scratches",
                },
            ),
            Mount(
                MountTypes.K8S_GENERIC,
                self.rel_work_dir,
                Path("/home/work"),
                MountPermission.READ_WRITE,
                opts={
                    "name": f"kernel-{self.kernel_id}-scratches",
                },
            ),
        ]

        # agent-socket mount - mount from kernel's scratch directory
        # In K8s, we create a placeholder agent.sock in the scratch dir
        if sys.platform != "darwin":
            rel_agent_sockpath = self.rel_scratch_dir / "agent.sock"
            mounts.append(
                Mount(
                    MountTypes.K8S_GENERIC,
                    rel_agent_sockpath,
                    Path("/opt/kernel/agent.sock"),
                    MountPermission.READ_WRITE,
                    opts={
                        "name": f"kernel-{self.kernel_id}-scratches",
                    },
                )
            )

        # Mount entire runner directory to reduce number of individual file mounts
        # Individual runner files will be accessed via this directory mount
        # NOTE: runner/ is in the global scratch root, not per-kernel scratch dir
        runner_path = self.local_config.container.scratch_root / "runner"
        mounts.append(
            Mount(
                MountTypes.K8S_HOSTPATH,
                runner_path,  # Absolute path to global runner directory
                Path("/opt/kernel-runner"),  # Mount entire runner/ directory here
                MountPermission.READ_ONLY,
                opts={
                    "name": f"kernel-{self.kernel_id}-runner",
                },
            )
        )

        # TODO: Find way to mount extra volumes

        return mounts

    @property
    @override
    def repl_ports(self) -> Sequence[int]:
        return (2000, 2001)

    @property
    @override
    def protected_services(self) -> Sequence[str]:
        # NOTE: Currently K8s does not support binding container ports to 127.0.0.1 when using NodePort.
        return ()

    @override
    async def apply_network(self, cluster_info: ClusterInfo) -> None:
        pass

    @override
    async def prepare_ssh(self, cluster_info: ClusterInfo) -> None:
        sshkey = cluster_info["ssh_keypair"]
        if sshkey is None:
            return

        ensure_kube_client_initialized()
        core_api = get_core_api()

        # Get hash of public key
        enc = hashlib.md5()
        enc.update(sshkey["public_key"].encode("ascii"))
        hash = enc.digest().decode("utf-8")

        try:
            await core_api.read_namespaced_config_map(f"ssh-keypair-{hash}", self.namespace)
        except Exception:
            # Keypair not stored on ConfigMap, create one
            cm = ConfigMap("", f"kernel-{self.kernel_id}-ssh-keypair-{hash}")
            cm.put("public", sshkey["public_key"])
            cm.put("private", sshkey["private_key"])

            self.config_maps.append(cm)

        await self.process_volumes([
            KubernetesConfigMapVolume(
                name=f"kernel-{self.kernel_id}-ssh-keypair",
                configMap={
                    "name": "ssh-keypair-hash",
                },
            ),
        ])
        await self.process_mounts([
            Mount(
                MountTypes.K8S_GENERIC,
                Path("public"),
                Path("/home/config/ssh/id_cluster.pub"),
                permission=MountPermission.READ_ONLY,
                opts={
                    "name": f"kernel-{self.kernel_id}-ssh-keypair",
                },
            ),
            Mount(
                MountTypes.K8S_GENERIC,
                Path("private"),
                Path("/home/config/ssh/id_cluster.pub"),
                permission=MountPermission.READ_ONLY,
                opts={
                    "name": f"kernel-{self.kernel_id}-ssh-keypair",
                },
            ),
        ])

    @override
    async def process_mounts(self, mounts: Sequence[Mount]):
        # Populate symlink_mappings for init container
        # Maps target path -> source path relative to /mnt/scratch
        for i, mount in zip(range(len(mounts)), mounts):
            if mount.type == MountTypes.VOLUME:
                # Handle krunner volume mount (e.g., /opt/backend.ai)
                # In K8s, skip creating symlink for krunner - it will be handled via direct mount
                # or the files are already in the image
                if mount.target.as_posix() == "/opt/backend.ai":
                    krunner_volume_name = Path(mount.source).name if mount.source else None
                    log.debug(
                        "Skipping krunner VOLUME mount (already in image or will mount subdirs): {} -> {}",
                        mount.target,
                        krunner_volume_name,
                    )
                    # Don't add to symlink_mappings - krunner is already in the base image
                else:
                    log.warning(
                        "Mount {}:{} -> VOLUME mount type only supported for /opt/backend.ai. Skipping mount",
                        mount.source,
                        mount.target,
                    )
            elif mount.type == MountTypes.K8S_GENERIC:
                name = (mount.opts or {})["name"]
                target_str = mount.target.as_posix()

                # Instead of using subPath, we'll create symlinks in init container
                if mount.source is not None:
                    source_path = Path(mount.source)
                    source_str = source_path.as_posix()

                    # Determine the relative path in /mnt/scratch
                    if "/ai/backend/runner/" in source_str:
                        # Skip individual runner files - we'll mount entire runner/ directory once
                        log.debug(
                            "Skipping individual runner file mount: {} (will use runner/ directory symlink)",
                            mount.target,
                        )
                        continue
                    else:
                        # For K8S_GENERIC mounts, mount.source is already the relative path
                        # from scratch root (e.g., "kernel_id/agent.sock")
                        # Use it directly as the scratch_subpath
                        if source_path.is_absolute():
                            # If somehow we get an absolute path, try to make it relative
                            try:
                                scratch_subpath = source_path.relative_to(
                                    self.local_config.container.scratch_root
                                ).as_posix()
                            except ValueError:
                                scratch_subpath = source_path.name
                        else:
                            # Source path is already relative - use it directly
                            scratch_subpath = source_str

                        log.debug(
                            "Scheduling symlink creation: {} -> /mnt/scratch/{}",
                            mount.target,
                            scratch_subpath,
                        )
                        self.symlink_mappings[target_str] = scratch_subpath
                else:
                    log.warning(
                        "Mount {}:{} -> K8S_GENERIC mount with no source, skipping",
                        mount.source,
                        mount.target,
                    )
            elif mount.type == MountTypes.K8S_HOSTPATH:
                if mount.source is None:
                    log.warning(
                        "Mount {}:{} -> K8S_HOSTPATH mount with no source, skipping",
                        mount.source,
                        mount.target,
                    )
                    continue
                name = (mount.opts or {})["name"]
                # Add volume mount
                self.volume_mounts.append(
                    KubernetesVolumeMount(
                        name=name,
                        mountPath=mount.target.as_posix(),
                        subPath=None,
                        readOnly=mount.permission == MountPermission.READ_ONLY,
                    ),
                )
                # Add corresponding hostPath volume
                self.volumes.append(
                    KubernetesHostPathVolume(
                        name=name,
                        hostPath={
                            "path": mount.source.as_posix(),
                            "type": "Directory",
                        },
                    )
                )
            else:
                log.warning(
                    "Mount {}:{} -> Mount type {} it not supported on K8s Agent. Skipping mount",
                    mount.source,
                    mount.target,
                    mount.type,
                )

    @override
    def resolve_krunner_filepath(self, filename: str) -> Path:
        return Path(
            pkg_resources.resource_filename(
                "ai.backend.runner",
                "../" + filename,
            )
        ).resolve()

    @override
    def get_runner_mount(
        self,
        type: MountTypes,
        src: Union[str, Path],
        target: Union[str, Path],
        perm: MountPermission = MountPermission.READ_ONLY,
        opts: Optional[Mapping[str, Any]] = None,
    ) -> Mount:
        return Mount(
            MountTypes.K8S_GENERIC,
            Path(src),
            Path(target),
            MountPermission(perm),
            opts={
                **(opts or {}),
                "name": f"kernel-{self.kernel_id}-scratches",
            },
        )

    async def process_volumes(
        self,
        volumes: List[KubernetesAbstractVolume],
    ) -> None:
        self.volumes += volumes

    @override
    async def mount_vfolders(
        self,
        vfolders: Sequence[VFolderMount],
        resource_spec: KernelResourceSpec,
    ) -> None:
        # We can't mount vFolder backed by storage proxy
        for idx, vfolder in enumerate(vfolders):
            if self.internal_data.get("prevent_vfolder_mounts", False):
                # Only allow mount of ".logs" directory to prevent expose
                # internal-only information, such as Docker credentials to user's ".docker" vfolder
                # in image importer kernels.
                if vfolder.name != ".logs":
                    continue
            mount = Mount(
                MountTypes.K8S_HOSTPATH,
                Path(vfolder.host_path),
                Path(vfolder.kernel_path),
                vfolder.mount_perm,
                opts={
                    "name": f"kernel-{self.kernel_id}-hostPath-{idx}",
                },
            )
            await self.process_volumes([
                KubernetesHostPathVolume(
                    name=f"kernel-{self.kernel_id}-hostPath-{idx}",
                    hostPath={
                        "path": vfolder.host_path.as_posix(),
                        "type": "Directory",
                    },
                ),
            ])
            resource_spec.mounts.append(mount)

    @override
    async def apply_accelerator_allocation(self, computer, device_alloc) -> None:
        """Apply accelerator allocation by delegating to the plugin."""

        # Get Kubernetes-specific resource spec from the plugin
        k8s_spec = await computer.generate_resource_spec(device_alloc)

        # Apply resource limits
        if "resources" in k8s_spec:
            self.resource_limits.update(k8s_spec["resources"].get("limits", {}))
            self.resource_requests.update(k8s_spec["resources"].get("requests", {}))

        # Apply environment variables
        if "env" in k8s_spec:
            # kernel_config["environ"] is Mapping, need to convert to MutableMapping
            env_dict = dict(self.kernel_config["environ"])
            env_dict.update(k8s_spec["env"])
            self.kernel_config["environ"] = env_dict

        # Apply volume mounts (for CUDA hooks, etc.)
        if "mounts" in k8s_spec:
            self.extra_mounts.extend(k8s_spec["mounts"])

        # Apply runtime class (e.g., "nvidia" for CUDA, "rebellions" for Rebellions NPU)
        if "runtimeClass" in k8s_spec:
            # Each node has only one device type, so only one plugin will set this
            if not self.runtime_class:
                self.runtime_class = k8s_spec["runtimeClass"]

    @override
    async def generate_accelerator_mounts(
        self,
        computer: AbstractComputePlugin,
        device_alloc: Mapping[SlotName, Mapping[DeviceId, Decimal]],
    ) -> List[MountInfo]:
        return []

    async def generate_deployment_object(
        self,
        image: str,
        environ: Mapping[str, Any],
        ports: List[int],
        command: List[str],
        labels: Mapping[str, Any] = {},
    ) -> dict:
        # Convert plugin-provided mounts to Kubernetes volume specs
        volume_mounts = []
        volumes = []

        for mount in self.extra_mounts:
            volume_mounts.append({
                "name": mount["name"],
                "mountPath": mount["mountPath"],
            })
            volumes.append({
                "name": mount["name"],
                "hostPath": {
                    "path": mount["hostPath"],
                    "type": "Directory",
                },
            })

        # Build container spec with resource limits
        container_spec: dict[str, Any] = {
            "name": f"kernel-{self.kernel_id}-session",
            "image": image,
            "imagePullPolicy": "IfNotPresent",
            # CRITICAL: Run entrypoint from /opt/kernel-runner (where it's mounted)
            # The entrypoint.sh script will create symlinks from /opt/kernel-runner/* to /opt/kernel/
            # Use explicit /bin/bash to ensure proper "$@" handling (sh may not preserve arg boundaries)
            "command": ["/bin/bash", "/opt/kernel-runner/entrypoint.sh"],
            "args": command,
            "env": [{"name": k, "value": v} for k, v in environ.items()],
            "volumeMounts": [
                *[cattr.unstructure(v) for v in self.volume_mounts],
                *volume_mounts,
            ],
            "ports": [{"containerPort": x} for x in ports],
            "securityContext": {"privileged": True},
        }

        # Add resource limits/requests if provided by plugins
        if self.resource_limits or self.resource_requests:
            container_spec["resources"] = {}
            if self.resource_limits:
                container_spec["resources"]["limits"] = self.resource_limits
            if self.resource_requests:
                container_spec["resources"]["requests"] = self.resource_requests

        log.debug("Container spec command: {}", container_spec.get("command"))
        log.debug(
            "Container spec args type: {}, content: {}",
            type(container_spec.get("args")),
            container_spec.get("args"),
        )

        # Build pod spec
        # Add scratch volume - mount entire PV at /mnt/scratch (single mount, no subPath)
        # This avoids the slow subPath bind mount overhead
        scratch_volume = {
            "name": "scratch-volume",
            "persistentVolumeClaim": {
                "claimName": self.static_pvc_name,
            },
        }
        volumes.append(scratch_volume)

        # Add scratch mount to main container
        container_spec["volumeMounts"].append({
            "name": "scratch-volume",
            "mountPath": "/mnt/scratch",
            "readOnly": False,
        })

        # Create init container to set up symlinks
        # This replaces slow subPath mounts with fast symlinks
        init_containers = []
        if self.symlink_mappings:
            # Build shell commands to create all symlinks
            # Strategy: For each symlink, create parent dir (if needed), remove target, create symlink
            # Do this one by one to avoid conflicts between nested paths
            symlink_commands = []

            for target, scratch_subpath in self.symlink_mappings.items():
                parent = str(Path(target).parent)
                # Create parent directory, remove existing target, then create symlink
                # Using ; instead of && so that rm failure doesn't stop the symlink creation
                symlink_commands.append(
                    f"mkdir -p {parent} && rm -rf {target} && ln -sf /mnt/scratch/{scratch_subpath} {target}"
                )

            init_container_spec = {
                "name": "setup-symlinks",
                "image": image,  # Use same image as main container
                "command": ["sh", "-c"],
                "args": [" && ".join(symlink_commands)],
                "volumeMounts": [
                    {
                        "name": "scratch-volume",
                        "mountPath": "/mnt/scratch",
                        "readOnly": False,
                    }
                ],
            }
            init_containers.append(init_container_spec)

        pod_spec = {
            # CRITICAL: Pin to agent's node
            "nodeName": self.node_name,
            "containers": [container_spec],
            "volumes": [
                *[cattr.unstructure(v) for v in self.volumes],
                *volumes,
            ],
            "securityContext": {"privileged": True},
        }

        # Add init containers if any
        if init_containers:
            pod_spec["initContainers"] = init_containers

        # Add runtime class if provided by plugins (e.g., "nvidia" for CUDA)
        if self.runtime_class:
            pod_spec["runtimeClassName"] = self.runtime_class

        return {
            "apiVersion": "apps/v1",
            "kind": "Deployment",
            "metadata": {
                "name": f"kernel-{self.kernel_id}",
                "labels": labels,
            },
            "spec": {
                "replicas": 0,
                "selector": {"matchLabels": {"run": f"kernel-{self.kernel_id}"}},
                "template": {
                    "metadata": {
                        "labels": {
                            "run": f"kernel-{self.kernel_id}",
                            **labels,  # Include all Backend.AI labels on the pod
                        }
                    },
                    "spec": pod_spec,
                },
            },
        }

    @override
    async def prepare_container(
        self,
        resource_spec: KernelResourceSpec,
        environ: Mapping[str, str],
        service_ports,
        cluster_info: ClusterInfo,
    ) -> KubernetesKernel:
        loop = current_loop()
        if self.restarting:
            pass
        else:
            if bootstrap := self.kernel_config.get("bootstrap_script"):

                def _write_user_bootstrap_script():
                    (self.work_dir / "bootstrap.sh").write_text(bootstrap)
                    if KernelFeatures.UID_MATCH in self.kernel_features:
                        uid = self.local_config.container.kernel_uid
                        gid = self.local_config.container.kernel_gid
                        if os.geteuid() == 0:
                            os.chown(self.work_dir / "bootstrap.sh", uid, gid)

                await loop.run_in_executor(None, _write_user_bootstrap_script)

            def _write_config(file_name: str, content: str):
                file_path = self.config_dir / file_name
                file_path.write_text(content)
                if KernelFeatures.UID_MATCH in self.kernel_features:
                    uid = self.local_config.container.kernel_uid
                    gid = self.local_config.container.kernel_gid
                    if os.geteuid() == 0:
                        os.chown(str(file_path), uid, gid)

            with StringIO() as buf:
                for k, v in environ.items():
                    buf.write(f"{k}={v}\n")
                # accel_envs = self.computer_docker_args.get('Env', [])
                # for env in accel_envs:
                #     buf.write(f'{env}\n')
                await loop.run_in_executor(
                    None,
                    functools.partial(_write_config, "environ.txt", buf.getvalue()),
                )

            with StringIO() as buf:
                resource_spec.write_to_file(buf)
                for dev_type, device_alloc in resource_spec.allocations.items():
                    computer_self = self.computers[dev_type]
                    kvpairs = await computer_self.instance.generate_resource_data(device_alloc)
                    for k, v in kvpairs.items():
                        buf.write(f"{k}={v}\n")
                await loop.run_in_executor(
                    None,
                    functools.partial(_write_config, "resource.txt", buf.getvalue()),
                )

            docker_creds = self.internal_data.get("docker_credentials")
            if docker_creds:
                await loop.run_in_executor(
                    None,
                    functools.partial(_write_config, "docker-creds.json", docker_creds),
                )

        if keypair := self.internal_data.get("ssh_keypair"):
            for mount in resource_spec.mounts:
                container_path = str(mount).split(":")[1]
                if container_path == "/home/work/.ssh":
                    break
            else:
                pubkey = keypair["public_key"].encode("ascii")
                privkey = keypair["private_key"].encode("ascii")
                ssh_config_map = ConfigMap(self.kernel_id, f"kernel-{self.kernel_id}-ssh-config")
                ssh_config_map.put("authorized_keys", pubkey)
                ssh_config_map.put("id_container", privkey)
                await self.process_volumes([
                    KubernetesConfigMapVolume(
                        name="ssh-config",
                        configMap={
                            "name": f"kernel-{self.kernel_id}-ssh-config",
                        },
                    ),
                ])
                await self.process_mounts([
                    Mount(
                        MountTypes.K8S_GENERIC,
                        Path("authorized_keys"),
                        Path("/home/work/.ssh/authorized_keys"),
                        opts={
                            "name": "ssh-config",
                        },
                    ),
                    Mount(
                        MountTypes.K8S_GENERIC,
                        Path("id_container"),
                        Path("/home/work/.ssh/id_container"),
                        opts={
                            "name": "ssh-config",
                        },
                    ),
                ])

        # higher priority dotfiles are stored last to support overwriting
        for dotfile in self.internal_data.get("dotfiles", []):
            if dotfile["path"].startswith("/"):
                if dotfile["path"].startswith("/home/"):
                    path_arr = dotfile["path"].split("/")
                    file_path: Path = self.scratch_dir / "/".join(path_arr[2:])
                else:
                    file_path = Path(dotfile["path"])
            else:
                file_path = self.work_dir / dotfile["path"]
            file_path.parent.mkdir(parents=True, exist_ok=True)
            await loop.run_in_executor(None, file_path.write_text, dotfile["data"])

            tmp = Path(file_path)
            while tmp != self.work_dir:
                tmp.chmod(int(dotfile["perm"], 8))
                if KernelFeatures.UID_MATCH in self.kernel_features and os.geteuid() == 0:
                    uid = self.local_config.container.kernel_uid
                    gid = self.local_config.container.kernel_gid
                    os.chown(tmp, uid, gid)
                tmp = tmp.parent

        # TODO: Mark shmem feature as unsupported when advertising agent

        # Convert CPU/memory from resource_spec.slots to Kubernetes resource requests/limits
        # This is essential for proper pod scheduling and QoS class assignment
        cpu_slot = resource_spec.slots.get("cpu")
        mem_slot = resource_spec.slots.get("mem")

        if cpu_slot is not None and cpu_slot > 0:
            # Backend.AI CPU is in virtual CPU units (e.g., 1 = 1 CPU)
            # Kubernetes accepts millicores (1000m = 1 CPU) or CPU units ("1")
            # Use string format like "1" for whole CPUs, "500m" for fractional
            cpu_millicores = int(cpu_slot * 1000)
            if cpu_millicores >= 1000 and cpu_millicores % 1000 == 0:
                cpu_str = str(cpu_millicores // 1000)
            else:
                cpu_str = f"{cpu_millicores}m"
            self.resource_requests["cpu"] = cpu_str
            self.resource_limits["cpu"] = cpu_str

        if mem_slot is not None and mem_slot > 0:
            # Backend.AI memory is in bytes
            # Kubernetes accepts bytes, Ki, Mi, Gi suffixes
            # Use Mi (mebibytes) for readability
            mem_bytes = int(mem_slot)
            mem_mi = mem_bytes // (1024 * 1024)
            if mem_mi > 0:
                mem_str = f"{mem_mi}Mi"
            else:
                # For very small allocations, use bytes
                mem_str = str(mem_bytes)
            self.resource_requests["memory"] = mem_str
            self.resource_limits["memory"] = mem_str

        kernel_obj = KubernetesKernel(
            self.ownership_data,
            self.kernel_config["network_id"],
            self.image_ref,
            self.kspec_version,
            agent_config=self.local_config.model_dump(by_alias=True),
            service_ports=service_ports,
            resource_spec=resource_spec,
            environ=environ,
            data={},
        )
        return kernel_obj

    @override
    async def start_container(
        self,
        kernel_obj: AbstractKernel,
        cmdargs: List[str],
        resource_opts,
        preopen_ports,
        cluster_info: ClusterInfo,
    ) -> Mapping[str, Any]:
        image_labels = self.kernel_config["image"]["labels"]
        service_ports = kernel_obj.service_ports
        environ = kernel_obj.environ

        ensure_kube_client_initialized()
        core_api = get_core_api()
        apps_api = get_apps_api()
        exposed_ports = [*self.repl_ports]
        for sport in service_ports:
            exposed_ports.extend(sport["container_ports"])

        encoded_preopen_ports = ",".join(
            f"{port_no}:preopen:{port_no}" for port_no in preopen_ports
        )

        service_port_label = image_labels.get("ai.backend.service-ports", "")
        if len(encoded_preopen_ports) > 0:
            if service_port_label:
                service_port_label += f",{encoded_preopen_ports}"
            else:
                service_port_label = encoded_preopen_ports

        log.debug("cmdargs type: {}, length: {}, content: {}", type(cmdargs), len(cmdargs), cmdargs)
        deployment = await self.generate_deployment_object(
            self.image_ref.canonical,
            environ,
            exposed_ports,
            cmdargs,
            labels={
                "ai.backend.service-ports": service_port_label.replace(":", "-").replace(",", "."),
                LabelName.AGENT_ID: str(self.agent_id),
                LabelName.KERNEL_ID: str(self.kernel_id),
                LabelName.SESSION_ID: str(self.session_id),
            },
        )

        if self.local_config.debug.log_kernel_config:
            log.debug("Initial container config: {0}", deployment)

        expose_service = Service(
            str(self.kernel_id),
            f"kernel-{self.kernel_id}-expose",
            [
                (port, f"kernel-{self.kernel_id}-svc-{index}")
                for index, port in zip(range(len(exposed_ports)), exposed_ports)
            ],
        )

        async def rollup(
            functions: List[Tuple[Optional[functools.partial], Optional[functools.partial]]],
        ):
            rollback_functions: List[Optional[functools.partial]] = []

            for rollup_function, future_rollback_function in functions:
                try:
                    if rollup_function:
                        await rollup_function()
                    rollback_functions.append(future_rollback_function)
                except Exception as e:
                    for rollback_function in rollback_functions[::-1]:
                        if rollback_function:
                            await rollback_function()
                    log.exception("Error while rollup: {}", e)
                    raise

        arguments: List[Tuple[Optional[functools.partial], Optional[functools.partial]]] = []

        try:
            expose_service_api_response: V1Service = await core_api.create_namespaced_service(
                self.namespace, body=expose_service.to_dict()
            )
        except Exception as e:
            log.exception("Error while rollup: {}", e)
            raise

        assert expose_service_api_response.spec is not None
        node_ports: List[V1ServicePort] = expose_service_api_response.spec.ports
        arguments.append((
            None,
            functools.partial(
                core_api.delete_namespaced_service, expose_service.name, self.namespace
            ),
        ))
        for cm in self.config_maps:
            arguments.append((
                functools.partial(
                    core_api.create_namespaced_config_map,
                    self.namespace,
                    body=cm.to_dict(),
                ),
                functools.partial(core_api.delete_namespaced_config_map, cm.name, self.namespace),
            ))

        arguments.append((
            functools.partial(
                apps_api.create_namespaced_deployment,
                self.namespace,
                body=deployment,
                pretty="pretty-example",
            ),
            None,
        ))

        await rollup(arguments)

        assigned_ports: MutableMapping[int, int] = {}
        for port in node_ports:
            assigned_ports[port.port] = port.node_port

        ctnr_host_port_map: MutableMapping[int, int] = {}
        stdin_port = 0
        stdout_port = 0
        for idx, port in enumerate(exposed_ports):
            host_port = assigned_ports[port]

            if port == 2000:  # intrinsic
                repl_in_port = host_port
            elif port == 2001:  # intrinsic
                repl_out_port = host_port
            elif port == 2002:  # legacy
                stdin_port = host_port
            elif port == 2003:  # legacy
                stdout_port = host_port
            else:
                ctnr_host_port_map[port] = host_port
        for sport in service_ports:
            sport["host_ports"] = tuple(
                ctnr_host_port_map[cport] for cport in sport["container_ports"]
            )

        target_node_ip = random.choice([x["InternalIP"] for x in self.workers.values()])

        return {
            "container_id": "",
            "kernel_host": target_node_ip,
            "repl_in_port": repl_in_port,
            "repl_out_port": repl_out_port,
            "stdin_port": stdin_port,  # legacy
            "stdout_port": stdout_port,  # legacy
            "assigned_ports": assigned_ports,
            # 'domain_socket_proxies': self.domain_socket_proxies,
            "block_service_ports": self.internal_data.get("block_service_ports", False),
        }


class KubernetesAgent(
    AbstractAgent[KubernetesKernel, KubernetesKernelCreationContext],
):
    workers: MutableMapping[str, MutableMapping[str, str]] = {}
    k8s_ptask_group: aiotools.PersistentTaskGroup
    agent_sockpath: Path

    def __init__(
        self,
        etcd: AgentEtcdClientView,
        local_config: AgentUnifiedConfig,
        *,
        stats_monitor: StatsPluginContext,
        error_monitor: ErrorPluginContext,
        skip_initial_scan: bool = False,
        agent_public_key: Optional[PublicKey],
        kernel_registry: KernelRegistry,
        computers: Mapping[DeviceName, ComputerContext],
        slots: Mapping[SlotName, Decimal],
    ) -> None:
        super().__init__(
            etcd,
            local_config,
            stats_monitor=stats_monitor,
            error_monitor=error_monitor,
            skip_initial_scan=skip_initial_scan,
            agent_public_key=agent_public_key,
            kernel_registry=kernel_registry,
            computers=computers,
            slots=slots,
        )

    async def __ainit__(self) -> None:
        await super().__ainit__()
        ipc_base_path = self.local_config.agent.ipc_base_path
        self.agent_sockpath = ipc_base_path / "container" / f"agent.{self.id}.sock"

        # Discover and set node name for kernel pod pinning
        self.node_name = await self._discover_node_name()

        await self.check_krunner_pv_status()
        await self.fetch_workers()
        self.k8s_ptask_group = aiotools.PersistentTaskGroup()
        # Socket Relay initialization
        # Agent socket handler initialization
        # K8s event monitor task initialization

    async def _discover_node_name(self) -> str:
        """
        Discover the Kubernetes node name where this agent pod is running.

        Returns the node name from:
        1. NODE_NAME environment variable (set via Downward API - preferred)
        2. Kubernetes API query using pod name and namespace

        Raises RuntimeError if node name cannot be determined.
        """
        # Try environment variable first (set via Downward API)
        node_name = os.environ.get("NODE_NAME")

        if node_name:
            log.info("Agent running on Kubernetes node: {}", node_name)
            return node_name

        # Fallback: Query Kubernetes API to find which node this pod is on
        log.warning("NODE_NAME not set, querying Kubernetes API...")

        ensure_kube_client_initialized()
        core_api = get_core_api()

        # Get pod name from environment or hostname
        import socket

        pod_name = os.environ.get("POD_NAME") or socket.gethostname()
        namespace = os.environ.get("POD_NAMESPACE", "backend-ai-test")

        try:
            pod = await core_api.read_namespaced_pod(pod_name, namespace)
            node_name = pod.spec.node_name
            if not node_name:
                raise ValueError("Pod has no node_name in spec")
            log.info("Discovered node name via K8s API: {}", node_name)
            return node_name
        except Exception as e:
            log.error("Failed to discover node name: {}", e)
            raise RuntimeError(
                "Cannot determine node name. Set NODE_NAME environment variable "
                "via Downward API in agent deployment YAML."
            ) from e

    async def check_krunner_pv_status(self):
        log.info("check_krunner_pv_status: Starting PV/PVC setup")
        capacity = format(self.local_config.container.scratch_size, "g")[:-1]
        log.debug("check_krunner_pv_status: capacity={}", capacity)

        ensure_kube_client_initialized()
        core_api = get_core_api()

        namespace = os.environ.get("POD_NAMESPACE", "backend-ai-test")
        log.info("check_krunner_pv_status: Using namespace={}", namespace)
        namespaces = await core_api.list_namespace()
        if len(list(filter(lambda ns: ns.metadata.name == namespace, namespaces.items))) == 0:
            await core_api.create_namespace({
                "apiVersion": "v1",
                "kind": "Namespace",
                "metadata": {
                    "name": namespace,
                },
            })

        pv = await core_api.list_persistent_volume(
            label_selector="backend.ai/backend-ai-scratch-volume"
        )
        log.info("check_krunner_pv_status: Found {} existing PVs", len(pv.items))

        if len(pv.items) == 0:
            # PV does not exists; create one
            if self.local_config.container.scratch_type == ScratchType.K8S_NFS:
                # Split NFS address into server and path
                # Format: "10.100.66.2:/export/backend-ai-scratch" -> server="10.100.66.2", path="/export/backend-ai-scratch"
                nfs_parts = self.local_config.container.scratch_nfs_address.split(":", 1)
                nfs_server = nfs_parts[0]
                nfs_path = nfs_parts[1] if len(nfs_parts) > 1 else "/"

                new_pv = NFSPersistentVolume(
                    nfs_server,
                    "backend-ai-static-pv",
                    capacity,
                    path=nfs_path,
                )
                # Sanitize NFS address for use as K8s label value (replace : and / with -)
                # Strip trailing dashes to ensure valid label (must end with alphanumeric)
                sanitized_nfs_addr = (
                    self.local_config.container.scratch_nfs_address.replace(":", "-")
                    .replace("/", "-")
                    .rstrip("-")
                )
                new_pv.label(
                    "backend.ai/backend-ai-scratch-volume",
                    sanitized_nfs_addr,
                )
                new_pv.options = [
                    x.strip() for x in self.local_config.container.scratch_nfs_options.split(",")
                ]
            elif self.local_config.container.scratch_type == ScratchType.HOSTDIR:
                new_pv = HostPathPersistentVolume(
                    self.local_config.container.scratch_root.as_posix(),
                    "backend-ai-static-pv",
                    capacity,
                )
                new_pv.label("backend.ai/backend-ai-scratch-volume", "hostPath")
            else:
                raise NotImplementedError(
                    f"Scratch type {self.local_config.container.scratch_type} is not supported",
                )

            # Add claimRef to explicitly bind PV to PVC in the correct namespace
            pv_dict = new_pv.to_dict()
            pv_dict["spec"]["claimRef"] = {
                "name": "backend-ai-static-pvc",
                "namespace": namespace,
            }

            try:
                log.info(
                    "check_krunner_pv_status: Creating PV with claimRef to {}/{}",
                    namespace,
                    "backend-ai-static-pvc",
                )
                await core_api.create_persistent_volume(body=pv_dict)
                log.info("check_krunner_pv_status: PV created successfully")
            except Exception as e:
                log.error("check_krunner_pv_status: Failed to create PV: {}", e)
                raise

        pvc = await core_api.list_namespaced_persistent_volume_claim(
            namespace,
            label_selector="backend.ai/backend-ai-scratch-volume",
        )
        log.info(
            "check_krunner_pv_status: Found {} existing PVCs in namespace {}",
            len(pvc.items),
            namespace,
        )

        if len(pvc.items) == 0:
            # PV does not exists; create one
            new_pvc = PersistentVolumeClaim(
                "backend-ai-static-pvc",
                "backend-ai-static-pv",
                capacity,
            )
            if self.local_config.container.scratch_type == ScratchType.K8S_NFS:
                # Sanitize NFS address for use as K8s label value (replace : and / with -)
                # Strip trailing dashes to ensure valid label (must end with alphanumeric)
                sanitized_nfs_addr = (
                    self.local_config.container.scratch_nfs_address.replace(":", "-")
                    .replace("/", "-")
                    .rstrip("-")
                )
                new_pvc.label(
                    "backend.ai/backend-ai-scratch-volume",
                    sanitized_nfs_addr,
                )
            else:
                new_pvc.label("backend.ai/backend-ai-scratch-volume", "hostPath")
            try:
                log.info("check_krunner_pv_status: Creating PVC in namespace {}", namespace)
                await core_api.create_namespaced_persistent_volume_claim(
                    namespace,
                    body=new_pvc.to_dict(),
                )
                log.info("check_krunner_pv_status: PVC created successfully")
            except Exception as e:
                log.error("check_krunner_pv_status: Failed to create PVC: {}", e)
                raise

        log.info("check_krunner_pv_status: PV/PVC setup completed successfully")

        # Populate volume with krunner files depending on scratch type
        if self.local_config.container.scratch_type == ScratchType.K8S_NFS:
            await self._populate_nfs_krunner_files(namespace)
        elif self.local_config.container.scratch_type == ScratchType.HOSTDIR:
            # For hostdir, directly copy runner files to the scratch directory
            # The agent pod should have direct access to the hostPath volume
            from ai.backend.agent.kubernetes.kernel import copy_runner_files

            scratch_root = Path(self.local_config.container.scratch_root).resolve()
            log.info("Copying runner files to hostdir volume at {}", scratch_root)
            await copy_runner_files(scratch_root)
            log.info("Runner files copied successfully to hostdir volume")

    async def _populate_nfs_krunner_files(self, namespace: str) -> None:
        """
        Populate the NFS PVC with krunner files by creating a temporary Pod
        that copies files from the agent's local scratch directory to the NFS volume.
        """
        log.info("Populating NFS volume with krunner files")

        # First, ensure krunner files exist in local scratch
        from ai.backend.agent.kubernetes.kernel import copy_runner_files

        scratch_root = Path(self.local_config.container.scratch_root).resolve()
        await copy_runner_files(scratch_root)

        log.debug("Scratch root resolved to: {}", scratch_root)

        # Create a one-time Job to copy files into NFS
        batch_api = get_batch_api()

        job_name = f"populate-krunner-{self.id[:8]}"

        job_spec = {
            "apiVersion": "batch/v1",
            "kind": "Job",
            "metadata": {
                "name": job_name,
                "namespace": namespace,
            },
            "spec": {
                "ttlSecondsAfterFinished": 30,  # Auto-cleanup after 30s
                "template": {
                    "spec": {
                        "restartPolicy": "Never",
                        "nodeName": self.node_name,  # Run on same node as agent
                        "containers": [
                            {
                                "name": "copier",
                                "image": "busybox:latest",
                                "command": ["sh", "-c"],
                                "args": [
                                    # Copy krunner files from host to NFS
                                    "cp -rv /agent-scratch/* /nfs-scratch/ && "
                                    "echo 'Krunner files copied successfully' && "
                                    "ls -la /nfs-scratch/"
                                ],
                                "volumeMounts": [
                                    {
                                        "name": "agent-scratch",
                                        "mountPath": "/agent-scratch",
                                        "readOnly": True,
                                    },
                                    {
                                        "name": "nfs-scratch",
                                        "mountPath": "/nfs-scratch",
                                    },
                                ],
                            }
                        ],
                        "volumes": [
                            {
                                "name": "agent-scratch",
                                "hostPath": {
                                    "path": str(scratch_root),
                                    "type": "Directory",
                                },
                            },
                            {
                                "name": "nfs-scratch",
                                "persistentVolumeClaim": {
                                    "claimName": "backend-ai-static-pvc",
                                },
                            },
                        ],
                    },
                },
            },
        }

        try:
            # Check if Job already exists and delete it
            try:
                await batch_api.delete_namespaced_job(
                    job_name,
                    namespace,
                    propagation_policy="Foreground",
                )
                log.debug("Deleted existing krunner population Job")
                # Wait a bit for deletion to complete
                import asyncio

                await asyncio.sleep(2)
            except Exception:
                pass  # Job doesn't exist, which is fine

            await batch_api.create_namespaced_job(namespace, body=job_spec)
            log.info("Created krunner population Job: {}", job_name)

            # Wait for job to complete (with timeout)
            import asyncio

            for _ in range(60):  # Wait up to 60 seconds
                await asyncio.sleep(1)
                job = await batch_api.read_namespaced_job_status(job_name, namespace)
                if job.status.succeeded:
                    log.info("Krunner files populated successfully")
                    break
                if job.status.failed:
                    log.error("Failed to populate krunner files")
                    break
            else:
                log.warning("Krunner population job timed out")

        except Exception as e:
            log.warning("Failed to populate NFS with krunner files: {}", e)
            # Don't fail agent startup, kernel creation will fail but agent should run

    async def fetch_workers(self):
        ensure_kube_client_initialized()
        core_api = get_core_api()
        nodes = await core_api.list_node()
        for node in nodes.items:
            # if 'node-role.kubernetes.io/master' in node.metadata.labels.keys():
            #     continue
            self.workers[node.metadata.name] = node.status.capacity
            for addr in node.status.addresses:
                if addr.type == "InternalIP":
                    self.workers[node.metadata.name]["InternalIP"] = addr.address
                if addr.type == "ExternalIP":
                    self.workers[node.metadata.name]["ExternalIP"] = addr.address

    async def shutdown(self, stop_signal: signal.Signals):
        # Stop agent socket handler task

        try:
            if self.k8s_ptask_group is not None:
                await self.k8s_ptask_group.shutdown()
            await super().shutdown(stop_signal)
        finally:
            # Stop k8s event monitoring and clean up API client.
            await cleanup_kube_client()

    @override
    def get_cgroup_path(self, controller: str, container_id: str) -> Path:
        # Not implemented yet for K8s Agent
        return Path()

    @override
    def get_cgroup_version(self) -> str:
        # Not implemented yet for K8s Agent
        return ""

    @override
    async def extract_image_command(self, image: str) -> str | None:
        raise NotImplementedError

    @override
    async def enumerate_containers(
        self,
        status_filter: FrozenSet[ContainerStatus] = ACTIVE_STATUS_SET,
    ) -> Sequence[Tuple[KernelId, Container]]:
        ensure_kube_client_initialized()
        core_api = get_core_api()

        namespace = os.environ.get("POD_NAMESPACE", "backend-ai-test")
        result = []
        fetch_tasks = []
        pods_list = (await core_api.list_namespaced_pod(namespace)).items
        log.debug("enumerate_containers: found {} pods in namespace {}", len(pods_list), namespace)
        for deployment in pods_list:
            # Additional check to filter out real worker pods only?

            async def _fetch_container_info(pod: Any):
                kernel_id: Union[KernelId, str, None] = "(unknown)"
                try:
                    # Use attribute access for kubernetes-asyncio objects
                    pod_name = pod.metadata.name if pod.metadata else "unknown"
                    log.debug("enumerate_containers: checking pod {}", pod_name)
                    kernel_id = await get_kernel_id_from_deployment(pod)
                    log.debug("enumerate_containers: pod {} -> kernel_id {}", pod_name, kernel_id)
                    if kernel_id is None:
                        log.debug(
                            "enumerate_containers: pod {} has no kernel_id, skipping", pod_name
                        )
                        return
                    if kernel_id not in self.kernel_registry:
                        log.debug(
                            "enumerate_containers: kernel_id {} not in registry (registry has {} kernels), skipping",
                            kernel_id,
                            len(self.kernel_registry),
                        )
                        return
                    # Is it okay to assume that only one container resides per pod?
                    # Check container status - pod.status.container_statuses[0].state has keys like 'running', 'waiting', 'terminated'
                    log.debug(
                        "enumerate_containers: pod {} phase={}, container_statuses={}",
                        pod.metadata.name,
                        pod.status.phase,
                        len(pod.status.container_statuses) if pod.status.container_statuses else 0,
                    )
                    if pod.status.container_statuses and len(pod.status.container_statuses) > 0:
                        container_state = pod.status.container_statuses[0].state
                        log.debug(
                            "enumerate_containers: pod {} container_state running={}, waiting={}, terminated={}",
                            pod.metadata.name,
                            container_state.running is not None,
                            container_state.waiting is not None,
                            container_state.terminated is not None,
                        )
                        # Convert K8s state to ContainerStatus
                        if container_state.running:
                            status = ContainerStatus.RUNNING
                        elif container_state.waiting:
                            status = ContainerStatus.RESTARTING
                        elif container_state.terminated:
                            status = ContainerStatus.EXITED
                        else:
                            status = ContainerStatus.RESTARTING

                        log.debug(
                            "enumerate_containers: pod {} status={}, status_filter={}",
                            pod.metadata.name,
                            status,
                            status_filter,
                        )
                        if status in status_filter:
                            log.debug(
                                "enumerate_containers: pod {} calling container_from_pod",
                                pod.metadata.name,
                            )
                            container = await container_from_pod(pod)
                            log.debug(
                                "enumerate_containers: pod {} got container, adding to result",
                                pod.metadata.name,
                            )
                            result.append(
                                (
                                    kernel_id,
                                    container,
                                ),
                            )
                    else:
                        log.debug(
                            "enumerate_containers: pod {} has no container_statuses, skipping",
                            pod.metadata.name,
                        )
                except asyncio.CancelledError:
                    pass
                except Exception:
                    # Use attribute access for kubernetes-asyncio objects
                    pod_uid = pod.metadata.uid if pod.metadata else "(unknown)"
                    log.exception(
                        "error while fetching container information (cid:{}, k:{})",
                        pod_uid,
                        kernel_id,
                    )

            fetch_tasks.append(_fetch_container_info(deployment))

        await asyncio.gather(*fetch_tasks, return_exceptions=True)
        return result

    @override
    async def resolve_image_distro(self, image: ImageConfig) -> str:
        image_labels = image["labels"]
        distro = image_labels.get("ai.backend.base-distro")
        if distro:
            return distro
        raise NotImplementedError

    @override
    async def scan_images(self) -> ScanImagesResult:
        # Retrieving image label from registry api is not possible
        return ScanImagesResult(scanned_images={}, removed_images={})

    @override
    async def push_image(
        self,
        image_ref: ImageRef,
        registry_conf: ImageRegistry,
        *,
        timeout: float | None | Sentinel = Sentinel.TOKEN,
    ) -> None:
        raise NotImplementedError

    async def handle_agent_socket(self):
        # TODO: Add support for remote agent socket mechanism
        pass

    @override
    async def pull_image(
        self,
        image_ref: ImageRef,
        registry_conf: ImageRegistry,
        *,
        timeout: float | None,
    ) -> None:
        # TODO: Add support for appropriate image pulling mechanism on K8s
        pass

    @override
    async def purge_images(self, request: PurgeImagesReq) -> PurgeImagesResp:
        # TODO: Add support for appropriate image purging mechanism on K8s
        return PurgeImagesResp([])

    @override
    async def check_image(
        self, image_ref: ImageRef, image_id: str, auto_pull: AutoPullBehavior
    ) -> bool:
        # TODO: Add support for appropriate image checking mechanism on K8s
        # Just mark all images as 'pulled' since we can't manually initiate image pull on each kube node
        return True

    @override
    async def init_kernel_context(
        self,
        ownership_data: KernelOwnershipData,
        kernel_image: ImageRef,
        kernel_config: KernelCreationConfig,
        *,
        restarting: bool = False,
        cluster_ssh_port_mapping: Optional[ClusterSSHPortMapping] = None,
    ) -> KubernetesKernelCreationContext:
        distro = await self.resolve_image_distro(kernel_config["image"])
        return KubernetesKernelCreationContext(
            ownership_data,
            self.event_producer,
            kernel_image,
            kernel_config,
            distro,
            self.local_config,
            self.agent_sockpath,
            self.computers,
            self.workers,
            "backend-ai-static-pvc",
            self.node_name,
            restarting=restarting,
        )

    @override
    async def destroy_kernel(
        self, kernel_id: KernelId, container_id: Optional[ContainerId]
    ) -> None:
        ensure_kube_client_initialized()
        core_api = get_core_api()
        apps_api = get_apps_api()
        namespace = os.environ.get("POD_NAMESPACE", "backend-ai-test")

        deployment_name: str | None = None

        # Try to get deployment_name from kernel registry first
        try:
            kernel = self.kernel_registry[kernel_id]
            deployment_name = kernel.get("deployment_name")
        except Exception:
            log.warning(
                "destroy_kernel(k:{}) kernel not in registry, will search by label", kernel_id
            )

        # If not in registry or no deployment_name, try to find by label
        if not deployment_name:
            try:
                # Search for deployment with the kernel-id label
                label_selector = f"ai.backend.kernel-id={kernel_id}"
                deployments = await apps_api.list_namespaced_deployment(
                    namespace, label_selector=label_selector
                )
                if deployments.items:
                    deployment_name = deployments.items[0].metadata.name
                    log.info(
                        "destroy_kernel(k:{}) found deployment by label: {}",
                        kernel_id,
                        deployment_name,
                    )
                else:
                    log.warning("destroy_kernel(k:{}) no deployment found with label", kernel_id)
                    return None
            except Exception:
                log.exception("destroy_kernel(k:{}) failed to search for deployment", kernel_id)
                return None

        if not deployment_name:
            log.warning("destroy_kernel(k:{}) deployment_name not found", kernel_id)
            return None

        # Delete the deployment and associated services
        log.info("destroy_kernel(k:{}) deleting deployment: {}", kernel_id, deployment_name)
        try:
            await core_api.delete_namespaced_service(f"{deployment_name}-service", namespace)
        except Exception:
            log.debug(
                "destroy_kernel(k:{}) service not found: {}-service", kernel_id, deployment_name
            )
        try:
            await core_api.delete_namespaced_service(f"{deployment_name}-nodeport", namespace)
        except Exception:
            log.debug(
                "destroy_kernel(k:{}) nodeport not found: {}-nodeport", kernel_id, deployment_name
            )
        try:
            await apps_api.delete_namespaced_deployment(deployment_name, namespace)
            log.info("destroy_kernel(k:{}) deployment deleted successfully", kernel_id)
        except Exception:
            log.warning("destroy_kernel(k:{}) failed to delete deployment", kernel_id)

    @override
    async def clean_kernel(
        self,
        kernel_id: KernelId,
        container_id: Optional[ContainerId],
        restarting: bool,
    ) -> None:
        loop = current_loop()
        if not restarting:
            scratch_dir = self.local_config.container.scratch_root / str(kernel_id)
            await loop.run_in_executor(None, shutil.rmtree, str(scratch_dir))

    @override
    async def create_local_network(self, network_name: str) -> None:
        raise NotImplementedError

    @override
    async def destroy_local_network(self, network_name: str) -> None:
        raise NotImplementedError

    @override
    async def restart_kernel__load_config(
        self,
        kernel_id: KernelId,
        name: str,
    ) -> bytes:
        loop = current_loop()
        scratch_dir = (self.local_config.container.scratch_root / str(kernel_id)).resolve()
        config_dir = scratch_dir / "config"
        return await loop.run_in_executor(
            None,
            (config_dir / name).read_bytes,
        )

    @override
    async def restart_kernel__store_config(
        self,
        kernel_id: KernelId,
        name: str,
        data: bytes,
    ) -> None:
        loop = current_loop()
        scratch_dir = (self.local_config.container.scratch_root / str(kernel_id)).resolve()
        config_dir = scratch_dir / "config"

        def _write_bytes(data: bytes) -> None:
            (config_dir / name).write_bytes(data)

        return await loop.run_in_executor(
            None,
            _write_bytes,
            data,
        )


async def get_kernel_id_from_deployment(pod: Any) -> Optional[KernelId]:
    """Extract kernel ID from pod metadata name.

    Pod names have format: kernel-{uuid}-{deployment-hash}-{pod-hash}
    Example: kernel-218a8c9c-fd46-41bc-99da-d7de14dc0720-74bbb6564-fmm7m

    We need to extract just the UUID portion (the part between 'kernel-' and the first deployment hash).
    The UUID format is always 8-4-4-4-12 hex digits with hyphens (36 chars total).
    """
    # Use attribute access for kubernetes-asyncio objects
    pod_name = pod.metadata.name if pod.metadata else None
    if pod_name is not None:
        # Strip 'kernel-' prefix if present
        after_prefix = pod_name.removeprefix("kernel-")

        # Extract just the UUID portion (first 36 characters, which is the UUID length)
        # UUID format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx (36 chars)
        if len(after_prefix) >= 36:
            kernel_id_str = after_prefix[:36]
        else:
            kernel_id_str = after_prefix

        try:
            return KernelId(uuid.UUID(kernel_id_str))
        except ValueError:
            log.warning(
                "Failed to parse kernel ID from pod name: {} (extracted: {})",
                pod_name,
                kernel_id_str,
            )
            return None
    return None


async def container_from_pod(pod: Any) -> Container:
    status: ContainerStatus = ContainerStatus.RUNNING
    # Use attribute access for kubernetes-asyncio objects
    phase = pod.status.phase if pod.status else "Unknown"
    if phase == "Pending" or phase == "Running":
        status = ContainerStatus.RUNNING
    elif phase == "Succeeded":
        status = ContainerStatus.EXITED
    elif phase == "Failed" or phase == "Unknown":
        status = ContainerStatus.DEAD

    # Get container info using attribute access
    containers = pod.spec.containers if pod.spec else []
    first_container = containers[0] if containers else None
    image = first_container.image if first_container else ""

    # Get ports from first container
    ports = []
    if first_container and first_container.ports:
        for port in first_container.ports:
            ports.append(
                Port(
                    port.host_ip or "",
                    port.container_port,
                    port.host_port or 0,
                )
            )

    # Use pod UID as container ID for Kubernetes
    pod_uid = pod.metadata.uid if pod.metadata and pod.metadata.uid else pod.metadata.name
    return Container(
        id=ContainerId(pod_uid),
        status=status,
        image=image,
        labels=dict(pod.metadata.labels) if pod.metadata and pod.metadata.labels else {},
        ports=ports,
        backend_obj=pod,
    )
