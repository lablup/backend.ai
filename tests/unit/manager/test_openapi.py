from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from ai.backend.manager.openapi import main


class TestOpenAPISpecCommand:
    @pytest.fixture
    def spec_output_file(self, tmp_path: Path) -> Path:
        return tmp_path / "openapi.json"

    def test_output_option_writes_the_spec_to_the_file(self, spec_output_file: Path) -> None:
        result = CliRunner().invoke(main, ["--output", str(spec_output_file)])

        assert result.exit_code == 0, result.output
        assert json.loads(spec_output_file.read_text())["paths"]
