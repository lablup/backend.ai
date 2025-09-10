# ruff: noqa: E402
from __future__ import annotations

import attrs

from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.services.processors import Processors


@attrs.define(auto_attribs=True, slots=True)
class StrawberryGQLContext:
    processors: Processors
    config_provider: ManagerConfigProvider
