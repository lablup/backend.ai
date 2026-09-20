"""The libc-to-distro mapping every backend's image probe ends in."""

from __future__ import annotations

from ai.backend.agent.image_distro import (
    is_deeplearning_image,
    known_glibc_distros,
    libc_probe_commands,
    parse_distro_from_ldd_output,
)


def _distro(line: str) -> str | None:
    return parse_distro_from_ldd_output([line])


class TestGlibc:
    def test_a_known_version_maps_to_its_distro(self) -> None:
        assert _distro("ldd (Ubuntu GLIBC 2.35-0ubuntu3) 2.35") == "ubuntu22.04"
        assert _distro("ldd (GNU libc) 2.17") == "centos7.6"

    def test_an_unknown_version_falls_back_to_the_newest_one_below_it(self) -> None:
        # NOT the next one up. glibc is backward-compatible, so a krunner built for an older distro
        # runs on a newer libc; one built for a newer distro is linked against symbols the image
        # does not have, and the kernel runner fails to start.
        assert _distro("ldd (GNU libc) 2.33") == "ubuntu20.04"  # between 2.31 and 2.34

    def test_a_version_newer_than_everything_we_know_takes_the_newest(self) -> None:
        assert _distro("ldd (GNU libc) 2.99") == list(known_glibc_distros.values())[-1]

    def test_a_version_older_than_everything_we_know_takes_the_oldest(self) -> None:
        # 2.12 predates every entry. It must NOT get the newest one: `idx - 1` at idx 0 wraps to
        # the end of the list, which handed the oldest images the newest distro's krunner.
        oldest = list(known_glibc_distros.values())[0]
        assert _distro("ldd (GNU libc) 2.12") == oldest

    def test_the_c_library_run_directly_is_read_too(self) -> None:
        banner = "GNU C Library (Debian GLIBC 2.41-12+deb13u3) stable release version 2.41."
        assert _distro(banner) == "ubuntu24.04"


class TestMusl:
    def test_musl_is_alpine(self) -> None:
        assert _distro("musl libc (x86_64)") == "alpine3.8"


class TestNeither:
    def test_unrecognised_output_resolves_to_nothing(self) -> None:
        # Guessing would inject a krunner the image cannot run, and the failure would surface much
        # later as an unexplained kernel that never comes up. The caller refuses by name instead.
        assert _distro("some unexpected output") is None
        assert _distro("") is None


class TestProbeCommands:
    def test_ldd_is_tried_first_and_the_arch_is_spelled_the_linux_way(self) -> None:
        commands = libc_probe_commands("x86_64")
        assert commands[0] == ["ldd", "--version"]
        assert ["/lib/x86_64-linux-gnu/libc.so.6"] in commands
        assert ["/lib/aarch64-linux-gnu/libc.so.6"] in libc_probe_commands("arm64")


class TestDeepLearningImages:
    def test_matched_on_the_name(self) -> None:
        assert is_deeplearning_image("cr.backend.ai/stable/python-tensorflow:2.16")
        assert not is_deeplearning_image("cr.backend.ai/stable/python:3.13-ubuntu24.04")
