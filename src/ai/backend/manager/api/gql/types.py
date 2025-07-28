# ruff: noqa: E402
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import attrs


@attrs.define(auto_attribs=True, slots=True)
class StrawberryGQLContext:
    user: Mapping[str, Any]  # TODO: express using typed dict
