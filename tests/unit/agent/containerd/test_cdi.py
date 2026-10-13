from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
import yaml

from ai.backend.agent.containerd.cdi import resolve_cdi_devices
from ai.backend.agent.errors.containerd import HostConfigNotTranslatable

SPEC: dict[str, Any] = {
    "cdiVersion": "0.6.0",
    "kind": "vendor.com/gpu",
    "containerEdits": {"env": ["SPEC_LEVEL=1"]},
    "devices": [
        {
            "name": "0",
            "containerEdits": {
                "env": ["DEV=0"],
                "deviceNodes": [
                    {"path": "/dev/gpu0", "hostPath": "/dev/host-gpu0", "permissions": "rw"}
                ],
            },
        },
        {"name": "1", "containerEdits": {"deviceNodes": [{"path": "/dev/gpu1"}]}},
    ],
}


def _write(directory: Path, name: str, spec: dict[str, Any]) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    text = yaml.safe_dump(spec) if name.endswith((".yaml", ".yml")) else json.dumps(spec)
    (directory / name).write_text(text)


class TestResolve:
    @pytest.mark.parametrize("filename", ["gpu.yaml", "gpu.json", "gpu.yml"])
    def test_spec_formats_resolve(self, tmp_path: Path, filename: str) -> None:
        _write(tmp_path, filename, SPEC)

        edits = resolve_cdi_devices("cuda", ["vendor.com/gpu=0"], [tmp_path])

        assert edits.env == ("SPEC_LEVEL=1", "DEV=0")
        assert [(n.path, n.host_path, n.permissions) for n in edits.device_nodes] == [
            ("/dev/gpu0", "/dev/host-gpu0", "rw")
        ]

    def test_spec_level_edits_apply_once(self, tmp_path: Path) -> None:
        _write(tmp_path, "gpu.yaml", SPEC)

        edits = resolve_cdi_devices("cuda", ["vendor.com/gpu=0", "vendor.com/gpu=1"], [tmp_path])

        assert edits.env.count("SPEC_LEVEL=1") == 1
        node = edits.device_nodes[1]
        assert (node.path, node.host_path, node.permissions) == ("/dev/gpu1", "/dev/gpu1", "rwm")

    def test_repeated_device_name_is_deduplicated(self, tmp_path: Path) -> None:
        _write(tmp_path, "gpu.yaml", SPEC)

        edits = resolve_cdi_devices("cuda", ["vendor.com/gpu=0", "vendor.com/gpu=0"], [tmp_path])

        assert len(edits.device_nodes) == 1

    def test_later_spec_dir_is_searched(self, tmp_path: Path) -> None:
        _write(tmp_path / "var-run", "gpu.yaml", SPEC)

        edits = resolve_cdi_devices(
            "cuda", ["vendor.com/gpu=1"], [tmp_path / "etc", tmp_path / "var-run"]
        )

        assert [n.path for n in edits.device_nodes] == ["/dev/gpu1"]

    def test_node_fields_are_parsed(self, tmp_path: Path) -> None:
        spec = {
            "kind": "v.com/c",
            "devices": [
                {
                    "name": "a",
                    "containerEdits": {
                        "deviceNodes": [
                            {
                                "path": "/dev/a",
                                "type": "c",
                                "major": 1,
                                "minor": 2,
                                "fileMode": 432,
                                "uid": 3,
                                "gid": 4,
                            }
                        ]
                    },
                }
            ],
        }
        _write(tmp_path, "a.json", spec)

        (node,) = resolve_cdi_devices("p", ["v.com/c=a"], [tmp_path]).device_nodes

        assert (node.type, node.major, node.minor) == ("c", 1, 2)
        assert (node.file_mode, node.uid, node.gid) == (432, 3, 4)


class TestFailClosed:
    def test_missing_dirs_have_no_specs(self, tmp_path: Path) -> None:
        with pytest.raises(HostConfigNotTranslatable, match="no CDI spec"):
            resolve_cdi_devices("cuda", ["vendor.com/gpu=0"], [tmp_path / "absent"])

    def test_unknown_kind_raises(self, tmp_path: Path) -> None:
        _write(tmp_path, "gpu.yaml", SPEC)

        with pytest.raises(HostConfigNotTranslatable, match=r"other\.com/gpu=0"):
            resolve_cdi_devices("cuda", ["other.com/gpu=0"], [tmp_path])

    def test_unknown_device_raises(self, tmp_path: Path) -> None:
        _write(tmp_path, "gpu.yaml", SPEC)

        with pytest.raises(HostConfigNotTranslatable, match=r"vendor\.com/gpu=9"):
            resolve_cdi_devices("cuda", ["vendor.com/gpu=9"], [tmp_path])

    @pytest.mark.parametrize("name", ["gpu=0", "vendor.com/gpu", "0", "", "a/b/c=0"])
    def test_malformed_name_raises(self, tmp_path: Path, name: str) -> None:
        _write(tmp_path, "gpu.yaml", SPEC)

        with pytest.raises(HostConfigNotTranslatable, match="malformed"):
            resolve_cdi_devices("cuda", [name], [tmp_path])

    def test_duplicate_definition_raises(self, tmp_path: Path) -> None:
        _write(tmp_path / "etc", "a.yaml", SPEC)
        _write(tmp_path / "var", "b.yaml", SPEC)

        with pytest.raises(HostConfigNotTranslatable, match="defined in"):
            resolve_cdi_devices("cuda", ["vendor.com/gpu=0"], [tmp_path / "etc", tmp_path / "var"])

    def test_unparsable_file_raises(self, tmp_path: Path) -> None:
        (tmp_path / "broken.yaml").write_text("kind: [unclosed")

        with pytest.raises(HostConfigNotTranslatable, match="unreadable"):
            resolve_cdi_devices("cuda", ["vendor.com/gpu=0"], [tmp_path])

    def test_non_spec_file_raises(self, tmp_path: Path) -> None:
        (tmp_path / "list.yaml").write_text("- a\n- b\n")

        with pytest.raises(HostConfigNotTranslatable, match="invalid CDI spec"):
            resolve_cdi_devices("cuda", ["vendor.com/gpu=0"], [tmp_path])

    @pytest.mark.parametrize(
        "edit",
        [
            {"mounts": [{"hostPath": "/a", "containerPath": "/a"}]},
            {"hooks": [{"hookName": "createContainer", "path": "/bin/x"}]},
            {"additionalGids": [1]},
            {"intelRdt": {}},
        ],
    )
    def test_unsupported_edits_raise(self, tmp_path: Path, edit: dict[str, Any]) -> None:
        spec = {"kind": "v.com/c", "devices": [{"name": "a", "containerEdits": edit}]}
        _write(tmp_path, "a.yaml", spec)

        with pytest.raises(HostConfigNotTranslatable, match="unsupported CDI container edit"):
            resolve_cdi_devices("cuda", ["v.com/c=a"], [tmp_path])

    def test_unsupported_spec_level_edit_raises(self, tmp_path: Path) -> None:
        spec = {
            "kind": "v.com/c",
            "containerEdits": {"mounts": []},
            "devices": [{"name": "a"}],
        }
        _write(tmp_path, "a.yaml", spec)

        with pytest.raises(HostConfigNotTranslatable, match="mounts"):
            resolve_cdi_devices("cuda", ["v.com/c=a"], [tmp_path])

    def test_unknown_node_field_raises(self, tmp_path: Path) -> None:
        edits = {"deviceNodes": [{"path": "/dev/a", "flags": 1}]}
        spec = {"kind": "v.com/c", "devices": [{"name": "a", "containerEdits": edits}]}
        _write(tmp_path, "a.yaml", spec)

        with pytest.raises(HostConfigNotTranslatable, match="flags"):
            resolve_cdi_devices("cuda", ["v.com/c=a"], [tmp_path])

    @pytest.mark.parametrize(
        "node",
        [
            {"path": "dev/a"},
            {"path": "/dev/a", "hostPath": "dev/a"},
            {"path": "dev/a", "hostPath": "/dev/a"},
        ],
    )
    def test_relative_node_paths_raise(self, tmp_path: Path, node: dict[str, Any]) -> None:
        edits = {"deviceNodes": [node]}
        spec = {"kind": "v.com/c", "devices": [{"name": "a", "containerEdits": edits}]}
        _write(tmp_path, "a.yaml", spec)

        with pytest.raises(HostConfigNotTranslatable, match="must be absolute"):
            resolve_cdi_devices("cuda", ["v.com/c=a"], [tmp_path])

    def test_error_names_plugin(self, tmp_path: Path) -> None:
        with pytest.raises(HostConfigNotTranslatable) as exc:
            resolve_cdi_devices("rebellions", ["v.com/c=a"], [tmp_path])

        assert exc.value.extra_data == {
            "plugin": "rebellions",
            "key": "HostConfig.DeviceRequests",
        }
