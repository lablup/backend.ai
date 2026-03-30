from dataclasses import dataclass
from typing import Self

from pydantic import BaseModel

from ai.backend.common.arch import arch_name_aliases


class InstalledImageInfo(BaseModel):
    """ "
    Information about an installed image on an agent.
    Attributes:
        canonical (str): The canonical name of the image.
        digest (str): The digest of the image.
        architecture (str): The architecture of the image. Supported values are 'x86', 'x86_64', 'aarch64'.
    """

    canonical: str
    digest: str
    architecture: str

    @classmethod
    def from_inspect_result(cls, canonical: str, inspect_result: dict[str, str]) -> Self:
        architecture = inspect_result.get("Architecture", "x86_64")
        architecture_alias = arch_name_aliases.get(architecture, architecture)
        return cls(
            canonical=canonical,
            digest=inspect_result["Id"],
            architecture=architecture_alias,
        )


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
