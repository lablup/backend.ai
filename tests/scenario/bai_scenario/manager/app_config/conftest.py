"""The merged app config adapter, assembled for one row."""

from __future__ import annotations

from typing import Any

import pytest
from bai_scenario.components.app_config import app_config_processors

from ai.backend.manager.actions.monitors import ActionMonitors
from ai.backend.manager.actions.v2.validators import ActionValidators as V2ActionValidators
from ai.backend.manager.api.adapters.app_config.adapter import AppConfigAdapter


@pytest.fixture
async def adapter(
    engine: Any,
    validators: V2ActionValidators,
    monitors: ActionMonitors,
) -> AppConfigAdapter:
    return AppConfigAdapter(app_config_processors(engine, validators, monitors))
