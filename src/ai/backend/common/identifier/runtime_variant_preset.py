from typing import NewType
from uuid import UUID

__all__ = ("RuntimeVariantPresetID",)


RuntimeVariantPresetID = NewType("RuntimeVariantPresetID", UUID)
