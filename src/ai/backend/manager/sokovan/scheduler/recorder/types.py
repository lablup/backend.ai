from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from ai.backend.common.types import SessionId


@dataclass
class ExecutionStep:
    """Represents a single execution step in the scheduler lifecycle."""

    phases: list[str]  # e.g., ["provisioner", "validator"], ["launcher", "prepare"]
    name: str  # e.g., "check_quota", "pull_image"
    status: str  # "started", "success", "failed"
    timestamp: datetime
    detail: Optional[str] = None


@dataclass
class PhaseDescriptor:
    """Descriptor for entering a phase (hierarchy grouping)."""

    session_id: SessionId
    name: str  # e.g., "provisioner", "validator", "launcher"


@dataclass
class StepDescriptor:
    """Descriptor for executing a step within a phase."""

    session_id: SessionId
    name: str  # e.g., "check_quota", "select_agent"
    success_detail: Optional[str] = None
