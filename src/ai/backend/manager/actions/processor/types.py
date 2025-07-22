from dataclasses import dataclass

from ..action.base import (
    BaseActionResultMeta,
)


@dataclass
class ProcessResult:
    meta: BaseActionResultMeta
