from __future__ import annotations

import hashlib
import json

import pytest

from ai.backend.agent.containerd.client import ImageTarget
from ai.backend.agent.containerd.image import (
    chain_id,
    parse_image_config,
    resolve_image,
    select_manifest_digest,
)
from ai.backend.agent.errors.containerd import ContainerdImageInvalid, ContainerdImageNotFound

from .fakes import FakeContainerd

INDEX_TYPE = "application/vnd.oci.image.index.v1+json"


class TestChainId:
    def test_single_layer_is_its_diff_id(self) -> None:
        assert chain_id(["sha256:aa"]) == "sha256:aa"

    def test_layers_are_chained_by_sha256(self) -> None:
        expected = "sha256:" + hashlib.sha256(b"sha256:aa sha256:bb").hexdigest()
        assert chain_id(["sha256:aa", "sha256:bb"]) == expected

    def test_three_layers_chain_the_previous_chain(self) -> None:
        second = "sha256:" + hashlib.sha256(b"sha256:aa sha256:bb").hexdigest()
        third = "sha256:" + hashlib.sha256(f"{second} sha256:cc".encode()).hexdigest()
        assert chain_id(["sha256:aa", "sha256:bb", "sha256:cc"]) == third

    def test_no_layers_is_invalid(self) -> None:
        with pytest.raises(ContainerdImageInvalid):
            chain_id([])


class TestSelectManifest:
    index = {
        "manifests": [
            {"digest": "sha256:arm", "platform": {"os": "linux", "architecture": "arm64"}},
            {"digest": "sha256:amd", "platform": {"os": "linux", "architecture": "amd64"}},
            {"digest": "sha256:win", "platform": {"os": "windows", "architecture": "amd64"}},
        ]
    }

    def test_machine_names_map_to_go_architectures(self) -> None:
        assert select_manifest_digest(self.index, "x86_64") == "sha256:amd"
        assert select_manifest_digest(self.index, "aarch64") == "sha256:arm"

    def test_missing_platform_is_invalid(self) -> None:
        with pytest.raises(ContainerdImageInvalid, match="riscv64"):
            select_manifest_digest(self.index, "riscv64")


class TestParseImageConfig:
    def test_runtime_config_is_read(self) -> None:
        resolved = parse_image_config({
            "rootfs": {"diff_ids": ["sha256:aa"]},
            "config": {
                "Env": ["PATH=/bin"],
                "WorkingDir": "/work",
                "Entrypoint": ["/e"],
                "Cmd": ["run"],
                "User": "1000",
                "Labels": {"k": "v"},
            },
        })

        assert resolved.chain_id == "sha256:aa"
        assert resolved.env == ("PATH=/bin",)
        assert resolved.working_dir == "/work"
        assert resolved.entrypoint == ("/e",)
        assert resolved.cmd == ("run",)
        assert resolved.user == "1000"
        assert resolved.labels == {"k": "v"}

    def test_absent_runtime_config_defaults_to_empty(self) -> None:
        resolved = parse_image_config({"rootfs": {"diff_ids": ["sha256:aa"]}})

        assert resolved.env == ()
        assert resolved.working_dir == ""
        assert resolved.labels == {}


class TestResolveImage:
    async def test_single_manifest_image(self, fake: FakeContainerd) -> None:
        fake.add_image("img:1", diff_ids=["sha256:aa", "sha256:bb"], env=["A=1"])

        resolved = await resolve_image(fake, "img:1", "x86_64")

        assert resolved.chain_id == chain_id(["sha256:aa", "sha256:bb"])
        assert resolved.env == ("A=1",)

    async def test_index_image_follows_the_platform_manifest(self, fake: FakeContainerd) -> None:
        fake.blobs["sha256:index"] = json.dumps({
            "manifests": [
                {"digest": "sha256:m-arm", "platform": {"os": "linux", "architecture": "arm64"}},
                {"digest": "sha256:m-amd", "platform": {"os": "linux", "architecture": "amd64"}},
            ]
        }).encode()
        for arch, diff in (("arm", "sha256:11"), ("amd", "sha256:22")):
            fake.blobs[f"sha256:m-{arch}"] = json.dumps({
                "config": {"digest": f"sha256:c-{arch}"}
            }).encode()
            fake.blobs[f"sha256:c-{arch}"] = json.dumps({"rootfs": {"diff_ids": [diff]}}).encode()
        fake.images["img:1"] = ImageTarget("sha256:index", INDEX_TYPE)

        assert (await resolve_image(fake, "img:1", "aarch64")).chain_id == "sha256:11"
        assert (await resolve_image(fake, "img:1", "x86_64")).chain_id == "sha256:22"

    async def test_missing_image_is_a_typed_error(self) -> None:
        with pytest.raises(ContainerdImageNotFound):
            await resolve_image(FakeContainerd(), "absent:1", "x86_64")

    async def test_manifest_without_config_is_invalid(self, fake: FakeContainerd) -> None:
        fake.blobs["sha256:manifest"] = b"{}"
        fake.images["img:1"] = ImageTarget(
            "sha256:manifest", "application/vnd.oci.image.manifest.v1+json"
        )

        with pytest.raises(ContainerdImageInvalid, match="config"):
            await resolve_image(fake, "img:1", "x86_64")

    async def test_non_json_blob_is_invalid(self, fake: FakeContainerd) -> None:
        fake.blobs["sha256:manifest"] = b"not json"
        fake.images["img:1"] = ImageTarget(
            "sha256:manifest", "application/vnd.oci.image.manifest.v1+json"
        )

        with pytest.raises(ContainerdImageInvalid, match="JSON"):
            await resolve_image(fake, "img:1", "x86_64")
