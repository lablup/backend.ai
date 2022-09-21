from __future__ import annotations

import enum
from typing import TYPE_CHECKING

import attr

if TYPE_CHECKING:
    from ..config import APIConfig
    from ..output import BaseOutputHandler


class OutputMode(enum.Enum):
    CONSOLE = "console"
    JSON = "json"


@attr.define(slots=True)
class CLIContext:
    api_config: APIConfig = attr.field()
    output_mode: OutputMode = attr.field()
    output: BaseOutputHandler = attr.field(default=None)
