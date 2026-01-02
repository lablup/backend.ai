"""
VFolderID type adapter for Pydantic.
"""

from __future__ import annotations

from typing import Annotated, Any

from pydantic import BeforeValidator, PlainSerializer

from ..types import VFolderID


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


VFolderIDField = Annotated[
    VFolderID,
    BeforeValidator(_parse_vfolder_id),
    PlainSerializer(_serialize_vfolder_id, return_type=str),
]
