from __future__ import annotations

import asyncio
import platform
import sys
from pathlib import Path

from ai.backend.common.arch import arch_name_aliases
from ai.backend.common.identity import get_root_fs_type, get_wsl_version

from .types import OSInfo, Platform, PrerequisiteError


async def detect_os() -> OSInfo:
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
        if p.stdout is None:
            raise RuntimeError("Failed to capture stdout from uname command")
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
        if p.stdout is None:
            raise RuntimeError("Failed to capture stdout from lsb_release command")
        lsb_release_output = (await p.stdout.read()).strip()
        await p.wait()
    except OSError:
        pass
    try:
        issue_output = Path("/etc/issue").read_bytes().strip()
    except OSError:
        issue_output = b""
    release_metadata = lsb_release_output + b"\n" + issue_output
    if uname_s_output == b"Darwin":
        if platform_kernel != "darwin":
            raise RuntimeError(
                f"Platform kernel mismatch: expected 'darwin', got '{platform_kernel}'"
            )
        platform_kernel = "macos"
        distro = "Darwin"
    elif (
        Path("/etc/debian_version").exists()
        or b"Ubuntu" in release_metadata
        or b"Debian" in release_metadata
    ):
        if platform_kernel != "linux":
            raise RuntimeError(
                f"Platform kernel mismatch for Debian: expected 'linux', got '{platform_kernel}'"
            )
        distro = "Debian"
    elif (
        Path("/etc/redhat-release").exists()
        or Path("/etc/system-release").exists()
        or b"RedHat" in release_metadata
        or b"CentOS" in release_metadata
        or b"Amazon" in release_metadata
    ):
        if platform_kernel != "linux":
            raise RuntimeError(
                f"Platform kernel mismatch for RedHat: expected 'linux', got '{platform_kernel}'"
            )
        distro = "RedHat"
    elif Path("/etc/os-release").exists() or b"SUSE" in issue_output:
        if platform_kernel != "linux":
            raise RuntimeError(
                f"Platform kernel mismatch for SUSE: expected 'linux', got '{platform_kernel}'"
            )
        distro = "SUSE"
    else:
        raise PrerequisiteError(
            "Unsupported host linux distribution: "
            f"{uname_s_output.decode()!r}, {release_metadata.decode()!r}"
        )
    distro_variants = set()
    root_fs_dev, root_fs_type = get_root_fs_type()
    if root_fs_type is not None and not root_fs_dev.is_block_device():
        distro_variants.add("LiveCD")
    wsl_version = get_wsl_version()
    if wsl_version > 0:
        distro_variants.add("WSL")
    if wsl_version == 1:
        raise PrerequisiteError(f"Unsupported WSL version: {wsl_version}")
    return OSInfo(
        platform=Platform(f"{platform_kernel}-{platform_arch}").value,  # type: ignore
        distro=distro,
        distro_variants=distro_variants,
    )


async def detect_cuda() -> str:
    return "(none)"
