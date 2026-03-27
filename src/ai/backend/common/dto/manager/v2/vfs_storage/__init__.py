"""VFS Storage DTOs v2 for Manager API."""

from ai.backend.common.dto.manager.v2.vfs_storage.request import (
    AdminSearchVFSStoragesInput,
    CreateVFSStorageInput,
    DeleteVFSStorageInput,
    UpdateVFSStorageInput,
)
from ai.backend.common.dto.manager.v2.vfs_storage.response import (
    AdminSearchVFSStoragesPayload,
    CreateVFSStoragePayload,
    DeleteVFSStoragePayload,
    UpdateVFSStoragePayload,
    VFSStorageNode,
)

__all__ = (
    "AdminSearchVFSStoragesInput",
    "AdminSearchVFSStoragesPayload",
    "CreateVFSStorageInput",
    "CreateVFSStoragePayload",
    "DeleteVFSStorageInput",
    "DeleteVFSStoragePayload",
    "UpdateVFSStorageInput",
    "UpdateVFSStoragePayload",
    "VFSStorageNode",
)
