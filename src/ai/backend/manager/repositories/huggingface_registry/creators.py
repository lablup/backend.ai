"""CreatorSpec implementations for HuggingFace registry domain."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from typing_extensions import override

from ai.backend.manager.models.huggingface_registry import HuggingFaceRegistryRow
from ai.backend.manager.repositories.base import CreatorSpec


@dataclass
class HuggingFaceRegistryCreatorSpec(CreatorSpec[HuggingFaceRegistryRow]):
    """CreatorSpec for HuggingFace registry creation."""

    url: str
    token: Optional[str] = None

    @override
    def build_row(self) -> HuggingFaceRegistryRow:
        return HuggingFaceRegistryRow(
            url=self.url,
            token=self.token,
        )
