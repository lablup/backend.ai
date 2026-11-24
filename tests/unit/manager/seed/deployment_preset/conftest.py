from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml

# Deployment preset files written for the tests, one preset per file. `vllm-small` states
# every field; `minimal` leaves the optional ones to their defaults.
_DEPLOYMENT_PRESETS: dict[str, dict[str, Any]] = {
    "vllm-small.yaml": {
        "id": "0198a5a0-0000-7000-8000-00000000f001",
        "runtime_variant_id": "0198a5a0-0000-7000-8000-00000000b001",
        "name": "vllm-small",
        "description": "vLLM on one GPU",
        "image_id": "0198a5a0-0000-7000-8000-00000000f101",
        "model_definition": {"models": [{"service": {"port": 8000}}]},
        "resource_slots": {"cpu": 2, "mem": 4294967296},
        "resource_opts": [{"name": "shmem", "value": "1g"}],
        "cluster_mode": "single-node",
        "cluster_size": 1,
        "startup_command": "vllm serve",
        "bootstrap_script": "pip install vllm",
        "environ": {"HF_HOME": "/models"},
        "runtime_variant_preset_values": [
            {"preset_id": "0198a5a0-0000-7000-8000-00000000f201", "value": "0.9"}
        ],
        "open_to_public": True,
        "replica_count": 2,
        "revision_history_limit": 5,
        "deployment_strategy": "BLUE_GREEN",
        "deployment_strategy_spec": {"auto_promote": True},
    },
    "minimal.yaml": {
        "id": "0198a5a0-0000-7000-8000-00000000f002",
        "runtime_variant_id": "0198a5a0-0000-7000-8000-00000000b001",
        "name": "minimal",
        "image_id": "0198a5a0-0000-7000-8000-00000000f101",
    },
}


@pytest.fixture
def deployment_preset_seed_dir(resource_slot_type_seed_dir: Path) -> Path:
    """The `resource_slot_type` directory plus one `deployment_preset` file per preset, so
    the slot names the presets state are registered first."""
    for file_name, preset in _DEPLOYMENT_PRESETS.items():
        (resource_slot_type_seed_dir / file_name).write_text(
            yaml.safe_dump({"kind": "deployment_preset", "version": 1, "items": [preset]})
        )
    return resource_slot_type_seed_dir


@pytest.fixture
def vllm_small_preset_id() -> str:
    return str(_DEPLOYMENT_PRESETS["vllm-small.yaml"]["id"])


@pytest.fixture
def minimal_preset_id() -> str:
    return str(_DEPLOYMENT_PRESETS["minimal.yaml"]["id"])
