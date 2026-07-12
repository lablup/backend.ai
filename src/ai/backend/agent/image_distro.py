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
