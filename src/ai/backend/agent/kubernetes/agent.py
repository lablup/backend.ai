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
    Literal,
    Mapping,
    MutableMapping,
    Optional,
    Sequence,
    Tuple,
    Union,
)

import aiotools
import cattr
import pkg_resources
from kubernetes_asyncio import client as kube_client
from kubernetes_asyncio import config as kube_config

from ai.backend.common.asyncio import current_loop
from ai.backend.common.docker import ImageRef
from ai.backend.common.etcd import AsyncEtcd
from ai.backend.common.events import EventProducer
from ai.backend.common.logging import BraceStyleAdapter
from ai.backend.common.plugin.monitor import ErrorPluginContext, StatsPluginContext
from ai.backend.common.types import (
    AgentId,
    AutoPullBehavior,
    ClusterInfo,
    ClusterSSHPortMapping,
    ContainerId,
    DeviceId,
    DeviceName,
    ImageConfig,
    ImageRegistry,
    KernelCreationConfig,
    KernelId,
    MountPermission,
    MountTypes,
    ResourceSlot,
    SessionId,
    SlotName,
    VFolderMount,
    current_resource_slots,
)

from ..agent import ACTIVE_STATUS_SET, AbstractAgent, AbstractKernelCreationContext, ComputerContext
from ..exception import K8sError, UnsupportedResource
from ..kernel import AbstractKernel, KernelFeatures
from ..resources import AbstractComputePlugin, KernelResourceSpec, Mount, known_slot_types
from ..types import Container, ContainerStatus, MountInfo, Port
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
from .resources import load_resources, scan_available_resources

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
        kernel_id: KernelId,
        session_id: SessionId,
        agent_id: AgentId,
        event_producer: EventProducer,
        kernel_config: KernelCreationConfig,
        distro: str,
        local_config: Mapping[str, Any],
        agent_sockpath: Path,
        computers: MutableMapping[DeviceName, ComputerContext],
        workers: Mapping[str, Mapping[str, str]],
        static_pvc_name: str,
        restarting: bool = False,
    ) -> None:
        super().__init__(
            kernel_id,
            session_id,
            agent_id,
            event_producer,
            kernel_config,
            distro,
            local_config,
            computers,
            restarting=restarting,
        )
        scratch_dir = (self.local_config["container"]["scratch-root"] / str(kernel_id)).resolve()
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

    async def get_extra_envs(self) -> Mapping[str, str]:
        return {}

    async def prepare_resource_spec(self) -> Tuple[KernelResourceSpec, Optional[Mapping[str, Any]]]:
        loop = current_loop()
        if self.restarting:
            await kube_config.load_kube_config()

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
                container_id="",
                allocations={},
                slots={**slots},  # copy
                mounts=[],
                scratch_disk_size=0,  # TODO: implement (#70)
            )
            resource_opts = self.kernel_config.get("resource_opts", {})
        return resource_spec, resource_opts

    async def prepare_scratch(self) -> None:
        loop = current_loop()
        await kube_config.load_kube_config()
        core_api = kube_client.CoreV1Api()

        # Unlike Docker, static files will be mounted directly to blank folder
        # Check if NFS PVC for static files exists and bound
        nfs_pvc = await core_api.list_persistent_volume_claim_for_all_namespaces(
            label_selector="backend.ai/backend-ai-scratch-volume",
        )
        if len(nfs_pvc.items) == 0:
            raise K8sError("No PVC for backend.ai static files")
        pvc = nfs_pvc.items[0]
        if pvc.status.phase != "Bound":
            raise K8sError("PVC not Bound")
        self.static_pvc_name = pvc.metadata.name

        def _create_scratch_dirs():
            self.work_dir.resolve().mkdir(parents=True, exist_ok=True)
            self.work_dir.chmod(0o755)
            self.config_dir.resolve().mkdir(parents=True, exist_ok=True)
            self.config_dir.chmod(0o755)

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
                    uid = self.local_config["container"]["kernel-uid"]
                    gid = self.local_config["container"]["kernel-gid"]
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

        rel_agent_sockpath = Path(str(self.agent_sockpath).split("/")[-1])
        # agent-socket mount
        if sys.platform != "darwin":
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

        # TODO: Find way to mount extra volumes

        return mounts

    async def apply_network(self, cluster_info: ClusterInfo) -> None:
        pass

    async def prepare_ssh(self, cluster_info: ClusterInfo) -> None:
        sshkey = cluster_info["ssh_keypair"]
        if sshkey is None:
            return

        await kube_config.load_kube_config()
        core_api = kube_client.CoreV1Api()

        # Get hash of public key
        enc = hashlib.md5()
        enc.update(sshkey["public_key"].encode("ascii"))
        hash = enc.digest().decode("utf-8")

        try:
            await core_api.read_namespaced_config_map(f"ssh-keypair-{hash}", "backend-ai")
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

    async def process_mounts(self, mounts: Sequence[Mount]):
        for i, mount in zip(range(len(mounts)), mounts):
            if mount.type == MountTypes.K8S_GENERIC:
                name = (mount.opts or {})["name"]
                self.volume_mounts.append(
                    KubernetesVolumeMount(
                        name=name,
                        mountPath=mount.target.as_posix(),
                        subPath=mount.source.as_posix() if mount.source is not None else None,
                        readOnly=mount.permission == MountPermission.READ_ONLY,
                    ),
                )
            elif mount.type == MountTypes.K8S_HOSTPATH:
                name = (mount.opts or {})["name"]
                self.volume_mounts.append(
                    KubernetesVolumeMount(
                        name=name,
                        mountPath=mount.target.as_posix(),
                        subPath=None,
                        readOnly=mount.permission == MountPermission.READ_ONLY,
                    ),
                )
            else:
                log.warning(
                    "Mount {}:{} -> Mount type {} it not supported on K8s Agent. Skipping mount",
                    mount.source,
                    mount.target,
                    mount.type,
                )

    def resolve_krunner_filepath(self, filename: str) -> Path:
        return Path(filename)

    def get_runner_mount(
        self,
        type: MountTypes,
        src: Union[str, Path],
        target: Union[str, Path],
        perm: Literal["ro", "rw"] = "ro",
        opts: Mapping[str, Any] = None,
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

    async def apply_accelerator_allocation(self, computer, device_alloc) -> None:
        # update_nested_dict(
        #     self.computer_docker_args,
        #     await computer.generate_docker_args(self.docker, device_alloc))
        # TODO: add support for accelerator allocation
        pass

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
                    "metadata": {"labels": {"run": f"kernel-{self.kernel_id}"}},
                    "spec": {
                        "containers": [
                            {
                                "name": f"kernel-{self.kernel_id}-session",
                                "image": image,
                                "imagePullPolicy": "IfNotPresent",
                                "command": ["sh", "/opt/kernel/entrypoint.sh"],
                                "args": command,
                                "env": [{"name": k, "value": v} for k, v in environ.items()],
                                "volumeMounts": [cattr.unstructure(v) for v in self.volume_mounts],
                                "ports": [{"containerPort": x} for x in ports],
                                "securityContext": {"privileged": True},
                            }
                        ],
                        "volumes": [cattr.unstructure(v) for v in self.volumes],
                        "securityContext": {"privileged": True},
                    },
                },
            },
        }

    async def spawn(
        self,
        resource_spec: KernelResourceSpec,
        environ: Mapping[str, str],
        service_ports,
    ) -> KubernetesKernel:
        loop = current_loop()
        if self.restarting:
            pass
        else:
            if bootstrap := self.kernel_config.get("bootstrap_script"):

                def _write_user_bootstrap_script():
                    (self.work_dir / "bootstrap.sh").write_text(bootstrap)
                    if KernelFeatures.UID_MATCH in self.kernel_features:
                        uid = self.local_config["container"]["kernel-uid"]
                        gid = self.local_config["container"]["kernel-gid"]
                        if os.geteuid() == 0:
                            os.chown(self.work_dir / "bootstrap.sh", uid, gid)

                await loop.run_in_executor(None, _write_user_bootstrap_script)

            def _write_config(file_name: str, content: str):
                file_path = self.config_dir / file_name
                file_path.write_text(content)
                if KernelFeatures.UID_MATCH in self.kernel_features:
                    uid = self.local_config["container"]["kernel-uid"]
                    gid = self.local_config["container"]["kernel-gid"]
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
                    uid = self.local_config["container"]["kernel-uid"]
                    gid = self.local_config["container"]["kernel-gid"]
                    os.chown(tmp, uid, gid)
                tmp = tmp.parent

        # TODO: Mark shmem feature as unsupported when advertising agent

        kernel_obj = KubernetesKernel(
            self.kernel_id,
            self.session_id,
            self.agent_id,
            self.image_ref,
            self.kspec_version,
            agent_config=self.local_config,
            service_ports=service_ports,
            resource_spec=resource_spec,
            environ=environ,
            data={},
        )
        return kernel_obj

    async def start_container(
        self,
        kernel_obj: AbstractKernel,
        cmdargs: List[str],
        resource_opts,
        preopen_ports,
    ) -> Mapping[str, Any]:
        image_labels = self.kernel_config["image"]["labels"]
        service_ports = kernel_obj.service_ports
        environ = kernel_obj.environ

        await kube_config.load_kube_config()
        core_api = kube_client.CoreV1Api()
        apps_api = kube_client.AppsV1Api()
        exposed_ports = [2000, 2001]
        for sport in service_ports:
            exposed_ports.extend(sport["container_ports"])

        encoded_preopen_ports = ",".join(
            f"{port_no}:preopen:{port_no}" for port_no in preopen_ports
        )

        service_port_label = image_labels["ai.backend.service-ports"]
        if len(encoded_preopen_ports) > 0:
            service_port_label += f",{encoded_preopen_ports}"

        deployment = await self.generate_deployment_object(
            self.image_ref.canonical,
            environ,
            exposed_ports,
            cmdargs,
            labels={
                "ai.backend.service-ports": service_port_label.replace(":", "-").replace(",", "."),
            },
        )

        if self.local_config["debug"]["log-kernel-config"]:
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
        node_ports = []

        try:
            expose_service_api_response = await core_api.create_namespaced_service(
                "backend-ai", body=expose_service.to_dict()
            )
        except Exception as e:
            log.exception("Error while rollup: {}", e)
            raise

        node_ports = expose_service_api_response.spec.ports
        arguments.append((
            None,
            functools.partial(
                core_api.delete_namespaced_service, expose_service.name, "backend-ai"
            ),
        ))
        for cm in self.config_maps:
            arguments.append((
                functools.partial(
                    core_api.create_namespaced_config_map,
                    "backend-ai",
                    body=cm.to_dict(),
                ),
                functools.partial(core_api.delete_namespaced_config_map, cm.name, "backend-ai"),
            ))

        arguments.append((
            functools.partial(
                apps_api.create_namespaced_deployment,
                "backend-ai",
                body=deployment,
                pretty="pretty-example",
            ),
            None,
        ))

        await rollup(arguments)

        assigned_ports: MutableMapping[str, int] = {}
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
        etcd: AsyncEtcd,
        local_config: Mapping[str, Any],
        *,
        stats_monitor: StatsPluginContext,
        error_monitor: ErrorPluginContext,
        skip_initial_scan: bool = False,
        agent_public_key: Optional[PublicKey],
    ) -> None:
        super().__init__(
            etcd,
            local_config,
            stats_monitor=stats_monitor,
            error_monitor=error_monitor,
            skip_initial_scan=skip_initial_scan,
            agent_public_key=agent_public_key,
        )

    async def __ainit__(self) -> None:
        await super().__ainit__()
        ipc_base_path = self.local_config["agent"]["ipc-base-path"]
        self.agent_sockpath = ipc_base_path / "container" / f"agent.{self.local_instance_id}.sock"

        await self.check_krunner_pv_status()
        await self.fetch_workers()
        self.k8s_ptask_group = aiotools.PersistentTaskGroup()
        # Socket Relay initialization
        # Agent socket handler initialization
        # K8s event monitor task initialization

    async def check_krunner_pv_status(self):
        capacity = format(self.local_config["container"]["scratch-size"], "g")[:-1]

        await kube_config.load_kube_config()
        core_api = kube_client.CoreV1Api()

        namespaces = await core_api.list_namespace()
        if len(list(filter(lambda ns: ns.metadata.name == "backend-ai", namespaces.items))) == 0:
            await core_api.create_namespace({
                "apiVersion": "v1",
                "kind": "Namespace",
                "metadata": {
                    "name": "backend-ai",
                },
            })

        pv = await core_api.list_persistent_volume(
            label_selector="backend.ai/backend-ai-scratch-volume"
        )

        if len(pv.items) == 0:
            # PV does not exists; create one
            if self.local_config["container"]["scratch-type"] == "k8s-nfs":
                new_pv = NFSPersistentVolume(
                    self.local_config["container"]["scratch-nfs-address"],
                    "backend-ai-static-pv",
                    capacity,
                )
                new_pv.label(
                    "backend.ai/backend-ai-scratch-volume",
                    self.local_config["container"]["scratch-nfs-address"],
                )
                new_pv.options = [
                    x.strip()
                    for x in self.local_config["container"]["scratch-nfs-options"].split(",")
                ]
            elif self.local_config["container"]["scratch-type"] == "hostdir":
                new_pv = HostPathPersistentVolume(
                    self.local_config["container"]["scratch-root"].as_posix(),
                    "backend-ai-static-pv",
                    capacity,
                )
                new_pv.label("backend.ai/backend-ai-scratch-volume", "hostPath")
            else:
                raise NotImplementedError(
                    f'Scratch type {self.local_config["container"]["scratch-type"]} is not'
                    " supported",
                )

            try:
                await core_api.create_persistent_volume(body=new_pv.to_dict())
            except Exception:
                raise

        pvc = await core_api.list_persistent_volume_claim_for_all_namespaces(
            label_selector="backend.ai/backend-ai-scratch-volume",
        )

        if len(pvc.items) == 0:
            # PV does not exists; create one
            new_pvc = PersistentVolumeClaim(
                "backend-ai-static-pvc",
                "backend-ai-static-pv",
                capacity,
            )
            if self.local_config["container"]["scratch-type"] == "k8s-nfs":
                new_pvc.label(
                    "backend.ai/backend-ai-scratch-volume",
                    self.local_config["container"]["scratch-nfs-address"],
                )
            else:
                new_pvc.label("backend.ai/backend-ai-scratch-volume", "hostPath")
            try:
                await core_api.create_namespaced_persistent_volume_claim(
                    "backend-ai",
                    body=new_pvc.to_dict(),
                )
            except Exception as e:
                log.exception("Error: {}", e)
                raise

    async def fetch_workers(self):
        await kube_config.load_kube_config()
        core_api = kube_client.CoreV1Api()
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
            # Stop k8s event monitoring.
            pass

    async def load_resources(self) -> Mapping[DeviceName, AbstractComputePlugin]:
        return await load_resources(self.etcd, self.local_config)

    async def scan_available_resources(self) -> Mapping[SlotName, Decimal]:
        return await scan_available_resources(
            self.local_config, {name: cctx.instance for name, cctx in self.computers.items()}
        )

    async def extract_command(self, image_ref: str) -> str | None:
        return None

    async def enumerate_containers(
        self,
        status_filter: FrozenSet[ContainerStatus] = ACTIVE_STATUS_SET,
    ) -> Sequence[Tuple[KernelId, Container]]:
        await kube_config.load_kube_config()
        core_api = kube_client.CoreV1Api()

        result = []
        fetch_tasks = []
        for deployment in (await core_api.list_namespaced_pod("backend-ai")).items:
            # Additional check to filter out real worker pods only?

            async def _fetch_container_info(pod: Any):
                kernel_id: Union[KernelId, str, None] = "(unknown)"
                try:
                    kernel_id = await get_kernel_id_from_deployment(pod)
                    if kernel_id is None or kernel_id not in self.kernel_registry:
                        return
                    # Is it okay to assume that only one container resides per pod?
                    if pod["status"]["containerStatuses"][0]["stats"].keys()[0] in status_filter:
                        result.append(
                            (
                                kernel_id,
                                await container_from_pod(pod),
                            ),
                        )
                except asyncio.CancelledError:
                    pass
                except Exception:
                    log.exception(
                        "error while fetching container information (cid:{}, k:{})",
                        pod["metadata"]["uid"],
                        kernel_id,
                    )

            fetch_tasks.append(_fetch_container_info(deployment))

        await asyncio.gather(*fetch_tasks, return_exceptions=True)
        return result

    async def resolve_image_distro(self, image: ImageConfig) -> str:
        image_labels = image["labels"]
        distro = image_labels.get("ai.backend.base-distro")
        if distro:
            return distro
        raise NotImplementedError

    async def scan_images(self) -> Mapping[str, str]:
        # Retrieving image label from registry api is not possible
        return {}

    async def handle_agent_socket(self):
        # TODO: Add support for remote agent socket mechanism
        pass

    async def pull_image(self, image_ref: ImageRef, registry_conf: ImageRegistry) -> None:
        # TODO: Add support for appropriate image pulling mechanism on K8s
        pass

    async def check_image(
        self, image_ref: ImageRef, image_id: str, auto_pull: AutoPullBehavior
    ) -> bool:
        # TODO: Add support for appropriate image checking mechanism on K8s
        # Just mark all images as 'pulled' since we can't manually initiate image pull on each kube node
        return True

    async def init_kernel_context(
        self,
        kernel_id: KernelId,
        session_id: SessionId,
        kernel_config: KernelCreationConfig,
        *,
        restarting: bool = False,
        cluster_ssh_port_mapping: Optional[ClusterSSHPortMapping] = None,
    ) -> KubernetesKernelCreationContext:
        distro = await self.resolve_image_distro(kernel_config["image"])
        return KubernetesKernelCreationContext(
            kernel_id,
            session_id,
            self.id,
            self.event_producer,
            kernel_config,
            distro,
            self.local_config,
            self.agent_sockpath,
            self.computers,
            self.workers,
            "backend-ai-static-pvc",
            restarting=restarting,
        )

    async def destroy_kernel(
        self, kernel_id: KernelId, container_id: Optional[ContainerId]
    ) -> None:
        await kube_config.load_kube_config()
        core_api = kube_client.CoreV1Api()
        apps_api = kube_client.AppsV1Api()

        async def force_cleanup(reason="self-terminated"):
            await self.send_event("kernel_terminated", kernel_id, "self-terminated", None)

        try:
            kernel = self.kernel_registry[kernel_id]
        except Exception:
            log.warning("_destroy_kernel({0}) kernel missing (already dead?)", kernel_id)
            await asyncio.shield(self.k8s_ptask_group.create_task(force_cleanup()))
            return None
        deployment_name = kernel["deployment_name"]
        try:
            await core_api.delete_namespaced_service(f"{deployment_name}-service", "backend-ai")
            await core_api.delete_namespaced_service(f"{deployment_name}-nodeport", "backend-ai")
            await apps_api.delete_namespaced_deployment(f"{deployment_name}", "backend-ai")
        except Exception:
            log.warning("_destroy({0}) kernel missing (already dead?)", kernel_id)

    async def clean_kernel(
        self,
        kernel_id: KernelId,
        container_id: Optional[ContainerId],
        restarting: bool,
    ) -> None:
        loop = current_loop()
        if not restarting:
            scratch_dir = self.local_config["container"]["scratch-root"] / str(kernel_id)
            await loop.run_in_executor(None, shutil.rmtree, str(scratch_dir))

    async def create_local_network(self, network_name: str) -> None:
        raise NotImplementedError

    async def destroy_local_network(self, network_name: str) -> None:
        raise NotImplementedError

    async def restart_kernel__load_config(
        self,
        kernel_id: KernelId,
        name: str,
    ) -> bytes:
        loop = current_loop()
        scratch_dir = (self.local_config["container"]["scratch-root"] / str(kernel_id)).resolve()
        config_dir = scratch_dir / "config"
        return await loop.run_in_executor(
            None,
            (config_dir / name).read_bytes,
        )

    async def restart_kernel__store_config(
        self,
        kernel_id: KernelId,
        name: str,
        data: bytes,
    ) -> None:
        loop = current_loop()
        scratch_dir = (self.local_config["container"]["scratch-root"] / str(kernel_id)).resolve()
        config_dir = scratch_dir / "config"
        return await loop.run_in_executor(
            None,
            (config_dir / name).write_bytes,
            data,
        )


async def get_kernel_id_from_deployment(pod: Any) -> Optional[KernelId]:
    # TODO: create function which extracts kernel id from pod object
    if (kernel_id := pod.get("metadata", {}).get("name")) is not None:
        return KernelId(uuid.UUID(kernel_id))
    return None


async def container_from_pod(pod: Any) -> Container:
    status: ContainerStatus = ContainerStatus.RUNNING
    phase = pod["status"]["phase"]
    if phase == "Pending" or phase == "Running":
        status = ContainerStatus.RUNNING
    elif phase == "Succeeded":
        status = ContainerStatus.EXITED
    elif phase == "Failed" or phase == "Unknown":
        status = ContainerStatus.DEAD

    # TODO: Create Container object from K8s Pod definition
    return Container(
        id=ContainerId(""),
        status=status,
        image=pod["spec"]["containers"][0]["image"],
        labels=pod["metadata"]["labels"],
        ports=[
            Port(
                port["host_ip"],
                port["container_port"],
                port["host_port"],
            )
            for port in pod["spec"]["containers"][0]["ports"]
        ],
        backend_obj=pod,
    )
