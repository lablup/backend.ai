"""Search conditions kept only until the filters they serve are removed.

`ModelCardV2Filter.storageHost` narrows model cards by the `host` of the vfolder they are
built on. A vfolder is another entity, so the EXISTS has no place to check the caller's
permission on it, which is why the declaration rules keep it out of `nested`. It shipped
in 26.4.2, so it cannot be dropped outright, and `used_by: { vfolder }` is the route off
it.

Deleting this module completes the model card's migration, as deleting `conditions.py`
and `orders.py` did.
"""

from __future__ import annotations

from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.model_card.row import ModelCardRow
from ai.backend.manager.models.specs.conditions.string import StringConditions
from ai.backend.manager.models.specs.search.correlation import ToOneCorrelation
from ai.backend.manager.models.vfolder.row import VFolderRow

__all__ = ("ModelCardDeprecatedSearch",)


class _StorageHostFilter:
    """The host of the vfolder a model card names as its model."""

    _correlation = ToOneCorrelation(VFolderRow, ModelCardRow, VFolderRow.id == ModelCardRow.vfolder)

    conditions = StringConditions(VFolderRow.host)

    def matching(self, conditions: list[QueryCondition]) -> QueryCondition:
        """The cards whose vfolder meets every condition."""
        return self._correlation.has(conditions)


class ModelCardDeprecatedSearch:
    storage_host = _StorageHostFilter()
