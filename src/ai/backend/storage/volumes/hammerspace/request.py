from __future__ import annotations

from dataclasses import dataclass


@dataclass
class CreateShareParams:
    name: str
    path: str
    create_path: bool = True
    validate_only: bool = False

    def query(self) -> dict[str, str]:
        return {
            "create-path": "true" if self.create_path else "false",
            "validate-only": "true" if self.validate_only else "false",
        }

    def body(self) -> dict[str, str]:
        return {
            "name": self.name,
            "path": self.path,
        }
