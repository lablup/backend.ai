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

# Runtime variant preset files written for the tests, one file per variant. `max-model-len`
# states every field; `enforce-eager` leaves the optional ones to their defaults.
_RUNTIME_VARIANT_PRESETS: dict[str, list[dict[str, Any]]] = {
    "vllm.yaml": [
        {
            "id": "0198a5a0-0000-7000-8000-00000000d001",
            "runtime_variant_id": _RUNTIME_VARIANTS["vllm.yaml"]["id"],
            "name": "max-model-len",
            "description": "Maximum context length",
            "rank": 100,
            "preset_target": "args",
            "value_type": "int",
            "default_value": "4096",
            "key": "--max-model-len",
            "required": True,
            "added_version": "0.6",
            "deprecated_version": "1.0.0",
            "category": "model",
            "display_name": "Max model length",
            "ui_option": {"ui_type": "slider", "slider": {"min": 512, "max": 32768, "step": 512}},
        },
        {
            "id": "0198a5a0-0000-7000-8000-00000000d002",
            "runtime_variant_id": _RUNTIME_VARIANTS["vllm.yaml"]["id"],
            "name": "enforce-eager",
            "rank": 200,
            "preset_target": "args",
            "value_type": "flag",
            "key": "--enforce-eager",
        },
    ],
}


@pytest.fixture
def runtime_variant_preset_seed_dir(tmp_path: Path) -> Path:
    """A directory of runtime variant preset seed files, the shape
    `seeds/manager/runtime_variant_preset/` has."""
    directory = tmp_path / "runtime_variant_preset"
    directory.mkdir()
    for file_name, presets in _RUNTIME_VARIANT_PRESETS.items():
        (directory / file_name).write_text(
            yaml.safe_dump({"kind": "runtime_variant_preset", "version": 1, "items": presets})
        )
    return directory


@pytest.fixture
def max_model_len_preset_id() -> str:
    return str(_RUNTIME_VARIANT_PRESETS["vllm.yaml"][0]["id"])
