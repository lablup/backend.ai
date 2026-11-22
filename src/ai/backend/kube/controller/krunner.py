"""Choose the kernel runner build that `deploy/krunner/install.sh` copies for an image."""

from __future__ import annotations

import re
from dataclasses import dataclass
from importlib.resources import files

from ai.backend.kube.errors import UnsupportedBaseDistroError

_RX_VERSION_SUFFIX = re.compile(r"(\d+(\.\d+)*)$")
_RX_LIBBAIHOOK = re.compile(r"^libbaihook\.([a-z-]+\d+\.\d+)\.([a-z0-9_]+)\.so$")


@dataclass(frozen=True)
class KrunnerSelection:
    libc: str
    arch: str
    libbaihook: str


def _split_distro(distro: str) -> tuple[str, tuple[int, ...] | None]:
    m = _RX_VERSION_SUFFIX.search(distro)
    if m is None:
        return distro, None
    return distro[: -len(m.group(1))], tuple(map(int, m.group(1).split(".")))


def match_distro(candidates: list[str], distro: str) -> str:
    """The newest candidate of the same distro not newer than `distro` (same rule as the Agent)."""
    prefix, version = _split_distro(distro)
    ranked = sorted(
        (
            (_split_distro(key)[1] or (0,), key)
            for key in candidates
            if _split_distro(key)[0] == prefix
        ),
        reverse=True,
    )
    if not ranked:
        raise UnsupportedBaseDistroError(f"no kernel runner build for {distro}")
    if version is None:
        return ranked[0][1]
    for candidate_version, key in ranked:
        if version >= candidate_version:
            return key
    return ranked[-1][1]


def available_libbaihooks(arch: str) -> dict[str, str]:
    """Distro → libbaihook file name in `ai.backend.runner`."""
    found: dict[str, str] = {}
    for entry in files("ai.backend.runner").iterdir():
        m = _RX_LIBBAIHOOK.match(entry.name)
        if m is not None and m.group(2) == arch:
            found[m.group(1)] = entry.name
    return found


def select_krunner(distro: str, arch: str) -> KrunnerSelection:
    libc = "musllinux" if distro.startswith("alpine") else "static-gnu"
    hooks = available_libbaihooks(arch)
    return KrunnerSelection(
        libc=libc,
        arch=arch,
        libbaihook=hooks[match_distro(list(hooks), distro)],
    )
