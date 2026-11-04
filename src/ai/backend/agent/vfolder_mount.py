from __future__ import annotations

import os
from pathlib import Path

from pydantic import TypeAdapter, ValidationError

from ai.backend.agent.errors.agent import InvalidVFolderMountSourceError
from ai.backend.common.typed_validators import VFolderRelativePath
from ai.backend.common.types import VFolderMount

_vfolder_relative_path_adapter: TypeAdapter[str] = TypeAdapter(VFolderRelativePath)


def resolve_vfolder_mount_source(vfolder: VFolderMount) -> Path:
    """Resolve the host path of a subpath mount and reject one that leaves its vfolder."""
    host_path = Path(vfolder.host_path)
    subpath_parts = vfolder.vfsubpath.parts
    if not subpath_parts:
        return host_path
    if host_path.parts[-len(subpath_parts) :] != subpath_parts:
        raise InvalidVFolderMountSourceError(
            f"The host path {host_path} does not end with the subpath {vfolder.vfsubpath}"
        )
    _validate_relative_path(vfolder.vfsubpath.as_posix(), vfolder)
    base_path = Path(*host_path.parts[: -len(subpath_parts)])
    try:
        resolved_base = base_path.resolve(strict=True)
        resolved_source = host_path.resolve(strict=True)
    except OSError as e:
        raise InvalidVFolderMountSourceError(
            f"Cannot resolve the mount source of vfolder {vfolder.vfid}: {e}"
        ) from e
    resolved_relpath = os.path.relpath(resolved_source, resolved_base)
    if resolved_relpath != os.curdir:
        _validate_relative_path(resolved_relpath, vfolder)
    return resolved_source


def _validate_relative_path(relpath: str, vfolder: VFolderMount) -> None:
    try:
        _vfolder_relative_path_adapter.validate_python(relpath)
    except ValidationError as e:
        raise InvalidVFolderMountSourceError(
            f"The subpath {vfolder.vfsubpath} of vfolder {vfolder.vfid} resolves outside the vfolder"
        ) from e
