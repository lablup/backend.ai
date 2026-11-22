"""Dotfile path rules shared by the manager and the agent."""

import re
from pathlib import PurePosixPath
from typing import override

from ai.backend.common.exception import (
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
    InvalidAPIParameters,
)

_KERNEL_WORK_DIR = PurePosixPath("/home/work")

_RESERVED_PATHS = frozenset({
    ".terminfo",
    ".jupyter",
    ".ssh",
    ".ssh/authorized_keys",
    ".local",
    ".config",
})

# Compared with the first segment only: `.aws/config` and `.ssh/config` stay valid.
_RESERVED_FIRST_SEGMENTS = frozenset({
    "config",
    "ssh",
    "restart-state",
    "kconfig.dat",
    "cluster.json",
    "environ.txt",
    "environ_base.txt",
    "resource.txt",
    "resource_base.txt",
    "docker-creds.json",
    "intrinsic-ports.json",
    "dotfiles.json",
    "id_container",
})


class InvalidDotfilePath(InvalidAPIParameters):
    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.DOTFILE,
            operation=ErrorOperation.PARSING,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )


# C0 and C1 control characters, DEL included. A newline would split the kernel file manifest.
_RX_CONTROL = re.compile(r"[\x00-\x1f\x7f-\x9f]")
_RX_PERM = re.compile(r"0?[0-7]{3}")


def _relative_dotfile_path(raw: str) -> PurePosixPath:
    if _RX_CONTROL.search(raw):
        raise InvalidDotfilePath("dotfile path must not contain control characters.")
    if raw != raw.strip():
        raise InvalidDotfilePath("dotfile path must not start or end with whitespace.")
    path = PurePosixPath(raw)
    if ".." in path.parts:
        raise InvalidDotfilePath(f"dotfile path must stay under {_KERNEL_WORK_DIR}.")
    if path.is_absolute():
        if not path.is_relative_to(_KERNEL_WORK_DIR):
            raise InvalidDotfilePath(f"dotfile path must stay under {_KERNEL_WORK_DIR}.")
        path = path.relative_to(_KERNEL_WORK_DIR)
    if not path.parts:
        raise InvalidDotfilePath("dotfile path must name a file.")
    if str(path) in _RESERVED_PATHS or path.parts[0] in _RESERVED_FIRST_SEGMENTS:
        raise InvalidDotfilePath("dotfile path is reserved for internal operations.")
    return path


def validate_dotfile_path(raw: str) -> str:
    """Return ``raw`` unchanged if it is a dotfile path under `/home/work`; raise
    :class:`InvalidDotfilePath` otherwise."""
    _relative_dotfile_path(raw)
    return raw


def validate_dotfile_perm(raw: str) -> str:
    """Return ``raw`` unchanged if it is an octal file mode from ``000`` to ``0777``; raise
    :class:`InvalidDotfilePath` otherwise."""
    if not _RX_PERM.fullmatch(raw):
        raise InvalidDotfilePath("dotfile permission must be an octal mode from 000 to 0777.")
    return raw


class DotfilePath:
    """A dotfile path under `/home/work`; relative paths are based on that directory."""

    relative: PurePosixPath

    def __init__(self, raw: str) -> None:
        self.relative = _relative_dotfile_path(raw)
