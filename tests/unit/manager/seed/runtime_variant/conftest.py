from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml

# Runtime variant files written for the tests, one variant per file. `vllm` states every
# field; `custom` leaves the optional ones to their defaults.
_RUNTIME_VARIANTS: dict[str, dict[str, Any]] = {
    "vllm.yaml": {
        "id": "0198a5a0-0000-7000-8000-00000000b001",
        "name": "vllm",
        "description": "vLLM",
        "reads_vfolder_config_files": True,
        "default_model_definition": {
            "models": [
                {"name": "vllm-model", "service": {"port": 8000}},
            ]
        },
    },
    "custom.yaml": {
        "id": "0198a5a0-0000-7000-8000-00000000b002",
        "name": "custom",
    },
}


@pytest.fixture
def runtime_variant_seed_dir(tmp_path: Path) -> Path:
    """A directory of runtime variant seed files, the shape `seeds/manager/runtime_variant/`
    has."""
    directory = tmp_path / "runtime_variant"
    directory.mkdir()
    for file_name, variant in _RUNTIME_VARIANTS.items():
        (directory / file_name).write_text(
            yaml.safe_dump({"kind": "runtime_variant", "version": 1, "items": [variant]})
        )
    return directory


@pytest.fixture
def vllm_variant_id() -> str:
    return str(_RUNTIME_VARIANTS["vllm.yaml"]["id"])
