"""Every registered kind has an idempotence test in its kind directory."""

from __future__ import annotations

import re
from pathlib import Path

from ai.backend.manager.seed.factory import create_seed_kind_registry
from ai.backend.manager.seed.types import SeedKind


def test_every_registered_kind_has_an_idempotence_test() -> None:
    registered = {kind.name for kind in create_seed_kind_registry().ordered()}
    tested: set[SeedKind] = set()
    for path in Path(__file__).parent.glob("*/test_idempotence.py"):
        tested.update(SeedKind[name] for name in re.findall(r"SeedKind\.(\w+)", path.read_text()))
    assert tested == registered
