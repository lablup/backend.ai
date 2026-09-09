"""What every domain scenario module needs: a runner bound to the domain's wiring.

The rows themselves stay in the test modules beside the behaviour they describe. Only
the runner is shared, which is what a conftest is for.
"""

from __future__ import annotations

from typing import Any

import pytest
from bai_kit.manager.config import base_config_dict
from bai_kit.manager.db import TemplateDatabase
from bai_kit.manager.monitors import ActionRecorder
from bai_kit.manager.typed_runner import TypedRunner
from bai_kit.manager.wiring.domain import domain_wiring


@pytest.fixture
def run(
    world_template: TemplateDatabase,
    test_db: str,
    engine: Any,
    recorder: ActionRecorder,
) -> TypedRunner:
    return TypedRunner(
        wiring=domain_wiring,
        engine=engine,
        world=world_template.world,
        base_config=base_config_dict(world_template.addr, test_db, None),
        recorder=recorder,
    )
