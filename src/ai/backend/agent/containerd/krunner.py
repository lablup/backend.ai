"""containerd-native krunner env provisioning (BEP-1062).

The Docker backend materializes each krunner env as a Docker *volume*, populated by running
an extractor container (``docker run`` + ``docker volume create``). The containerd backend
does neither: the extractor is just ``tar xJf`` into a directory, so we unpack the packaged
``krunner-env.{distro}.{arch}.tar.xz`` straight to a host directory and bind-mount that —
no Docker daemon, no nerdctl volume.

Returns ``{distro: absolute host path}``; the path flows into the krunner mount as an
absolute source, which the runtime binds directly.
"""

from __future__ import annotations

import asyncio
import logging
import shutil
import tarfile
from collections.abc import Mapping
from importlib.resources import files
from pathlib import Path
from typing import Any

from ai.backend.agent.utils import get_arch_name
from ai.backend.logging import BraceStyleAdapter
from ai.backend.plugin.entrypoint import scan_entrypoints

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

# Host root for extracted krunner envs (bind-mounted read-only into every container).
KRUNNER_ROOT = Path("/var/lib/backend.ai/krunner")
_ENTRY_PREFIX = "backendai_krunner_v10"


def _extract(distro: str, entrypoint_name: str, arch: str) -> str | None:
    """Extract the packaged krunner archive for (distro, arch) to a versioned host dir
    (idempotent by version); return its absolute path, or None if unsupported."""
    pkg = f"ai.backend.krunner.{entrypoint_name}"
    version = int(
        Path(str(files(pkg).joinpath(f"krunner-version.{distro}.txt"))).read_text().strip()
    )
    name = f"backendai-krunner.v{version}.{arch}.{distro}"
    target = KRUNNER_ROOT / name
    stamp = target / "VERSION"
    if stamp.is_file() and stamp.read_text().strip() == str(version):
        return str(target)  # already extracted at this version
    archive = Path(str(files(pkg).joinpath(f"krunner-env.{distro}.{arch}.tar.xz"))).resolve()
    if not archive.exists():
        log.warning("krunner environment for {} ({}) is not supported!", distro, arch)
        return None
    log.info("extracting krunner env {} (v{}) -> {}", name, version, target)
    if target.exists():
        shutil.rmtree(target)
    target.mkdir(parents=True)
    # Our own trusted archive; preserve modes/links exactly as the shell extractor's `tar` did.
    with tarfile.open(str(archive), "r:xz") as tar:
        tar.extractall(target, filter="fully_trusted")
    stamp.write_text(str(version))
    return str(target)


async def prepare_krunner_env(_local_config: Mapping[str, Any]) -> Mapping[str, str]:
    """Ensure every packaged krunner distro env is extracted on this host; return
    ``{distro: host path}`` for the krunner mount."""
    arch = get_arch_name()
    result: dict[str, str] = {}
    for entrypoint in scan_entrypoints(_ENTRY_PREFIX):
        plugin = entrypoint.load()
        await plugin.init({})
        versions = (
            Path(str(files(f"ai.backend.krunner.{entrypoint.name}").joinpath("versions.txt")))
            .read_text()
            .splitlines()
        )
        for distro in versions:
            path = await asyncio.to_thread(_extract, distro, entrypoint.name, arch)
            if path is not None:
                result[distro] = path
    return result
