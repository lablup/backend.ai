from __future__ import annotations

import asyncio
import platform
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from ai.backend.common.arch import arch_name_aliases

from .types import OSInfo, Platform

if TYPE_CHECKING:
    from .context import Context


async def detect_os(ctx: Context) -> OSInfo:
    platform_kernel = sys.platform
    platform_arch = arch_name_aliases.get(platform.machine(), platform.machine())
    distro: str | None = None
    uname_s_output = b""
    try:
        p = await asyncio.create_subprocess_shell(
            "uname -s",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
        )
        assert p.stdout is not None
        uname_s_output = (await p.stdout.read()).strip()
        await p.wait()
    except OSError:
        pass
    lsb_release_output = b""
    try:
        p = await asyncio.create_subprocess_shell(
            "lsb_release -d",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
        )
        assert p.stdout is not None
        lsb_release_output = (await p.stdout.read()).strip()
        await p.wait()
    except OSError:
        pass
    try:
        issue_output = Path("/etc/issue").read_bytes().strip()
    except IOError:
        issue_output = b""
    release_metadata = lsb_release_output + b"\n" + issue_output
    if uname_s_output == b"Darwin":
        assert platform_kernel == "darwin"
        platform_kernel = "macos"
        distro = "Darwin"
    elif (
        Path("/etc/debian_version").exists()
        or b"Ubuntu" in release_metadata
        or b"Debian" in release_metadata
    ):
        assert platform_kernel == "linux"
        distro = "Debian"
    elif (
        Path("/etc/redhat-release").exists()
        or Path("/etc/system-release").exists()
        or b"RedHat" in release_metadata
        or b"CentOS" in release_metadata
        or b"Amazon" in release_metadata
    ):
        assert platform_kernel == "linux"
        distro = "RedHat"
    elif Path("/etc/os-release").exists() or b"SUSE" in issue_output:
        assert platform_kernel == "linux"
        distro = "SUSE"
    else:
        raise RuntimeError(
            "Unsupported host linux distribution: "
            f"{uname_s_output.decode()!r}, {release_metadata.decode()!r}"
        )
    return OSInfo(
        platform=Platform(f"{platform_kernel}-{platform_arch}").value,  # type: ignore
        distro=distro,
    )


async def detect_cuda(ctx: Context) -> None:
    pass
