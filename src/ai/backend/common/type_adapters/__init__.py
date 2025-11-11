"""
Type adapters for Pydantic serialization.

This package provides type adapter fields for custom classes
that need special serialization/deserialization handling.
"""

from .vfolder import VFolderIDField

__all__ = [
    "VFolderIDField",
]
