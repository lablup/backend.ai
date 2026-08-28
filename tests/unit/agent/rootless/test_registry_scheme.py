"""Which registries are reached over plain HTTP — one decision, shared by both rootless backends.

The metadata probe in this module already chose per registry, while the runtimes' pull flags were
unconditional. That disagreement is not cosmetic: `ENROOT_ALLOW_HTTP` and apptainer's `--no-https`
do not *permit* http, they PIN it, so every pull from a public HTTPS registry was sent to port 80
and hung there until curl timed out (measured live against cr.backend.ai, which is what made a
multi-node enroot session sit in PREPARED).
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import pytest

from ai.backend.agent.enroot.runtime import EnrootRuntime
from ai.backend.agent.rootless.registry import (
    _credentials_for,
    _parse_ref,
    is_insecure_registry,
)
from ai.backend.agent.singularity.runtime import SingularityRuntime


class TestIsInsecureRegistry:
    @pytest.mark.parametrize(
        "ref",
        [
            "192.168.0.156:5000/stable/python:3.13",
            "localhost/committed-x:latest",
            "registry.internal:5000/team/img:1",
        ],
    )
    def test_a_registry_reached_by_port_or_localhost_is_insecure(self, ref: str) -> None:
        assert is_insecure_registry(ref) is True

    @pytest.mark.parametrize(
        "ref",
        [
            "cr.backend.ai/stable/python:3.13-ubuntu24.04-amd64",
            "ghcr.io/lablup/something:1",
            "python:3.13",  # Docker Hub
            "library/python:3.13",
        ],
    )
    def test_a_public_registry_is_not(self, ref: str) -> None:
        assert is_insecure_registry(ref) is False

    def test_a_digest_reference_is_parsed_the_same_way(self) -> None:
        """`@sha256:...` takes a different branch of the ref parser; the verdict must not move."""
        digest = "@sha256:" + "0" * 64
        assert is_insecure_registry("cr.backend.ai/stable/python" + digest) is False
        assert is_insecure_registry("192.168.0.156:5000/stable/python" + digest) is True


def _runtime(cls: Any, tmp_path: Path) -> Any:
    return cls(
        data_path=tmp_path / "data",
        cache_path=tmp_path / "cache",
        runtime_path=tmp_path / "run",
        state_path=tmp_path / "state",
        kernel_uid=os.geteuid(),
        kernel_gid=os.getegid(),
    )


class TestTheScopeOfThePlainHttpFlag:
    async def test_enroot_forces_http_only_for_an_insecure_registry(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        rt = _runtime(EnrootRuntime, tmp_path)
        (tmp_path / "data").mkdir(parents=True)
        seen: list[Any] = []

        async def _fake_run(*argv: str, **kwargs: Any) -> tuple[int, bytes, bytes]:
            seen.append(kwargs.get("extra_env"))
            return 1, b"", b"stopped before touching the network"

        monkeypatch.setattr(rt, "_run", _fake_run)

        with pytest.raises(RuntimeError):
            await rt.pull_image("192.168.0.156:5000/stable/python:3.13")
        assert seen[-1] == {"ENROOT_ALLOW_HTTP": "y"}

        with pytest.raises(RuntimeError):
            await rt.pull_image("cr.backend.ai/stable/python:3.13-ubuntu24.04-amd64")
        assert seen[-1] is None

    async def test_the_flag_is_not_in_the_process_environment_any_more(
        self, tmp_path: Path
    ) -> None:
        """It used to ride on every enroot invocation, not just the one that talks to a registry."""
        rt = _runtime(EnrootRuntime, tmp_path)
        assert "ENROOT_ALLOW_HTTP" not in rt._runtime_env()

    async def test_apptainer_pins_http_only_for_an_insecure_registry(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        rt = _runtime(SingularityRuntime, tmp_path)
        (tmp_path / "data").mkdir(parents=True)
        seen: list[tuple[str, ...]] = []

        async def _fake_run(*argv: str, **kwargs: Any) -> tuple[int, bytes, bytes]:
            seen.append(argv)
            return 1, b"", b"stopped before touching the network"

        monkeypatch.setattr(rt, "_run", _fake_run)

        with pytest.raises(RuntimeError):
            await rt.pull_image("192.168.0.156:5000/stable/python:3.13")
        assert "--no-https" in seen[-1]

        with pytest.raises(RuntimeError):
            await rt.pull_image("cr.backend.ai/stable/python:3.13-ubuntu24.04-amd64")
        assert "--no-https" not in seen[-1]


class TestTheInsecureHeuristic:
    """A port used to be the whole test, and 443 is the case where naming the port says the
    opposite of what the test concluded."""

    def test_the_standard_https_port_is_not_insecure(self) -> None:
        assert is_insecure_registry("registry.example.com:443/team/img:1") is False

    def test_another_explicit_port_still_is(self) -> None:
        assert is_insecure_registry("registry.example.com:5000/team/img:1") is True
        assert is_insecure_registry("registry.example.com:80/team/img:1") is True

    def test_a_tag_colon_is_not_a_port(self) -> None:
        assert is_insecure_registry("cr.backend.ai/stable/python:3.13") is False


class TestCredentialsOnTheHttpFallback:
    """A registry we did not classify as insecure is tried https-then-http, and the second attempt
    used to carry the same username and password — so a registry whose TLS merely broke handed the
    operator's credentials over in cleartext, on the strength of a failure."""

    def test_a_secure_registry_falls_back_anonymously(self) -> None:
        ref = _parse_ref("cr.backend.ai/stable/python:3.13")
        creds = {"username": "u", "password": "p"}
        assert _credentials_for("https", ref, creds) == creds
        assert _credentials_for("http", ref, creds) == {}

    def test_an_insecure_registry_still_authenticates(self) -> None:
        """It was never going to be TLS, so http is not a downgrade and a private registry there
        still has to be reachable."""
        ref = _parse_ref("192.168.0.156:5000/stable/python:3.13")
        creds = {"username": "u", "password": "p"}
        assert _credentials_for("http", ref, creds) == creds
