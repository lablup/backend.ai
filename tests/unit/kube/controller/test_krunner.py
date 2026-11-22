from __future__ import annotations

import platform

import pytest

from ai.backend.kube.controller.krunner import match_distro, select_krunner
from ai.backend.kube.errors import UnsupportedBaseDistroError

CANDIDATES = ["ubuntu18.04", "ubuntu20.04", "ubuntu22.04", "centos8.0", "alpine3.8"]


class TestMatchDistro:
    @pytest.mark.parametrize(
        ("distro", "expected"),
        [
            ("ubuntu22.04", "ubuntu22.04"),
            ("ubuntu24.04", "ubuntu22.04"),
            ("ubuntu21.10", "ubuntu20.04"),
            ("ubuntu16.04", "ubuntu18.04"),
            ("ubuntu", "ubuntu22.04"),
        ],
    )
    def test_newest_not_newer(self, distro: str, expected: str) -> None:
        assert match_distro(CANDIDATES, distro) == expected

    def test_unknown_distro(self) -> None:
        with pytest.raises(UnsupportedBaseDistroError):
            match_distro(CANDIDATES, "fedora40")


class TestSelectKrunner:
    def test_alpine_uses_musl_build(self) -> None:
        assert select_krunner("alpine3.19", "x86_64").libc == "musllinux"

    def test_glibc_uses_static_build_of_the_arch(self) -> None:
        # Only the host architecture's builds are packaged.
        arch = {"amd64": "x86_64", "arm64": "aarch64"}.get(platform.machine(), platform.machine())
        selection = select_krunner("ubuntu24.04", arch)
        assert selection.libc == "static-gnu"
        assert selection.libbaihook == f"libbaihook.ubuntu22.04.{arch}.so"
