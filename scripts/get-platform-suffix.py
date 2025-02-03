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

platform_kernel = sys.platform
platform_arch = arch_name_aliases.get(platform.machine(), platform.machine())

print(f"{platform_kernel}-{platform_arch}")
