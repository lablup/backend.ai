from __future__ import annotations

import enum


class RapidFileEntryType(enum.StrEnum):
    FILE = "file"
    DIRECTORY = "directory"
    SYMLINK = "symlink"
