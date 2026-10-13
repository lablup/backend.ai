"""Provision the kernel runner environments as host directories, without Docker volumes."""

from __future__ import annotations

import asyncio
import logging
import shutil
import tarfile
import tempfile
from collections.abc import Mapping
from importlib.resources import files
from pathlib import Path
from typing import Any, Final

from ai.backend.agent.errors.containerd import KrunnerEnvironmentError
from ai.backend.agent.utils import get_arch_name
from ai.backend.common.asyncio import run_in_executor_with_context
from ai.backend.logging.structured import StructuredLogger
from ai.backend.plugin.entrypoint import scan_entrypoints

log = StructuredLogger(logging.getLogger(__spec__.name))

KRUNNER_ENTRY_PREFIX: Final = "backendai_krunner_v10"
VERSION_FILE: Final = "VERSION"


def krunner_dir(root: Path, version: int, arch: str, distro: str) -> Path:
    return root / f"v{version}.{arch}.{distro}"


def extract_krunner_env(archive: Path, dest: Path, version: int) -> None:
    """Extract `archive` into `dest` unless `dest` is already complete; safe to run concurrently."""
    if (dest / VERSION_FILE).is_file():
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix=f".{dest.name}.", dir=dest.parent))
    try:
        with tarfile.open(archive, "r:xz") as tar:
            tar.extractall(tmp, filter="tar")
        (tmp / VERSION_FILE).write_text(f"{version}\n")
        try:
            tmp.rename(dest)
        except OSError:
            # Another process finished first; its directory is equivalent.
            if not (dest / VERSION_FILE).is_file():
                raise
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


async def _prepare_one(root: Path, distro: str, entrypoint_name: str) -> tuple[str, str | None]:
    arch = get_arch_name()
    package = files(f"ai.backend.krunner.{entrypoint_name}")
    try:
        version = int(
            Path(str(package.joinpath(f"krunner-version.{distro}.txt"))).read_text().strip()
        )
        archive = Path(str(package.joinpath(f"krunner-env.{distro}.{arch}.tar.xz"))).resolve()
        if not archive.exists():
            log.warning("krunner environment unsupported", distro=distro, arch=arch)
            return distro, None
        dest = krunner_dir(root, version, arch, distro)
        await run_in_executor_with_context(None, extract_krunner_env, archive, dest, version)
    except (OSError, ValueError, tarfile.TarError) as e:
        log.exception("krunner environment preparation failed", distro=distro, arch=arch)
        raise KrunnerEnvironmentError(f"{distro}.{arch}: {e}") from e
    return distro, str(dest)


async def prepare_krunner_env(local_config: Mapping[str, Any]) -> Mapping[str, str]:
    """Extract the packaged krunner archives into `<var-base-path>/krunner`; map distro to path."""
    root = Path(local_config["agent"]["var-base-path"]) / "krunner"
    distros: list[tuple[str, str]] = []
    for entrypoint in scan_entrypoints(KRUNNER_ENTRY_PREFIX):
        log.debug("krunner package loading", module_name=entrypoint.module)
        plugin = entrypoint.load()
        await plugin.init({})  # currently does nothing
        versions = Path(
            str(files(f"ai.backend.krunner.{entrypoint.name}").joinpath("versions.txt"))
        ).read_text()
        distros.extend((distro, entrypoint.name) for distro in versions.splitlines())
    results = await asyncio.gather(
        *(_prepare_one(root, distro, name) for distro, name in distros),
        return_exceptions=True,
    )
    volumes: dict[str, str] = {}
    for result in results:
        if isinstance(result, BaseException):
            continue  # already logged by _prepare_one; other distros stay usable
        distro, path = result
        if path is not None:
            volumes[distro] = path
    return volumes
