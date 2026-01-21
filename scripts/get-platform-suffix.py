#! /usr/bin/env python3

import platform
import sys

arch_name_aliases = {
    "arm64": "aarch64",  # macOS with LLVM
    "amd64": "x86_64",  # Windows/Linux
    "x64": "x86_64",  # Windows
    "x32": "x86",  # Windows
    "i686": "x86",  # Windows
}

kernel_name_aliases = {
    "linux": "linux",
    "darwin": "macos",
    "win32": "windows",
}

platform_kernel = kernel_name_aliases.get(sys.platform, sys.platform)
platform_arch = arch_name_aliases.get(platform.machine(), platform.machine())

print(f"{platform_kernel}-{platform_arch}")
