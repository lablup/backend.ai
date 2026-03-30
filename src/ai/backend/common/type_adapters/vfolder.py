"""
VFolderID type adapter for Pydantic.

Note: VFolderID now has native Pydantic support via __get_pydantic_core_schema__.
When used with Pydantic, that method takes precedence over these annotations.
The annotations below serve as documentation and allow future extensions with
non-Pydantic metadata.
"""

from __future__ import annotations

from typing import Annotated, Any

from pydantic import BeforeValidator, PlainSerializer

from ai.backend.common.types import VFolderID


def _parse_vfolder_id(v: Any) -> VFolderID:
    """Parse VFolderID from string or return as-is if already VFolderID."""
    if isinstance(v, VFolderID):
        return v
    if isinstance(v, str):
        return VFolderID.from_str(v)
    raise ValueError(f"Invalid VFolderID: {v}")


def _serialize_vfolder_id(v: VFolderID) -> str:
    """Serialize VFolderID to string."""
    return str(v)


# VFolderID has __get_pydantic_core_schema__, so Pydantic uses that.
# These annotations serve as documentation and allow future non-Pydantic extensions.
VFolderIDField = Annotated[
    VFolderID,
    BeforeValidator(_parse_vfolder_id),
    PlainSerializer(_serialize_vfolder_id, return_type=str),
]
