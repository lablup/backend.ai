"""The field shape paired with the ops backing, kept here rather than beside the other
pairings: the ops package must not import the field bases, or the two form a cycle."""

from abc import ABC
from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier, FieldData, FieldIdentifier
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.field.base import BaseSingleFieldAction
from ai.backend.manager.actions.v2.field.bulk_base import BasePartialBulkFieldAction
from ai.backend.manager.actions.v2.ops.base import (
    FieldGetOpsAction,
    FieldPartialBulkPurgeOpsAction,
    FieldPurgeOpsAction,
    UpdateOpsAction,
)
from ai.backend.manager.models.base import Base

__all__ = (
    "GetFieldOpsAction",
    "UpdateFieldOpsAction",
    "DeleteFieldOpsAction",
    "RestoreFieldOpsAction",
    "PurgeFieldOpsAction",
    "PartialBulkPurgeFieldOpsAction",
)


class GetFieldOpsAction[
    TFieldID: FieldIdentifier,
    TOwnerID: EntityIdentifier,
    TRow: Base,
    TData: FieldData,
](BaseSingleFieldAction[TFieldID, TOwnerID], FieldGetOpsAction[TRow, TData], ABC):
    """A read of one field row, authorized against the entity owning it."""

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET


class UpdateFieldOpsAction[
    TFieldID: FieldIdentifier,
    TOwnerID: EntityIdentifier,
    TRow: Base,
    TData: FieldData,
](BaseSingleFieldAction[TFieldID, TOwnerID], UpdateOpsAction[TRow, TData], ABC):
    """A write to one field row, authorized against the entity owning it."""

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE


class DeleteFieldOpsAction[
    TFieldID: FieldIdentifier,
    TOwnerID: EntityIdentifier,
    TRow: Base,
    TData: FieldData,
](BaseSingleFieldAction[TFieldID, TOwnerID], UpdateOpsAction[TRow, TData], ABC):
    """A soft delete of one field row; the updater writes the lifecycle column alone."""

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE


class RestoreFieldOpsAction[
    TFieldID: FieldIdentifier,
    TOwnerID: EntityIdentifier,
    TRow: Base,
    TData: FieldData,
](BaseSingleFieldAction[TFieldID, TOwnerID], UpdateOpsAction[TRow, TData], ABC):
    """The reverse transition of a field row's soft delete."""

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE


class PurgeFieldOpsAction[
    TFieldID: FieldIdentifier,
    TOwnerID: EntityIdentifier,
    TRow: Base,
    TData: FieldData,
](BaseSingleFieldAction[TFieldID, TOwnerID], FieldPurgeOpsAction[TRow, TData], ABC):
    """A hard delete of a field row, authorized against its owner."""

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE


class PartialBulkPurgeFieldOpsAction[
    TFieldID: FieldIdentifier,
    TOwnerID: EntityIdentifier,
    TRow: Base,
    TData: FieldData,
](
    BasePartialBulkFieldAction[TFieldID, TOwnerID],
    FieldPartialBulkPurgeOpsAction[TFieldID, TRow, TData],
    ABC,
):
    """A hard delete over the field rows the caller named."""

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE
