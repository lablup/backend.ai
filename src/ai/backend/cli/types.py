import enum
from typing import Dict

import attr


@attr.define(slots=True)
class CliContextInfo:
    info: Dict = attr.field()


class ExitCode(enum.IntEnum):
    OK = 0
    FAILURE = 1  # generic failure
    INVALID_USAGE = 2  # wraps Click's UsageError
    OPERATION_TIMEOUT = 3  # timeout during operation
    INVALID_ARGUMENT = 4  # invalid argument while it's not UsageError
