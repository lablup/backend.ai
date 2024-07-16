"""
The kernel main program.
"""

import argparse
import importlib
import os
import signal
import sys
from pathlib import Path

from . import lang_map
from .compat import asyncio_run_forever


def setproctitle(title):
    # setproctitle package doesn't work for unknown reasons
    # We don't need a portable implementation, so here is a Linux-only version
    import ctypes
    import ctypes.util

    libc_path = ctypes.util.find_library("c")
    libc = ctypes.CDLL(libc_path)
    PR_SET_NAME = 15
    title = ctypes.c_char_p(bytes(title, "utf-8"))
    libc.prctl(PR_SET_NAME, title)


def parse_args(args=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", action="store_true", default=False)
    parser.add_argument("lang", type=str, choices=lang_map.keys())
    parser.add_argument("runtime_path", type=Path, nargs="?", default=None)
    return parser.parse_args(args)


def main(args) -> None:
    cls_name = lang_map[args.lang]
    imp_path, cls_name = cls_name.rsplit(".", 1)
    mod = importlib.import_module(imp_path)
    cls = getattr(mod, cls_name)

    if args.runtime_path is None:
        runtime_path = cls.default_runtime_path
    else:
        runtime_path = args.runtime_path
    runner = cls(runtime_path)

    # Replace stdin with a "null" file
    # (trying to read stdin will raise EOFError immediately afterwards.)
    sys.stdin = open(os.devnull, "r", encoding="latin1")
    setproctitle("backend.ai: kernel runner")
    asyncio_run_forever(
        runner._init(args),
        runner._shutdown(),
        stop_signals={signal.SIGINT, signal.SIGTERM},
        debug=args.debug,
    )


args = parse_args()
main(args)
