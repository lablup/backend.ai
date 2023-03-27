import os
from pathlib import Path


def setns(fd: int):
    import ctypes
    import ctypes.util

    libc_path = ctypes.util.find_library("c")
    libc = ctypes.CDLL(libc_path)
    CLONE_NEWNET = 1 << 30
    libc.setns(fd, CLONE_NEWNET)


class NetworkNamespaceManager:
    def __init__(self, path: Path):
        self.self_ns = os.open("/proc/self/ns/net", os.O_RDONLY)
        self.new_ns = os.open(path, os.O_RDONLY)

    def __enter__(self):
        setns(self.new_ns)

    def __exit__(self, *exc_info_args):
        setns(self.self_ns)
        os.close(self.new_ns)
        os.close(self.self_ns)


def nsenter(path: Path) -> NetworkNamespaceManager:
    return NetworkNamespaceManager(path)
