from typing import Dict

import attr


@attr.define(slots=True)
class CliContextInfo:
    info: Dict = attr.field()
