"""Which distro an image's libc implies — the answer that picks the krunner we inject into it.

Both backends probe the same way (`ldd --version` inside the image) and used to each carry their
own copy of this mapping, so the two could drift on the one thing they must agree about: the
krunner binaries are linked against a specific glibc, and choosing the wrong distro ships a kernel
runner the image's libc cannot load.
"""

import pytest

from ai.backend.agent.image_distro import (
    UnknownImageLibc,
    distro_from_ldd_output,
    known_glibc_distros,
)


class TestGlibc:
    def test_a_known_version_maps_to_its_distro(self) -> None:
        assert distro_from_ldd_output("ldd (Ubuntu GLIBC 2.35-0ubuntu3) 2.35") == "ubuntu22.04"
        assert distro_from_ldd_output("ldd (GNU libc) 2.17") == "centos7.6"

    def test_an_unknown_version_falls_back_to_the_newest_one_below_it(self) -> None:
        # NOT the next one up. glibc is backward-compatible, so a krunner built for an older distro
        # runs on a newer libc; one built for a newer distro is linked against symbols the image
        # does not have, and the kernel runner fails to start.
        assert distro_from_ldd_output("ldd (GNU libc) 2.33") == "ubuntu20.04"  # between 2.31, 2.34

    def test_a_version_newer_than_everything_we_know_takes_the_newest(self) -> None:
        assert (
            distro_from_ldd_output("ldd (GNU libc) 2.99") == list(known_glibc_distros.values())[-1]
        )

    def test_a_version_older_than_everything_we_know_takes_the_oldest(self) -> None:
        # 2.12 predates every entry we have. It must NOT get the newest one: `idx - 1` at idx 0
        # wraps to the end of the list, which handed the oldest images the newest distro's krunner
        # — linked against symbols their libc does not have, so it could never load.
        oldest = list(known_glibc_distros.values())[0]
        assert distro_from_ldd_output("ldd (GNU libc) 2.12") == oldest
        assert (
            distro_from_ldd_output("ldd (GNU libc) 2.12") != list(known_glibc_distros.values())[-1]
        )


class TestMusl:
    def test_musl_is_alpine(self) -> None:
        assert distro_from_ldd_output("musl libc (x86_64)") == "alpine3.8"


class TestNeither:
    def test_unrecognised_output_is_refused_by_name(self) -> None:
        # Guessing here would inject a krunner the image cannot run, and the failure would surface
        # much later as an unexplained kernel that never comes up.
        with pytest.raises(UnknownImageLibc):
            distro_from_ldd_output("some unexpected output")

    def test_empty_output_is_refused(self) -> None:
        with pytest.raises(UnknownImageLibc):
            distro_from_ldd_output("")
