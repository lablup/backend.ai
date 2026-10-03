"""A file is loaded in the format its suffix names."""

from __future__ import annotations

from pathlib import Path

import pytest

from ai.backend.common.serde.exceptions import InvalidFileContent, UnsupportedFileFormat
from ai.backend.common.serde.loader import FileLoader
from ai.backend.common.serde.types import FileFormat

_EXPECTED = {"kind": "sample", "version": 1, "items": [{"name": "a", "tags": ["x", "y"]}]}
_SAME_CONTENT = {
    "seed.yaml": "kind: sample\nversion: 1\nitems:\n  - name: a\n    tags: [x, y]\n",
    "seed.yml": "kind: sample\nversion: 1\nitems:\n  - name: a\n    tags: [x, y]\n",
    "seed.json": '{"kind": "sample", "version": 1, "items": [{"name": "a", "tags": ["x", "y"]}]}',
    "seed.toml": 'kind = "sample"\nversion = 1\n\n[[items]]\nname = "a"\ntags = ["x", "y"]\n',
}


class TestFileFormat:
    @pytest.mark.parametrize(
        ("name", "expected"),
        [
            ("a.yaml", FileFormat.YAML),
            ("a.yml", FileFormat.YAML),
            ("a.json", FileFormat.JSON),
            ("a.toml", FileFormat.TOML),
            ("dir/A.YAML", FileFormat.YAML),
        ],
    )
    def test_the_suffix_names_the_format(self, name: str, expected: FileFormat) -> None:
        assert FileFormat.from_name(name) is expected

    @pytest.mark.parametrize("name", ["a.ini", "a.txt", "a", "a.json5"])
    def test_another_suffix_is_refused(self, name: str) -> None:
        with pytest.raises(UnsupportedFileFormat):
            FileFormat.from_name(name)

    def test_all_suffixes(self) -> None:
        assert FileFormat.all_suffixes() == {".yaml", ".yml", ".json", ".toml"}


class TestFileLoader:
    @pytest.mark.parametrize("name", sorted(_SAME_CONTENT))
    def test_every_format_loads_the_same_values(self, name: str) -> None:
        assert FileLoader().parse(name, _SAME_CONTENT[name]) == _EXPECTED

    @pytest.mark.parametrize(
        ("name", "text"),
        [
            ("a.yaml", "kind: [unclosed"),
            ("a.json", "{not json"),
            ("a.toml", "kind = "),
        ],
    )
    def test_unreadable_content_is_refused(self, name: str, text: str) -> None:
        with pytest.raises(InvalidFileContent):
            FileLoader().parse(name, text)

    def test_a_path_is_loaded_by_its_suffix(self, tmp_path: Path) -> None:
        path = tmp_path / "seed.toml"
        path.write_text(_SAME_CONTENT["seed.toml"])
        assert FileLoader().load(path) == _EXPECTED
