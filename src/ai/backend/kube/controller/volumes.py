"""Mount vfolders through StorageBindings: one PV and PVC per binding and namespace, a subPath
per vfolder (suggestion-1122 7.4)."""

from __future__ import annotations

import posixpath
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from ai.backend.kube.crd.session import MountPermission, VFolderVolumeMount
from ai.backend.kube.crd.storage import StorageBinding
from ai.backend.kube.errors import InvalidSessionWorkloadError


@dataclass(frozen=True)
class ResolvedMount:
    binding: StorageBinding
    subpath: str
    mount: VFolderVolumeMount

    @property
    def volume_name(self) -> str:
        return claim_name(self.binding)


def binding_name(binding: StorageBinding) -> str:
    name: str = binding.metadata["name"]
    return name


def claim_name(binding: StorageBinding) -> str:
    return f"sb-{binding_name(binding)}"


def volume_name(binding: StorageBinding, namespace: str) -> str:
    return f"sb-{binding_name(binding)}-{namespace}"


def resolve_mount(mount: VFolderVolumeMount, bindings: Sequence[StorageBinding]) -> ResolvedMount:
    """The binding whose mount base path is the longest prefix of the vfolder's path."""
    path = posixpath.normpath(mount.host_path)
    best: StorageBinding | None = None
    for binding in bindings:
        base = posixpath.normpath(binding.spec.mount_base_path)
        if path != base and not path.startswith(base.rstrip("/") + "/"):
            continue
        if best is None or len(base) > len(posixpath.normpath(best.spec.mount_base_path)):
            best = binding
    if best is None:
        raise InvalidSessionWorkloadError(
            f"no StorageBinding covers the vfolder {mount.name} ({mount.host_path})"
        )
    subpath = posixpath.relpath(path, posixpath.normpath(best.spec.mount_base_path))
    return ResolvedMount(best, "" if subpath == "." else subpath, mount)


def build_volume(binding: StorageBinding, namespace: str) -> dict[str, Any]:
    """A PV for one namespace, pre-bound to that namespace's claim: a PV binds one claim."""
    pv = binding.spec.pv
    spec: dict[str, Any] = {
        "capacity": {"storage": pv.capacity},
        "accessModes": ["ReadWriteMany"],
        "persistentVolumeReclaimPolicy": "Retain",
        "storageClassName": pv.storage_class_name,
        "claimRef": {"namespace": namespace, "name": claim_name(binding)},
        "csi": {
            "driver": pv.csi.driver,
            # The handle is per PV: the CSI node plugin keys its mounts by it.
            "volumeHandle": f"{pv.csi.volume_handle}#{namespace}",
            "volumeAttributes": dict(pv.csi.volume_attributes),
        },
    }
    if pv.csi.fs_type:
        spec["csi"]["fsType"] = pv.csi.fs_type
    if pv.mount_options:
        spec["mountOptions"] = list(pv.mount_options)
    if binding.spec.node_selector:
        spec["nodeAffinity"] = {
            "required": {
                "nodeSelectorTerms": [
                    {
                        "matchExpressions": [
                            {"key": k, "operator": "In", "values": [v]}
                            for k, v in binding.spec.node_selector.items()
                        ]
                    }
                ]
            }
        }
    return {
        "apiVersion": "v1",
        "kind": "PersistentVolume",
        "metadata": {
            "name": volume_name(binding, namespace),
            "labels": {"backend.ai/storage-binding": binding_name(binding)},
        },
        "spec": spec,
    }


def build_claim(binding: StorageBinding, namespace: str) -> dict[str, Any]:
    return {
        "apiVersion": "v1",
        "kind": "PersistentVolumeClaim",
        "metadata": {
            "name": claim_name(binding),
            "namespace": namespace,
            "labels": {"backend.ai/storage-binding": binding_name(binding)},
        },
        "spec": {
            "accessModes": ["ReadWriteMany"],
            "storageClassName": binding.spec.pv.storage_class_name,
            "volumeName": volume_name(binding, namespace),
            "resources": {"requests": {"storage": binding.spec.pv.capacity}},
        },
    }


def pod_volumes(resolved: Sequence[ResolvedMount]) -> list[dict[str, Any]]:
    names = sorted({r.volume_name for r in resolved})
    return [{"name": name, "persistentVolumeClaim": {"claimName": name}} for name in names]


def volume_mounts(resolved: Sequence[ResolvedMount]) -> list[dict[str, Any]]:
    return [
        {
            "name": r.volume_name,
            "mountPath": r.mount.kernel_path,
            "subPath": r.subpath,
            "readOnly": r.mount.mount_perm == MountPermission.RO,
        }
        for r in resolved
    ]
