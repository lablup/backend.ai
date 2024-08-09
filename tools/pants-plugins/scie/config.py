# Copyright 2023 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).

from __future__ import annotations

import logging
from dataclasses import dataclass

import toml

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Config:
    lift: LiftConfig

    def __post_init__(self):
        if isinstance(self.lift, dict):
            logger.warning(f"LIFT: {self.lift}")
            object.__setattr__(self, "lift", LiftConfig(**self.lift))

    @classmethod
    def from_toml(cls, file_path):
        with open(file_path) as f:
            data = toml.load(f)
        return cls(**data)


@dataclass(frozen=True)
class LiftConfig:
    """
    This configuration is a subset of the configuration that can be found here:
    https://github.com/a-scie/lift/blob/main/science/model.py
    """

    name: str
    description: str
    platforms: list[str]
    interpreters: list[Interpreter]
    files: list[File]
    commands: list[Command]
    bindings: frozenset[Command] = frozenset()

    def __post_init__(self):
        if any(isinstance(i, dict) for i in self.interpreters):
            object.__setattr__(self, "interpreters", [Interpreter(**i) for i in self.interpreters])  # type: ignore
        if any(isinstance(f, dict) for f in self.files):
            object.__setattr__(self, "files", [File(**f) for f in self.files])  # type: ignore
        if any(isinstance(c, dict) for c in self.commands):
            object.__setattr__(self, "commands", [Command(**c) for c in self.commands])  # type: ignore
        if any(isinstance(b, dict) for b in self.bindings):
            object.__setattr__(self, "bindings", [Command(**b) for b in self.bindings])  # type: ignore


@dataclass(frozen=True)
class Interpreter:
    version: str
    id: str = "cpython"
    provider: str = "PythonBuildStandalone"
    release: str = "20240713"
    lazy: bool = False


@dataclass(frozen=True)
class File:
    name: str


@dataclass(frozen=True)
class Command:
    exe: str
    args: list[str]
    env: dict[str, str] | None = None
    name: str | None = None
    description: str | None = None
