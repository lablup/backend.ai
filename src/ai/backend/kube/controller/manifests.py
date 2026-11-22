"""Kubernetes objects of a SessionWorkload. Pure functions: no API calls."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Final

from ai.backend.common.docker import LabelName
from ai.backend.common.service_ports import parse_service_ports
from ai.backend.kube.controller.adapters import SchedulerAdapter, adapter_for, build_adapters
from ai.backend.kube.controller.devices import (
    INTRINSIC_SLOTS,
    DeviceClaim,
    PodDeviceParts,
    pod_device_parts,
)
from ai.backend.kube.controller.kernel_files import build_kernel_files
from ai.backend.kube.controller.krunner import select_krunner
from ai.backend.kube.controller.naming import (
    ANNOTATION_KERNEL_GID,
    ANNOTATION_KERNEL_UID,
    HOSTNAME_LABEL,
    KERNEL_CONTAINER,
    KRUNNER_CONTAINER,
    LABEL_NETWORK_ID,
    LABEL_SESSION_ID,
    kernel_labels,
    kernel_pod_name,
    kernel_secret_name,
    session_labels,
    session_queue,
)
from ai.backend.kube.controller.volumes import ResolvedMount, pod_volumes, volume_mounts
from ai.backend.kube.crd.device import GPUAllocationPolicy
from ai.backend.kube.crd.scheduling import (
    PodGroup,
    PodGroupSpec,
    SokovanBindMode,
    TopologyConstraint,
)
from ai.backend.kube.crd.session import KernelSpec, ServicePortSpec, SessionWorkload
from ai.backend.kube.errors import InvalidSessionWorkloadError

REPL_PORTS: Final = (2000, 2001)
INTRINSIC_PORTS: Final = {"sshd": 2200, "ttyd": 7681, "etty": 7682}
DEFAULT_SHMEM: Final = 64 * 1024 * 1024
_ARCH_TO_K8S: Final = {"x86_64": "amd64", "aarch64": "arm64"}
_SECCOMP_DEFAULT: Final = {"type": "RuntimeDefault"}
# The container runtime's default set without NET_RAW, MKNOD, SETFCAP and SETPCAP, plus what
# the Docker agent adds (IPC_LOCK, SYS_NICE). The entrypoint starts as root and drops to
# LOCAL_USER_ID with su-exec: that takes SETUID and SETGID, not privilege escalation.
KERNEL_CAPABILITIES: Final = (
    "AUDIT_WRITE",
    "CHOWN",
    "DAC_OVERRIDE",
    "FOWNER",
    "FSETID",
    "IPC_LOCK",
    "KILL",
    "NET_BIND_SERVICE",
    "SETGID",
    "SETUID",
    "SYS_CHROOT",
    "SYS_NICE",
)
# install.sh chowns the two area roots, then places the files as the kernel user.
KRUNNER_CAPABILITIES: Final = ("CHOWN", "SETGID", "SETUID")


@dataclass(frozen=True)
class ControllerSettings:
    krunner_image: str
    system_namespace: str = "backendai-system"
    kernel_uid: int = 1000
    kernel_gid: int = 1000
    termination_grace_seconds: int = 10
    bind_mode: SokovanBindMode = SokovanBindMode.GATE
    kueue_cluster_queue: str = "backendai"
    gpu_allocation_policy: GPUAllocationPolicy = GPUAllocationPolicy.BAI
    # An admitted session not placed this long is handed back to the Manager (contract C11).
    placement_timeout_seconds: float = 600.0


@dataclass(frozen=True)
class SessionSecrets:
    """The parts of the session Secret (`spec.secretName`) the controller uses."""

    cluster_ssh_keypair: Mapping[str, str] | None
    internal_data: Mapping[str, Mapping[str, Any]]  # kernel id → internal data
    bootstrap_scripts: Mapping[str, str]  # kernel id → bootstrap script


def scheduler_adapter(workload: SessionWorkload, settings: ControllerSettings) -> SchedulerAdapter:
    return adapter_for(build_adapters(settings.bind_mode, settings.kueue_cluster_queue), workload)


def owner_reference(workload: SessionWorkload) -> dict[str, Any]:
    return {
        "apiVersion": workload.crd.api_version,
        "kind": workload.crd.kind,
        "name": workload.metadata["name"],
        "uid": workload.metadata["uid"],
        "controller": True,
        "blockOwnerDeletion": True,
    }


def _metadata(
    workload: SessionWorkload,
    name: str,
    labels: Mapping[str, str],
    annotations: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    meta: dict[str, Any] = {
        "name": name,
        "namespace": workload.metadata["namespace"],
        "labels": dict(labels),
        "ownerReferences": [owner_reference(workload)],
    }
    if annotations:
        meta["annotations"] = dict(annotations)
    return meta


def _quantity(value: str) -> str:
    amount = Decimal(value)
    if amount == amount.to_integral_value():
        return str(int(amount))
    return format(amount.normalize(), "f")


def _features(kernel: KernelSpec) -> set[str]:
    raw = kernel.image.labels.get(LabelName.FEATURES)
    return set(raw.split()) if raw is not None else {"uid-match"}


def kernel_ids(kernel: KernelSpec, settings: ControllerSettings) -> tuple[int | None, int | None]:
    """uid and gid for `LOCAL_USER_ID`, `LOCAL_GROUP_ID` (same rule as the Agent)."""
    uid_match = "uid-match" in _features(kernel)
    uid = kernel.uid if kernel.uid is not None else (settings.kernel_uid if uid_match else None)
    gid = (
        kernel.main_gid
        if kernel.main_gid is not None
        else (settings.kernel_gid if uid_match else None)
    )
    return uid, gid


def kernel_environ(kernel: KernelSpec, settings: ControllerSettings) -> dict[str, str]:
    environ = dict(kernel.environ)
    uid, gid = kernel_ids(kernel, settings)
    if uid is not None:
        environ["LOCAL_USER_ID"] = str(uid)
    if gid is not None:
        environ["LOCAL_GROUP_ID"] = str(gid)
    gids = set(kernel.supplementary_gids)
    if kernel.main_gid is not None and "uid-match" in _features(kernel):
        gids.add(settings.kernel_gid)
    if gids:
        environ["ADDITIONAL_GIDS"] = ",".join(map(str, sorted(gids)))
    if kernel.mounts:
        environ["BACKENDAI_PERSISTENT_PATHS"] = ":".join(m.kernel_path for m in kernel.mounts)
    cpu_count = str(math.ceil(Decimal(kernel.resource_slots.get("cpu", "1"))))
    if corecount_label := kernel.image.labels.get(LabelName.ENVS_CORECOUNT):
        for key in corecount_label.split(","):
            environ.setdefault(key, cpu_count)
    environ["GPU_COUNT"] = "0"
    environ["N_GPUS"] = "0"
    environ["LD_PRELOAD"] = "/opt/kernel/libbaihook.so"
    return environ


def _resources(kernel: KernelSpec, devices: PodDeviceParts) -> dict[str, Any]:
    """Device slots arrive as claims or extended resources; the translator rejects slots it
    has no profile for."""
    slots = kernel.resource_slots
    for slot in INTRINSIC_SLOTS:
        if slot not in slots:
            raise InvalidSessionWorkloadError(f"kernel {kernel.kernel_id}: {slot} slot is required")
    amounts = {
        "cpu": _quantity(slots["cpu"]),
        "memory": _quantity(slots["mem"]),
        **devices.extended_resources,
    }
    resources: dict[str, Any] = {"requests": amounts, "limits": dict(amounts)}
    if devices.container_claims:
        resources["claims"] = list(devices.container_claims)
    return resources


def kernel_service_ports(kernel: KernelSpec) -> list[ServicePortSpec]:
    """The service ports of a kernel, derived as the Agent does: intrinsic ones, the image's
    `ai.backend.service-ports` on the main kernel, the spec's own, then preopen ports."""
    ports = [
        ServicePortSpec(name="sshd", protocol="tcp", container_ports=[INTRINSIC_PORTS["sshd"]]),
        ServicePortSpec(name="ttyd", protocol="http", container_ports=[INTRINSIC_PORTS["ttyd"]]),
        ServicePortSpec(name="etty", protocol="http", container_ports=[INTRINSIC_PORTS["etty"]]),
    ]
    if kernel.cluster_role in ("main", "master"):
        for sport in parse_service_ports(
            kernel.image.labels.get(LabelName.SERVICE_PORTS, ""),
            kernel.image.labels.get(LabelName.ENDPOINT_PORTS, ""),
            exception_cls=InvalidSessionWorkloadError,
        ):
            ports.append(
                ServicePortSpec(
                    name=sport["name"],
                    protocol=str(sport["protocol"]),
                    container_ports=list(sport["container_ports"]),
                    is_inference=sport["is_inference"],
                )
            )
    known = {p.name for p in ports}
    ports += [p for p in kernel.service_ports if p.name not in known]
    ports += [
        ServicePortSpec(name=str(port), protocol="preopen", container_ports=[port])
        for port in kernel.preopen_ports
    ]
    return ports


def _container_ports(kernel: KernelSpec) -> list[dict[str, Any]]:
    numbers = set(REPL_PORTS)
    for sport in kernel_service_ports(kernel):
        numbers.update(sport.container_ports)
    # Port names must be unique, at most 15 characters, so they are not set.
    return [{"containerPort": port, "protocol": "TCP"} for port in sorted(numbers)]


def _kernel_cmdargs(workload: SessionWorkload, kernel: KernelSpec) -> list[str]:
    labels = kernel.image.labels
    roles = sorted({k.cluster_role for k in workload.spec.kernels})
    args = [
        "/opt/backend.ai/bin/python",
        "-s",
        "-m",
        "ai.backend.kernel",
        "--session-id",
        workload.spec.session_id,
    ]
    for role in roles:
        args += ["--cluster-role", role]
    args.append(labels.get(LabelName.RUNTIME_TYPE, "app"))
    if runtime_path := labels.get(LabelName.RUNTIME_PATH):
        args.append(runtime_path)
    return args


def build_kernel_pod(
    workload: SessionWorkload,
    kernel: KernelSpec,
    settings: ControllerSettings,
    mounts: Sequence[ResolvedMount] = (),
    devices: Sequence[DeviceClaim] = (),
    *,
    sudo_session: bool = False,
    compute_domain: bool = False,
) -> dict[str, Any]:
    """`sudo_session` lets the kernel user gain root through sudo, as the Agent allows;
    `compute_domain` adds the claim of the session's ComputeDomain channel."""
    if len(mounts) != len(kernel.mounts):
        raise InvalidSessionWorkloadError(f"kernel {kernel.kernel_id}: unresolved vfolder mounts")
    device_parts = pod_device_parts(workload, kernel, devices, compute_domain=compute_domain)
    scheduling = scheduler_adapter(workload, settings).pod(workload)
    distro = kernel.image.labels.get(LabelName.BASE_DISTRO, "ubuntu22.04")
    krunner = select_krunner(distro, kernel.image.architecture)
    shmem = int(kernel.resource_opts.get("shmem") or DEFAULT_SHMEM)
    env = [{"name": k, "value": v} for k, v in kernel_environ(kernel, settings).items()]
    pod_spec: dict[str, Any] = {
        "hostname": kernel.cluster_hostname,
        "subdomain": workload.metadata["name"],
        # Peers resolve by bare hostname (`sub1`), as on a Docker session network.
        "dnsConfig": {
            "searches": [
                f"{workload.metadata['name']}.{workload.metadata['namespace']}.svc.cluster.local"
            ]
        },
        "restartPolicy": "Never",
        **scheduling.spec,
        "enableServiceLinks": False,
        "automountServiceAccountToken": False,
        "securityContext": {"seccompProfile": _SECCOMP_DEFAULT},
        "terminationGracePeriodSeconds": settings.termination_grace_seconds,
        "nodeSelector": {
            "kubernetes.io/arch": _ARCH_TO_K8S.get(
                kernel.image.architecture, kernel.image.architecture
            )
        },
        "initContainers": [
            {
                "name": KRUNNER_CONTAINER,
                "image": settings.krunner_image,
                "imagePullPolicy": "IfNotPresent",
                "env": [
                    {"name": "KRUNNER_LIBC", "value": krunner.libc},
                    {"name": "KRUNNER_ARCH", "value": krunner.arch},
                    {"name": "KRUNNER_LIBBAIHOOK", "value": krunner.libbaihook},
                    {"name": "KERNEL_UID", "value": str(kernel_ids(kernel, settings)[0] or 9001)},
                    {"name": "KERNEL_GID", "value": str(kernel_ids(kernel, settings)[1] or 9001)},
                    # The kernel starts once its peers resolve: an early miss is cached.
                    {"name": "KRUNNER_WAIT_PEERS", "value": " ".join(peer_hosts(workload, kernel))},
                ],
                "volumeMounts": [
                    {"name": "krunner", "mountPath": "/krunner-dest"},
                    {"name": "kernel-files", "mountPath": "/kprep", "readOnly": True},
                    {"name": "config", "mountPath": "/kconfig"},
                    {"name": "work", "mountPath": "/kwork"},
                ],
                "resources": {
                    "requests": {"cpu": "100m", "memory": "64Mi"},
                    "limits": {"cpu": "1", "memory": "256Mi"},
                },
                "securityContext": {
                    "runAsUser": 0,
                    "allowPrivilegeEscalation": False,
                    "readOnlyRootFilesystem": True,
                    "capabilities": {"drop": ["ALL"], "add": list(KRUNNER_CAPABILITIES)},
                    "seccompProfile": _SECCOMP_DEFAULT,
                },
            }
        ],
        "containers": [
            {
                "name": KERNEL_CONTAINER,
                "image": kernel.image.canonical,
                "imagePullPolicy": kernel.image.pull_policy,
                "command": ["/opt/kernel/entrypoint.sh"],
                "args": _kernel_cmdargs(workload, kernel),
                "workingDir": "/home/work",
                "tty": True,
                "stdin": True,
                "env": env,
                "ports": _container_ports(kernel),
                "resources": _resources(kernel, device_parts),
                "securityContext": {
                    "allowPrivilegeEscalation": sudo_session,
                    "capabilities": {"drop": ["ALL"], "add": list(KERNEL_CAPABILITIES)},
                    "seccompProfile": _SECCOMP_DEFAULT,
                },
                "readinessProbe": {
                    "tcpSocket": {"port": REPL_PORTS[0]},
                    "periodSeconds": 2,
                    "failureThreshold": 3,
                },
                "volumeMounts": [
                    {
                        "name": "krunner",
                        "mountPath": "/opt/backend.ai",
                        "subPath": "backend.ai",
                        "readOnly": True,
                    },
                    {
                        "name": "krunner",
                        "mountPath": "/opt/kernel",
                        "subPath": "kernel",
                        "readOnly": True,
                    },
                    {
                        "name": "krunner",
                        "mountPath": "/usr/local/bin/all-smi",
                        "subPath": "bin/all-smi",
                        "readOnly": True,
                    },
                    {
                        "name": "krunner",
                        "mountPath": "/usr/local/bin/bssh",
                        "subPath": "bin/bssh",
                        "readOnly": True,
                    },
                    {"name": "config", "mountPath": "/home/config", "readOnly": True},
                    {"name": "work", "mountPath": "/home/work"},
                    {"name": "shm", "mountPath": "/dev/shm"},
                    *volume_mounts(mounts),
                ],
            }
        ],
        "volumes": [
            {"name": "krunner", "emptyDir": {}},
            {
                "name": "kernel-files",
                "secret": {
                    "secretName": kernel_secret_name(workload, kernel),
                    # Only the init container mounts it; it reads them as the kernel user.
                    "defaultMode": 0o444,
                },
            },
            {"name": "config", "emptyDir": {"medium": "Memory", "sizeLimit": "16Mi"}},
            {"name": "work", "emptyDir": {}},
            {"name": "shm", "emptyDir": {"medium": "Memory", "sizeLimit": str(shmem)}},
            *pod_volumes(mounts),
        ],
    }
    if kernel.image.pull_secret_name:
        pod_spec["imagePullSecrets"] = [{"name": kernel.image.pull_secret_name}]
    if device_parts.pod_claims:
        pod_spec["resourceClaims"] = device_parts.pod_claims
    return {
        "apiVersion": "v1",
        "kind": "Pod",
        "metadata": _metadata(
            workload,
            kernel_pod_name(workload, kernel),
            {**kernel_labels(workload, kernel), **scheduling.labels},
            {
                **scheduling.annotations,
                **device_parts.annotations,
                **_kernel_id_annotations(kernel, settings),
            },
        ),
        "spec": pod_spec,
    }


def _kernel_id_annotations(kernel: KernelSpec, settings: ControllerSettings) -> dict[str, str]:
    """The kernel's uid and gid, for the gateway (it never parses the user's environ)."""
    uid, gid = kernel_ids(kernel, settings)
    annotations = {}
    if uid is not None:
        annotations[ANNOTATION_KERNEL_UID] = str(uid)
    if gid is not None:
        annotations[ANNOTATION_KERNEL_GID] = str(gid)
    return annotations


def build_kernel_secret(
    workload: SessionWorkload,
    kernel: KernelSpec,
    settings: ControllerSettings,
    secrets: SessionSecrets,
) -> dict[str, Any]:
    files = build_kernel_files(
        environ=kernel_environ(kernel, settings),
        slots=kernel.resource_slots,
        mounts=[],
        session_name=workload.spec.session_name,
        internal_data=secrets.internal_data.get(kernel.kernel_id, {}),
        cluster_ssh_keypair=secrets.cluster_ssh_keypair,
        bootstrap_script=secrets.bootstrap_scripts.get(kernel.kernel_id),
    )
    return {
        "apiVersion": "v1",
        "kind": "Secret",
        "type": "Opaque",
        "metadata": _metadata(
            workload, kernel_secret_name(workload, kernel), kernel_labels(workload, kernel)
        ),
        "stringData": files.to_secret_data(),
    }


def build_session_service(workload: SessionWorkload) -> dict[str, Any]:
    """Headless Service that gives each kernel `<hostname>.<service>` DNS."""
    return {
        "apiVersion": "v1",
        "kind": "Service",
        "metadata": _metadata(workload, workload.metadata["name"], session_labels(workload)),
        "spec": {
            "clusterIP": "None",
            "publishNotReadyAddresses": True,
            "selector": {LABEL_SESSION_ID: workload.spec.session_id},
        },
    }


def build_session_network_policy(
    workload: SessionWorkload, settings: ControllerSettings
) -> dict[str, Any]:
    """Ingress only from the same session, the sessions on its persistent network, and the
    Backend.AI system namespace."""
    session_selector = {"matchLabels": {LABEL_SESSION_ID: workload.spec.session_id}}
    network_peers: list[dict[str, Any]] = []
    if workload.spec.network_id:
        # A persistent network spans projects, hence namespaces.
        network_peers.append({
            "from": [
                {
                    "namespaceSelector": {},
                    "podSelector": {"matchLabels": {LABEL_NETWORK_ID: workload.spec.network_id}},
                }
            ]
        })
    return {
        "apiVersion": "networking.k8s.io/v1",
        "kind": "NetworkPolicy",
        "metadata": _metadata(workload, workload.metadata["name"], session_labels(workload)),
        "spec": {
            "podSelector": session_selector,
            "policyTypes": ["Ingress"],
            "ingress": [
                {"from": [{"podSelector": session_selector}]},
                *network_peers,
                {
                    "from": [
                        {
                            "namespaceSelector": {
                                "matchLabels": {
                                    "kubernetes.io/metadata.name": settings.system_namespace
                                }
                            }
                        }
                    ]
                },
            ],
        },
    }


def build_pod_group(workload: SessionWorkload) -> dict[str, Any]:
    spec = workload.spec
    group = PodGroup(
        metadata=_metadata(workload, workload.metadata["name"], session_labels(workload)),
        spec=PodGroupSpec(
            min_member=len(spec.kernels),
            queue=session_queue(workload),
            priority=spec.priority,
            session_id=spec.session_id,
            topology=_topology(workload),
        ),
    )
    return group.to_manifest()


def _topology(workload: SessionWorkload) -> TopologyConstraint | None:
    """A single-node session keeps all its kernels on one node, as on one Agent."""
    if workload.spec.cluster_mode == "single-node" and len(workload.spec.kernels) > 1:
        return TopologyConstraint(required_levels=[HOSTNAME_LABEL])
    return None


def peer_hosts(workload: SessionWorkload, kernel: KernelSpec) -> list[str]:
    """FQDNs of the other kernels of the session, through its headless Service."""
    domain = f"{workload.metadata['name']}.{workload.metadata['namespace']}.svc.cluster.local"
    return [
        f"{k.cluster_hostname}.{domain}"
        for k in workload.spec.kernels
        if k.kernel_id != kernel.kernel_id
    ]
