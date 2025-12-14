"""CreatorSpec implementations for HuggingFace registry domain."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

from typing_extensions import override

from ai.backend.manager.repositories.base import CreatorSpec

if TYPE_CHECKING:
    from ai.backend.manager.models.huggingface_registry import HuggingFaceRegistryRow


@dataclass
class HuggingFaceRegistryCreatorSpec(CreatorSpec["HuggingFaceRegistryRow"]):
    """CreatorSpec for HuggingFace registry creation."""

    url: str
    token: Optional[str] = None

    @override
    def build_row(self) -> HuggingFaceRegistryRow:
        from ai.backend.manager.models.huggingface_registry import HuggingFaceRegistryRow

        return HuggingFaceRegistryRow(
            url=self.url,
            token=self.token,
        )
