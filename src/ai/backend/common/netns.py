import ctypes
import ctypes.util
import logging
import os
from pathlib import Path
from typing import Any

from ai.backend.logging import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

_libc: ctypes.CDLL | None = None
CLONE_NEWNET = 1 << 30


def _get_libc() -> ctypes.CDLL:
    global _libc
    if _libc is None:
        libc_path = ctypes.util.find_library("c")
        _libc = ctypes.CDLL(libc_path, use_errno=True)
    return _libc


def setns(fd: int) -> None:
    libc = _get_libc()
    ret = libc.setns(fd, CLONE_NEWNET)
    if ret == -1:
        errno = ctypes.get_errno()
        raise OSError(errno, f"setns() failed: {os.strerror(errno)}")


class NetworkNamespaceManager:
    def __init__(self, path: Path) -> None:
        self.self_ns = os.open("/proc/self/ns/net", os.O_RDONLY)
        self.new_ns = os.open(path, os.O_RDONLY)

    def __enter__(self) -> None:
        setns(self.new_ns)

    def __exit__(self, *exc_info_args: Any) -> None:
        try:
            setns(self.self_ns)
        except OSError:
            log.warning("Failed to restore original network namespace")
        finally:
            os.close(self.new_ns)
            os.close(self.self_ns)


def nsenter(path: Path) -> NetworkNamespaceManager:
    return NetworkNamespaceManager(path)
