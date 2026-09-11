"""
Resource slot domain exceptions.
"""

from __future__ import annotations

from typing import override

from aiohttp import web

from ai.backend.common.data.entity.agent_resource import AgentResourceFieldType
from ai.backend.common.data.entity.resource_allocation import ResourceAllocationFieldType
from ai.backend.common.data.entity.resource_slot import ResourceSlotTypeEntityType
from ai.backend.common.exception import ErrorDetail
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.errors.base.entity import EntityError, EntityErrorCode
from ai.backend.manager.errors.base.field import FieldError, FieldErrorCode


class ResourceSlotTypeNotFound(EntityError, web.HTTPNotFound):
    """Raised when a requested resource slot type does not exist."""

    error_type = "https://api.backend.ai/probs/resource-slot-type-not-found"
    error_title = "Resource slot type not found."

    @override
    def entity_error_code(self) -> EntityErrorCode:
        return EntityErrorCode(
            ResourceSlotTypeEntityType(), ActionOperationType.GET, ErrorDetail.NOT_FOUND
        )


class ResourceSlotTypeAlreadyExists(EntityError, web.HTTPConflict):
    """Raised when creating a resource slot type whose slot name is already registered."""

    error_type = "https://api.backend.ai/probs/resource-slot-type-already-exists"
    error_title = "Resource slot type already exists."

    @override
    def entity_error_code(self) -> EntityErrorCode:
        return EntityErrorCode(
            ResourceSlotTypeEntityType(), ActionOperationType.CREATE, ErrorDetail.ALREADY_EXISTS
        )


class ResourceSlotTypeInUse(EntityError, web.HTTPConflict):
    """Raised when deleting a resource slot type that is still referenced elsewhere."""

    error_type = "https://api.backend.ai/probs/resource-slot-type-in-use"
    error_title = "Resource slot type is still referenced."

    @override
    def entity_error_code(self) -> EntityErrorCode:
        return EntityErrorCode(
            ResourceSlotTypeEntityType(), ActionOperationType.PURGE, ErrorDetail.CONFLICT
        )


class AgentResourceNotFound(FieldError, web.HTTPNotFound):
    """Raised when an agent resource entry for a given agent+slot is not found."""

    error_type = "https://api.backend.ai/probs/agent-resource-not-found"
    error_title = "Agent resource not found."

    @override
    def field_error_code(self) -> FieldErrorCode:
        return FieldErrorCode(
            AgentResourceFieldType(), ActionOperationType.GET, ErrorDetail.NOT_FOUND
        )


class ResourceAllocationNotFound(FieldError, web.HTTPNotFound):
    """Raised when a resource allocation entry for a given kernel+slot is not found."""

    error_type = "https://api.backend.ai/probs/resource-allocation-not-found"
    error_title = "Resource allocation not found."

    @override
    def field_error_code(self) -> FieldErrorCode:
        return FieldErrorCode(
            ResourceAllocationFieldType(), ActionOperationType.GET, ErrorDetail.NOT_FOUND
        )


class AgentResourceCapacityExceeded(FieldError, web.HTTPConflict):
    """Raised when an agent resource update would exceed the slot capacity."""

    error_type = "https://api.backend.ai/probs/agent-resource-capacity-exceeded"
    error_title = "Agent resource capacity exceeded."

    @override
    def field_error_code(self) -> FieldErrorCode:
        return FieldErrorCode(
            AgentResourceFieldType(), ActionOperationType.UPDATE, ErrorDetail.CONFLICT
        )
