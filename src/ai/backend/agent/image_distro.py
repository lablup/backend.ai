"""Identify an image's libc flavour, and so its krunner distro, from a probe run inside it.

Runtime-neutral: every backend runs the same probe commands in the image and reads the same
output; only how it runs them differs. Docker's `_run_libc_probe` and containerd's exec both end
here.
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from typing import Final

from ai.backend.common.arch import arch_name_aliases

__all__ = (
    "DEEPLEARNING_IMAGE_KEYS",
    "LDD_GLIBC_REGEX",
    "LDD_MUSL_REGEX",
    "LIBC_BANNER_GLIBC_REGEX",
    "distro_for_glibc_version",
    "is_deeplearning_image",
    "known_glibc_distros",
    "libc_probe_commands",
    "parse_distro_from_ldd_output",
)

LDD_GLIBC_REGEX = re.compile(r"^ldd \([^\)]+\) (\d+(?:\.\d+)?)[\d\.]*$")
LDD_MUSL_REGEX = re.compile(r"^musl libc .+$")
# Printed when the C library itself is executed (images without ldd), e.g.
# "GNU C Library (Debian GLIBC 2.41-12+deb13u3) stable release version 2.41."
LIBC_BANNER_GLIBC_REGEX = re.compile(r"^GNU C Library .*release version (\d+\.\d+)")

known_glibc_distros: Final[dict[float, str]] = {
    2.17: "centos7.6",
    2.27: "ubuntu18.04",
    2.28: "centos8.0",
    2.31: "ubuntu20.04",
    2.34: "centos9.0",
    2.35: "ubuntu22.04",
    2.39: "ubuntu24.04",
}

DEEPLEARNING_IMAGE_KEYS: Final[frozenset[str]] = frozenset({
    "tensorflow",
    "caffe",
    "keras",
    "torch",
    "mxnet",
    "theano",
})


def is_deeplearning_image(image_name: str) -> bool:
    """Whether an image is one the sample notebooks are meant for. Matched on the name, as it has
    always been -- the images carry no label saying so."""
    return any(key in image_name for key in DEEPLEARNING_IMAGE_KEYS)


def distro_for_glibc_version(version: float) -> str:
    """The newest known distro at or below this glibc: its krunner is linked against symbols the
    image's libc has; the next one up is not."""
    if version in known_glibc_distros:
        return known_glibc_distros[version]
    for idx, known_version in enumerate(known_glibc_distros.keys()):
        if version < known_version:
            return list(known_glibc_distros.values())[max(idx - 1, 0)]
    return list(known_glibc_distros.values())[-1]


def parse_distro_from_ldd_output(log_chunks: Sequence[str]) -> str | None:
    """Resolve the distro from the output of ``ldd --version`` or of the C library run directly."""
    for line in "".join(log_chunks).splitlines():
        stripped_line = line.strip()
        if m := LDD_GLIBC_REGEX.search(stripped_line):
            return distro_for_glibc_version(float(m.group(1)))
        if m := LIBC_BANNER_GLIBC_REGEX.search(stripped_line):
            return distro_for_glibc_version(float(m.group(1)))
        if LDD_MUSL_REGEX.search(stripped_line):
            return "alpine3.8"
    return None


def libc_probe_commands(arch: str) -> list[list[str]]:
    """Commands tried in order to learn an image's C library. ``ldd`` is authoritative and comes
    first; the rest execute the library itself for images without ldd and are best-effort (a musl
    image carrying a glibc compat layer would answer as glibc)."""
    arch = arch_name_aliases.get(arch.lower(), arch.lower())
    return [
        ["ldd", "--version"],
        [f"/lib/{arch}-linux-gnu/libc.so.6"],
        ["/lib64/libc.so.6"],
        ["/usr/lib64/libc.so.6"],
        ["/usr/lib/libc.so.6"],
        ["/lib/libc.so.6"],
        [f"/lib/ld-musl-{arch}.so.1"],
    ]
