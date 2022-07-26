from dataclasses import dataclass
from typing import Optional

PeerId = str


@dataclass
class CommandResponse:
    success: bool
    redirect: Optional[str] = None
