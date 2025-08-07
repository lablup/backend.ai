# ruff: noqa: E402
from __future__ import annotations

import attrs

from ai.backend.common.data.user.types import UserData


@attrs.define(auto_attribs=True, slots=True)
class StrawberryGQLContext:
    user: UserData
