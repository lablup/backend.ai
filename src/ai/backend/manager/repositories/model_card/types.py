"""Types for model card repository operations."""

from __future__ import annotations

from dataclasses import dataclass

from ai.backend.manager.data.deployment_revision_preset.types import DeploymentRevisionPresetData

__all__ = ("AvailablePresetsSearchResult",)


@dataclass
class AvailablePresetsSearchResult:
    """Result from searching available presets for a model card."""

    items: list[DeploymentRevisionPresetData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool
