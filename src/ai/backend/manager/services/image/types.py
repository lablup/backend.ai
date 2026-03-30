from dataclasses import dataclass


@dataclass
class ImageRefData:
    name: str
    registry: str
    architecture: str
