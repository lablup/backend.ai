import enum
from typing import Dict

import attr


@attr.define(slots=True)
class CliContextInfo:
    info: Dict = attr.field()


class ExitCode(enum.Enum):
    OK = 0
    FAILURE = 1
    TIMEOUT = 2
    INVALID_ARGUMENT = 3
