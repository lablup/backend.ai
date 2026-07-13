"""Identify an image's libc flavour and distro from its `ldd --version` output.

Runtime-neutral: every backend probes the image the same way (run `ldd --version` in it and match
the output) and only differs in how it runs the probe. These lived in the Docker backend, which
forced the containerd backend to import from it.
"""

import re
from typing import Final

LDD_GLIBC_REGEX = re.compile(r"^ldd \([^\)]+\) ([\d\.]+)$")
LDD_MUSL_REGEX = re.compile(r"^musl libc .+$")

known_glibc_distros: Final[dict[float, str]] = {
    2.17: "centos7.6",
    2.27: "ubuntu18.04",
    2.28: "centos8.0",
    2.31: "ubuntu20.04",
    2.34: "centos9.0",
    2.35: "ubuntu22.04",
    2.39: "ubuntu24.04",
}


def distro_from_ldd_output(first_line: str) -> str:
    """The distro an image's first `ldd --version` line implies.

    A glibc version we do not know by name resolves to the newest one below it — the ABI is
    backward-compatible, so the krunner built for that distro runs on this image; picking the next
    one *up* would ship binaries linked against symbols the image's libc does not have.
    """
    if m := LDD_GLIBC_REGEX.search(first_line):
        version = float(m.group(1))
        if version in known_glibc_distros:
            return known_glibc_distros[version]
        distros = list(known_glibc_distros.values())
        for idx, known_version in enumerate(known_glibc_distros.keys()):
            if version < known_version:
                # Older than everything we know: there is nothing below it, so take the oldest we
                # have. (`idx - 1` at idx 0 wraps to the NEWEST — which is the one guaranteed not to
                # run, since its krunner is linked against symbols this libc does not have.)
                return distros[idx - 1] if idx > 0 else distros[0]
        return distros[-1]
    if LDD_MUSL_REGEX.search(first_line):
        return "alpine3.8"
    raise UnknownImageLibc(f"could not determine the C library variant from {first_line!r}")


class UnknownImageLibc(RuntimeError):
    """The image's `ldd --version` names neither glibc nor musl, so no krunner can be chosen
    for it."""
