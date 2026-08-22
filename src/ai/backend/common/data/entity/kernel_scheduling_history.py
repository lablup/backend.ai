from typing import NewType
from uuid import UUID

__all__ = ("KernelSchedulingHistoryID",)

KernelSchedulingHistoryID = NewType("KernelSchedulingHistoryID", UUID)
