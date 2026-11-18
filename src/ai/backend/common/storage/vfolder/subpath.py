from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from pydantic import TypeAdapter, ValidationError

from ai.backend.common.exception import InvalidVFolderMountSourceError
from ai.backend.common.typed_validators import VFolderRelativePath

_vfolder_relative_path_adapter: TypeAdapter[str] = TypeAdapter(VFolderRelativePath)


@dataclass(frozen=True)
class VFolderSubpath:
    base_path: Path
    subpath: PurePosixPath


def resolve_vfolder_subpath(target: VFolderSubpath) -> Path:
    """Resolve the subpath under the vfolder base and reject one that leaves the vfolder."""
    if not target.subpath.parts:
        return target.base_path
    _validate_relative_path(target.subpath.as_posix(), target)
    try:
        resolved_base = target.base_path.resolve(strict=True)
        resolved_path = (target.base_path / target.subpath).resolve(strict=True)
    except OSError as e:
        raise InvalidVFolderMountSourceError(
            f"Cannot resolve the subpath {target.subpath} under {target.base_path}: {e}"
        ) from e
    resolved_relpath = os.path.relpath(resolved_path, resolved_base)
    if resolved_relpath != os.curdir:
        _validate_relative_path(resolved_relpath, target)
    return resolved_path


def _validate_relative_path(relpath: str, target: VFolderSubpath) -> None:
    try:
        _vfolder_relative_path_adapter.validate_python(relpath)
    except ValidationError as e:
        raise InvalidVFolderMountSourceError(
            f"The subpath {target.subpath} resolves outside {target.base_path}"
        ) from e
