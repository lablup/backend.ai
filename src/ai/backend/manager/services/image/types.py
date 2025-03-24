from dataclasses import dataclass
from typing import Optional


@dataclass
class ResourceLimitInput:
    key: str
    min: Optional[str] = None
    max: Optional[str] = None


@dataclass
class KVPairInput:
    key: str
    value: str


@dataclass
class ImageRefData:
    name: str
    registry: str
    architecture: str
