"""Build the SessionWorkload and its Secret from what the launcher would send an Agent."""

from __future__ import annotations

import base64
import json
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Final
from uuid import UUID

from ai.backend.common.kernel_creation_config import KernelCreationConfig
from ai.backend.common.types import ClusterInfo, SessionId
from ai.backend.kube.crd.session import (
    KernelImage,
    KernelSpec,
    MountPermission,
    SessionWorkload,
    SessionWorkloadSpec,
    VFolderVolumeMount,
)

SCHEDULER_NAME: Final = "sokovan"
LABEL_MANAGED_BY: Final = "app.kubernetes.io/managed-by"
MANAGED_BY: Final = "backendai-manager"
LABEL_SESSION_ID: Final = "backend.ai/session-id"


@dataclass(frozen=True)
class SessionPlacement:
    """Where and as whom the session runs in the cluster."""

    namespace: str
    session_id: SessionId
    session_name: str
    session_type: str
    owner_user_id: str
    owner_project_id: str
    access_key: str
    domain_name: str | None
    resource_group: str
    queue: str
    priority: int
    network_id: str | None
    scheduler_name: str = SCHEDULER_NAME


@dataclass(frozen=True)
class SessionObjects:
    workload: dict[str, Any]
    secret: dict[str, Any]
    pull_secret: dict[str, Any] | None


def queue_name(resource_group: str, project_id: UUID | None = None) -> str:
    """A resource group's queue, or a project's queue under it, as a Kubernetes object name."""
    base = re.sub(r"[^a-z0-9-]+", "-", resource_group.lower()).strip("-") or "rg"
    return base if project_id is None else f"{base}.{project_id}"


def workload_name(session_id: SessionId) -> str:
    return f"s-{session_id}"


def _pull_secret_name(session_id: SessionId) -> str:
    return f"{workload_name(session_id)}-registry"


def _kernel_spec(config: KernelCreationConfig, pull_secret: str | None) -> KernelSpec:
    image = config["image"]
    return KernelSpec(
        kernel_id=config["kernel_id"],
        cluster_role=config["cluster_role"],
        cluster_idx=config["cluster_idx"],
        cluster_hostname=config["cluster_hostname"],
        local_rank=config["local_rank"],
        image=KernelImage(
            canonical=image["canonical"],
            architecture=image["architecture"],
            digest=image.get("digest") or None,
            pull_secret_name=pull_secret,
            labels=dict(image["labels"]),
        ),
        resource_slots={k: str(v) for k, v in config["resource_slots"].items()},
        mounts=[_vfolder_mount(m) for m in config["mounts"]],
        resource_opts=dict(config["resource_opts"]),
        environ=dict(config["environ"]),
        preopen_ports=list(config["preopen_ports"]),
        uid=config["uid"],
        main_gid=config["main_gid"],
        supplementary_gids=list(config["supplementary_gids"]),
        startup_command=config["startup_command"],
    )


def _vfolder_mount(raw: Mapping[str, Any]) -> VFolderVolumeMount:
    """A serialized `VFolderMount`; its host path is where the storage-proxy mounts it."""
    return VFolderVolumeMount(
        name=raw["name"],
        vfid=str(raw["vfid"]),
        host_path=str(raw["host_path"]),
        kernel_path=str(raw["kernel_path"]),
        mount_perm=MountPermission(str(raw["mount_perm"])),
        usage_mode=str(raw["usage_mode"]),
    )


def _registry_auth(configs: Sequence[KernelCreationConfig]) -> dict[str, Any] | None:
    """A docker config for the registries that need credentials, if any does."""
    auths: dict[str, dict[str, str]] = {}
    for config in configs:
        registry = config["image"]["registry"]
        username = registry.get("username")
        if not username:
            continue
        host = str(registry["url"]).split("://", 1)[-1].rstrip("/")
        token = base64.b64encode(f"{username}:{registry.get('password') or ''}".encode()).decode()
        auths[host] = {"auth": token}
    return {"auths": auths} if auths else None


def build_session_objects(
    placement: SessionPlacement,
    configs: Sequence[KernelCreationConfig],
    cluster_info: ClusterInfo,
) -> SessionObjects:
    name = workload_name(placement.session_id)
    labels = {LABEL_MANAGED_BY: MANAGED_BY, LABEL_SESSION_ID: str(placement.session_id)}
    auth = _registry_auth(configs)
    pull_secret_name = _pull_secret_name(placement.session_id) if auth else None
    kernels = [_kernel_spec(config, pull_secret_name) for config in configs]
    workload = SessionWorkload(
        metadata={"name": name, "namespace": placement.namespace, "labels": labels},
        spec=SessionWorkloadSpec(
            session_id=str(placement.session_id),
            session_name=placement.session_name,
            session_type=placement.session_type,
            owner_user_id=placement.owner_user_id,
            owner_project_id=placement.owner_project_id,
            access_key=placement.access_key,
            domain_name=placement.domain_name,
            resource_group=placement.resource_group,
            queue=placement.queue,
            priority=placement.priority,
            cluster_mode=str(cluster_info["mode"]),
            cluster_size=len(kernels),
            network_id=placement.network_id,
            idle_timeout=configs[0]["idle_timeout"] if configs else 0,
            scheduler_name=placement.scheduler_name,
            secret_name=f"{name}-secret",
            kernels=kernels,
        ),
    )
    secret_data: dict[str, str] = {}
    if keypair := cluster_info.get("ssh_keypair"):
        secret_data["cluster-ssh-keypair"] = json.dumps(dict(keypair))
    for config in configs:
        secret_data[f"kernel-{config['kernel_id']}"] = json.dumps({
            "internal_data": _jsonable(config["internal_data"] or {}),
            "bootstrap_script": config["bootstrap_script"],
        })
    secret = {
        "apiVersion": "v1",
        "kind": "Secret",
        "type": "Opaque",
        "metadata": {"name": f"{name}-secret", "namespace": placement.namespace, "labels": labels},
        "stringData": secret_data,
    }
    pull_secret = None
    if auth is not None and pull_secret_name is not None:
        pull_secret = {
            "apiVersion": "v1",
            "kind": "Secret",
            "type": "kubernetes.io/dockerconfigjson",
            "metadata": {
                "name": pull_secret_name,
                "namespace": placement.namespace,
                "labels": labels,
            },
            "stringData": {".dockerconfigjson": json.dumps(auth)},
        }
    return SessionObjects(workload.to_manifest(), secret, pull_secret)


def _jsonable(value: Mapping[str, Any]) -> Mapping[str, Any]:
    """internal_data holds plain JSON values; round-trip to drop anything that is not."""
    loaded: Mapping[str, Any] = json.loads(json.dumps(value, default=str))
    return loaded
