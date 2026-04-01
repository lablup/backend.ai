"""
Resource policy DTOs v2 for Manager API.
"""

from ai.backend.common.dto.manager.v2.resource_policy.request import (
    CreateKeypairResourcePolicyInput,
    CreateProjectResourcePolicyInput,
    CreateUserResourcePolicyInput,
    DeleteKeypairResourcePolicyInput,
    DeleteProjectResourcePolicyInput,
    DeleteUserResourcePolicyInput,
    UpdateKeypairResourcePolicyInput,
    UpdateProjectResourcePolicyInput,
    UpdateUserResourcePolicyInput,
)
from ai.backend.common.dto.manager.v2.resource_policy.response import (
    CreateKeypairResourcePolicyPayload,
    CreateProjectResourcePolicyPayload,
    CreateUserResourcePolicyPayload,
    DeleteKeypairResourcePolicyPayload,
    DeleteProjectResourcePolicyPayload,
    DeleteUserResourcePolicyPayload,
    KeypairResourcePolicyNode,
    ProjectResourcePolicyNode,
    UpdateKeypairResourcePolicyPayload,
    UpdateProjectResourcePolicyPayload,
    UpdateUserResourcePolicyPayload,
    UserResourcePolicyNode,
)
from ai.backend.common.dto.manager.v2.resource_policy.types import (
    DefaultForUnspecified,
    KeypairResourcePolicyOrderField,
    OrderDirection,
    ProjectResourcePolicyOrderField,
    UserResourcePolicyOrderField,
)

__all__ = (
    # Types
    "DefaultForUnspecified",
    "KeypairResourcePolicyOrderField",
    "OrderDirection",
    "ProjectResourcePolicyOrderField",
    "UserResourcePolicyOrderField",
    # Input models (request) -- Keypair
    "CreateKeypairResourcePolicyInput",
    "DeleteKeypairResourcePolicyInput",
    "UpdateKeypairResourcePolicyInput",
    # Input models (request) -- User
    "CreateUserResourcePolicyInput",
    "DeleteUserResourcePolicyInput",
    "UpdateUserResourcePolicyInput",
    # Input models (request) -- Project
    "CreateProjectResourcePolicyInput",
    "DeleteProjectResourcePolicyInput",
    "UpdateProjectResourcePolicyInput",
    # Node and Payload models (response) -- Keypair
    "CreateKeypairResourcePolicyPayload",
    "DeleteKeypairResourcePolicyPayload",
    "KeypairResourcePolicyNode",
    "UpdateKeypairResourcePolicyPayload",
    # Node and Payload models (response) -- User
    "CreateUserResourcePolicyPayload",
    "DeleteUserResourcePolicyPayload",
    "UpdateUserResourcePolicyPayload",
    "UserResourcePolicyNode",
    # Node and Payload models (response) -- Project
    "CreateProjectResourcePolicyPayload",
    "DeleteProjectResourcePolicyPayload",
    "ProjectResourcePolicyNode",
    "UpdateProjectResourcePolicyPayload",
)
