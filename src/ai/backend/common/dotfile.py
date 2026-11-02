"""Dotfile path rules shared by the manager and the agent."""

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


class DotfilePath:
    """A dotfile path under `/home/work`; relative paths are based on that directory."""

    relative: PurePosixPath

    def __init__(self, raw: str) -> None:
        self.relative = self._to_relative(raw)
        if str(self.relative) in _RESERVED_PATHS or self.relative.parts[0] in (
            _RESERVED_FIRST_SEGMENTS
        ):
            raise InvalidDotfilePath("dotfile path is reserved for internal operations.")

    def _to_relative(self, raw: str) -> PurePosixPath:
        path = PurePosixPath(raw)
        if "\x00" in raw or ".." in path.parts:
            raise InvalidDotfilePath(f"dotfile path must stay under {_KERNEL_WORK_DIR}.")
        if path.is_absolute():
            if not path.is_relative_to(_KERNEL_WORK_DIR):
                raise InvalidDotfilePath(f"dotfile path must stay under {_KERNEL_WORK_DIR}.")
            path = path.relative_to(_KERNEL_WORK_DIR)
        if not path.parts:
            raise InvalidDotfilePath("dotfile path must name a file.")
        return path
