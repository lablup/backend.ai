from dataclasses import dataclass
from typing import Self


@dataclass
class ScannedImage:
    canonical: str
    digest: str

    def to_dict(self) -> dict[str, str]:
        return {
            "canonical": self.canonical,
            "digest": self.digest,
        }

    @classmethod
    def from_dict(cls, data: dict[str, str]) -> Self:
        return cls(
            canonical=data["canonical"],
            digest=data["digest"],
        )
