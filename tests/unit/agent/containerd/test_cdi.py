"""Unit tests for the CDI resolver/injector (BEP-1062)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from ai.backend.agent.containerd.runtime.cdi import (
    inject_cdi_devices,
    load_device_edits,
)


def _write_spec(dir_: Path) -> None:
    spec: dict[str, Any] = {
        "cdiVersion": "0.5.0",
        "kind": "nvidia.com/gpu",
        # Spec-level edits apply to every device. Explicit major/minor so tests need no /dev nodes.
        "containerEdits": {
            "deviceNodes": [{"path": "/dev/nvidiactl", "major": 195, "minor": 255}],
            "mounts": [
                {
                    "hostPath": "/usr/lib/libcuda.so.1",
                    "containerPath": "/usr/lib/libcuda.so.1",
                    "options": ["ro", "nosuid", "nodev", "bind"],
                }
            ],
            "hooks": [
                {
                    "hookName": "createContainer",
                    "path": "/usr/bin/nvidia-cdi-hook",
                    "args": ["nvidia-cdi-hook", "update-ldcache"],
                }
            ],
            "env": ["NVIDIA_VISIBLE_DEVICES=void"],
        },
        "devices": [
            {
                "name": "0",
                "containerEdits": {
                    "deviceNodes": [{"path": "/dev/nvidia0", "major": 195, "minor": 0}]
                },
            },
        ],
    }
    (dir_ / "nvidia.yaml").write_text(yaml.safe_dump(spec))


class TestLoad:
    def test_merges_spec_level_and_device_edits(self, tmp_path: Path) -> None:
        _write_spec(tmp_path)
        edits = load_device_edits([str(tmp_path)])["nvidia.com/gpu=0"]
        paths = [dn["path"] for dn in edits["deviceNodes"]]
        assert paths == ["/dev/nvidiactl", "/dev/nvidia0"]  # spec-level first, then device

    def test_empty_when_no_specs(self, tmp_path: Path) -> None:
        assert load_device_edits([str(tmp_path)]) == {}


class TestInject:
    def _blank_spec(self) -> dict[str, Any]:
        return {"process": {"env": ["NVIDIA_VISIBLE_DEVICES=all"]}, "linux": {}, "mounts": []}

    def test_injects_devices_mounts_hooks_env(self, tmp_path: Path) -> None:
        _write_spec(tmp_path)
        spec = self._blank_spec()
        assert inject_cdi_devices(spec, ["nvidia.com/gpu=0"], dirs=[str(tmp_path)]) is True
        dev_paths = [d["path"] for d in spec["linux"]["devices"]]
        assert "/dev/nvidia0" in dev_paths and "/dev/nvidiactl" in dev_paths
        assert any(r["major"] == 195 and r["allow"] for r in spec["linux"]["resources"]["devices"])
        assert any(m["destination"] == "/usr/lib/libcuda.so.1" for m in spec["mounts"])
        assert spec["hooks"]["createContainer"][0]["path"].endswith("nvidia-cdi-hook")
        # env override: the CDI value replaces the image's baked-in NVIDIA_VISIBLE_DEVICES.
        assert "NVIDIA_VISIBLE_DEVICES=void" in spec["process"]["env"]
        assert "NVIDIA_VISIBLE_DEVICES=all" not in spec["process"]["env"]

    def test_unknown_device_returns_false_without_mutation(self, tmp_path: Path) -> None:
        _write_spec(tmp_path)
        spec = self._blank_spec()
        assert inject_cdi_devices(spec, ["nvidia.com/gpu=9"], dirs=[str(tmp_path)]) is False
        assert spec["linux"] == {}  # untouched on failure

    def test_no_specs_returns_false(self, tmp_path: Path) -> None:
        spec = self._blank_spec()
        assert inject_cdi_devices(spec, ["nvidia.com/gpu=0"], dirs=[str(tmp_path)]) is False

    def test_device_paths_deduplicated(self, tmp_path: Path) -> None:
        _write_spec(tmp_path)
        spec = self._blank_spec()
        # Two references pull the shared /dev/nvidiactl twice; it must appear once.
        inject_cdi_devices(spec, ["nvidia.com/gpu=0", "nvidia.com/gpu=0"], dirs=[str(tmp_path)])
        ctl = [d for d in spec["linux"]["devices"] if d["path"] == "/dev/nvidiactl"]
        assert len(ctl) == 1
