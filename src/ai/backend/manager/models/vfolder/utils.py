from typing import Any
from uuid import UUID

from ai.backend.manager.data.deployment.types import MountSpec


def merge_mount_options_with_subpaths(mount_spec: MountSpec) -> dict[UUID, dict[str, Any]]:
    """Merge mount_subpaths into mount_options for prepare_vfolder_mounts consumption."""
    merged: dict[UUID, dict[str, Any]] = {k: dict(v) for k, v in mount_spec.mount_options.items()}
    for vfolder_id, subpath in mount_spec.mount_subpaths.items():
        if vfolder_id in merged:
            merged[vfolder_id]["subpath"] = subpath
        else:
            merged[vfolder_id] = {"subpath": subpath}
    return merged
