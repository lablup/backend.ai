from typing import NewType
from uuid import UUID

__all__ = ("RuntimeVariantID",)


RuntimeVariantID = NewType("RuntimeVariantID", UUID)
