from __future__ import annotations

import attrs


@attrs.define(slots=True)
class ProcResult:
    succeeded: bool = attrs.field()
    body: str = attrs.field()
