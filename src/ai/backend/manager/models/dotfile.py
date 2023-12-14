from __future__ import annotations

from pathlib import PurePosixPath
from typing import TYPE_CHECKING, Any, Mapping, Sequence

import sqlalchemy as sa

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import (
        AsyncConnection as SAConnection,
    )

from ai.backend.common import msgpack
from ai.backend.common.types import VFolderMount

from ..api.exceptions import BackendError
from ..types import UserScope
from .domain import query_domain_dotfiles
from .group import query_group_dotfiles
from .keypair import keypairs

__all__ = ("prepare_dotfiles",)


async def prepare_dotfiles(
    conn: SAConnection,
    user_scope: UserScope,
    access_key: str,
    vfolder_mounts: Sequence[VFolderMount],
) -> Mapping[str, Any]:
    # Feed SSH keypair and dotfiles if exists.
    internal_data = {}
    query = (
        sa.select([
            keypairs.c.ssh_public_key,
            keypairs.c.ssh_private_key,
            keypairs.c.dotfiles,
        ])
        .select_from(keypairs)
        .where(keypairs.c.access_key == access_key)
    )
    result = await conn.execute(query)
    row = result.first()
    dotfiles = msgpack.unpackb(row["dotfiles"])
    internal_data.update({"dotfiles": dotfiles})
    if row["ssh_public_key"] and row["ssh_private_key"]:
        internal_data["ssh_keypair"] = {
            "public_key": row["ssh_public_key"],
            "private_key": row["ssh_private_key"],
        }
    # use dotfiles in the priority of keypair > group > domain
    dotfile_paths = set(map(lambda x: x["path"], dotfiles))
    # add keypair dotfiles
    internal_data.update({"dotfiles": list(dotfiles)})
    # add group dotfiles
    dotfiles, _ = await query_group_dotfiles(conn, user_scope.group_id)
    for dotfile in dotfiles:
        if dotfile["path"] not in dotfile_paths:
            internal_data["dotfiles"].append(dotfile)
            dotfile_paths.add(dotfile["path"])
    # add domain dotfiles
    dotfiles, _ = await query_domain_dotfiles(conn, user_scope.domain_name)
    for dotfile in dotfiles:
        if dotfile["path"] not in dotfile_paths:
            internal_data["dotfiles"].append(dotfile)
            dotfile_paths.add(dotfile["path"])
    # reverse the dotfiles list so that higher priority can overwrite
    # in case the actual path is the same
    internal_data["dotfiles"].reverse()

    # check if there is no name conflict of dotfile and vfolder
    vfolder_kernel_paths = {m.kernel_path for m in vfolder_mounts}
    for dotfile in internal_data.get("dotfiles", []):
        dotfile_path = PurePosixPath(dotfile["path"])
        if not dotfile_path.is_absolute():
            dotfile_path = PurePosixPath("/home/work", dotfile["path"])
        if dotfile_path in vfolder_kernel_paths:
            raise BackendError(
                "There is a kernel-side path from vfolders that conflicts with "
                f"a dotfile '{dotfile['path']}'.",
            )

    return internal_data
