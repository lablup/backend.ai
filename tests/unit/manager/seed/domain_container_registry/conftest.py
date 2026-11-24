from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml

_REGISTRIES: list[dict[str, Any]] = [
    {
        "id": "0198a5a0-0000-7000-8000-00000000c001",
        "registry_name": "cr.backend.ai",
        "url": "https://cr.backend.ai",
        "type": "harbor2",
        "project": "stable",
    },
    {
        "id": "0198a5a0-0000-7000-8000-00000000c002",
        "registry_name": "cr.backend.ai",
        "url": "https://cr.backend.ai",
        "type": "harbor2",
        "project": "community",
    },
]


@pytest.fixture
def domain_container_registry_seed_dir(domain_seed_dir: Path) -> Path:
    """The domain directory plus two registries the `default` domain is allowed to use."""
    (domain_seed_dir / "registries.yaml").write_text(
        yaml.safe_dump({"kind": "container_registry", "version": 1, "items": _REGISTRIES})
    )
    allowed = [
        {"domain_id": "0198a5a0-0000-7000-8000-00000000d001", "registry_id": registry["id"]}
        for registry in _REGISTRIES
    ]
    (domain_seed_dir / "allowed-registries.yaml").write_text(
        yaml.safe_dump({"kind": "domain_container_registry", "version": 1, "items": allowed})
    )
    return domain_seed_dir
