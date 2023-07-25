from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import NewType

from .exception import InvalidServiceName

ServiceVersion = NewType("ServiceVersion", str)


@dataclass(frozen=True)
class ServiceName:
    name: str
    version: ServiceVersion
    distro: str
    architecture: str

    def __str__(self) -> str:
        return f"{self.name}:{self.version}:{self.distro}:{self.architecture}"

    @classmethod
    def from_str(cls, value: str) -> ServiceName:
        try:
            name, version, distro, arch = value.split(":")
        except ValueError:
            raise InvalidServiceName(f"Service path `{value}` is invalid.")
        return cls(name, ServiceVersion(version), distro, arch)

    @property
    def candidate(self) -> CandidateServiceName:
        return CandidateServiceName(self.name, self.distro, self.architecture)


@dataclass(frozen=True)
class CandidateServiceName:
    name: str
    distro: str
    architecture: str

    def __str__(self) -> str:
        return f"{self.name}:{self.distro}:{self.architecture}"


@dataclass
class ServicePath:
    parent_path: Path
    service_name: ServiceName

    def __str__(self) -> str:
        return str(Path(self.parent_path, str(self.service_name)))

    @property
    def config_file(self) -> Path:
        return Path(self.parent_path, "app-config.json")

    @property
    def def_file(self) -> Path:
        scoped_file = Path(self.parent_path, str(self.service_name), "service-def.json")
        if scoped_file.exists():
            return scoped_file
        return Path(self.parent_path, "service-def.json")
