from typing import NewType
from uuid import UUID

__all__ = ("ImageID",)


ImageID = NewType("ImageID", UUID)
