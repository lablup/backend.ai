"""Turning a committed `.sqsh` back into something a registry — and Docker — will accept.

A squashfs carries no OCI config, so the identity of a committed image is whatever the sidecar
recorded and this rebuilds. Getting it wrong produces an image that pushes and pulls perfectly and
only fails when someone runs it: the first cut republished the base image's `Cmd` as `Entrypoint`,
which surfaced as `cannot execute binary file` and nothing more.
"""

from __future__ import annotations

import gzip
import hashlib
import io
import tarfile
from pathlib import Path
from typing import Any

import pytest

from ai.backend.agent.enroot.runtime import EnrootRuntime
from ai.backend.agent.rootless.base import write_layer


def _config(**meta: Any) -> dict[str, Any]:
    return EnrootRuntime._image_config(meta)


class TestImageConfig:
    def test_entrypoint_and_cmd_stay_separate(self) -> None:
        """Docker's own semantics: `Entrypoint` is exec'd and `Cmd` is its default arguments.
        Collapsing the two makes the runtime try to exec the argument."""
        config = _config(entrypoint=["/opt/kernel/entrypoint.sh"], cmd=["/bin/bash"])["config"]

        assert config["Entrypoint"] == ["/opt/kernel/entrypoint.sh"]
        assert config["Cmd"] == ["/bin/bash"]

    def test_an_image_with_only_a_cmd_gets_no_entrypoint(self) -> None:
        """Most base images are this shape, and it is the shape that broke: an absent `Entrypoint`
        must stay absent rather than be filled in from `Cmd`."""
        config = _config(cmd=["/bin/bash"])["config"]

        assert "Entrypoint" not in config
        assert config["Cmd"] == ["/bin/bash"]

    def test_the_labels_the_agent_reads_back(self) -> None:
        """The kernel-spec / base-distro labels are how the manager knows what a committed image
        can run; without them it is unschedulable."""
        labels = {"ai.backend.kernelspec": "1", "ai.backend.base-distro": "ubuntu20.04"}

        assert _config(labels=labels)["config"]["Labels"] == labels

    def test_env_and_working_dir_are_carried_over(self) -> None:
        config = _config(env=["PATH=/usr/bin", "LANG=C.UTF-8"], working_dir="/home/work")["config"]

        assert config["Env"] == ["PATH=/usr/bin", "LANG=C.UTF-8"]
        assert config["WorkingDir"] == "/home/work"

    def test_the_architecture_is_inherited(self) -> None:
        assert _config(architecture="arm64")["architecture"] == "arm64"

    def test_an_empty_sidecar_still_produces_a_valid_config(self) -> None:
        """A sidecar written by an older agent has none of these keys. The push must still make a
        document a registry will accept rather than fail on a missing field."""
        document = _config()

        assert document["architecture"] == "amd64"
        assert document["os"] == "linux"
        assert document["config"]["Labels"] == {}


@pytest.fixture
def rootfs(tmp_path: Path) -> Path:
    root = tmp_path / "rootfs"
    (root / "usr" / "bin").mkdir(parents=True)
    (root / "usr" / "bin" / "hello").write_bytes(b"#!/bin/sh\necho hi\n")
    (root / "etc").mkdir()
    (root / "etc" / "hostname").write_bytes(b"kernel\n")
    return root


class TestLayer:
    def test_the_digest_is_of_the_uncompressed_tar(self, rootfs: Path, tmp_path: Path) -> None:
        """It goes into the config's `rootfs.diff_ids`, which is defined over the *uncompressed*
        layer. Digesting the gzip instead yields a config the registry accepts and that no runtime
        can then verify against the layer it pulled."""
        layer = tmp_path / "layer.tar.gz"

        digest = write_layer(rootfs, layer)

        expected = hashlib.sha256(gzip.decompress(layer.read_bytes())).hexdigest()
        assert digest == f"sha256:{expected}"

    def test_the_layer_contains_the_rootfs(self, rootfs: Path, tmp_path: Path) -> None:
        layer = tmp_path / "layer.tar.gz"

        write_layer(rootfs, layer)

        with tarfile.open(fileobj=io.BytesIO(gzip.decompress(layer.read_bytes()))) as tar:
            names = set(tar.getnames())
        assert "./usr/bin/hello" in names
        assert "./etc/hostname" in names

    def test_the_same_rootfs_produces_the_same_bytes(self, rootfs: Path, tmp_path: Path) -> None:
        """`mtime=0` on the gzip wrapper: re-pushing an unchanged image should be a no-op the
        registry dedupes, not a fresh blob every time."""
        first, second = tmp_path / "a.tar.gz", tmp_path / "b.tar.gz"

        digest_a = write_layer(rootfs, first)
        digest_b = write_layer(rootfs, second)

        assert digest_a == digest_b
        assert first.read_bytes() == second.read_bytes()
