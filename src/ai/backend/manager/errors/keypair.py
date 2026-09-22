"""
Keypair-related exceptions.
"""

from __future__ import annotations

from typing import override

from aiohttp import web

from ai.backend.common.data.entity.keypair import KeyPairFieldType
from ai.backend.common.data.entity.resource_policy import KeyPairResourcePolicyEntityType
from ai.backend.common.exception import ErrorDetail
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.errors.base.entity import EntityError, EntityErrorCode
from ai.backend.manager.errors.base.field import FieldError, FieldErrorCode


class InvalidSSHPrivateKey(FieldError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/invalid-ssh-private-key"
    error_title = "The SSH private key is invalid or in an unsupported format."

    @override
    def field_error_code(self) -> FieldErrorCode:
        return FieldErrorCode(
            KeyPairFieldType(), ActionOperationType.CREATE, ErrorDetail.INVALID_DATA_FORMAT
        )


class InvalidSSHPublicKey(FieldError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/invalid-ssh-public-key"
    error_title = "The SSH public key is invalid or in an unsupported format."

    @override
    def field_error_code(self) -> FieldErrorCode:
        return FieldErrorCode(
            KeyPairFieldType(), ActionOperationType.CREATE, ErrorDetail.INVALID_DATA_FORMAT
        )


class KeypairResourcePolicyNotFound(EntityError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/keypair-resource-policy-not-found"
    error_title = "No keypair resource policy goes by that name."

    @override
    def entity_error_code(self) -> EntityErrorCode:
        return EntityErrorCode(
            KeyPairResourcePolicyEntityType(), ActionOperationType.GET, ErrorDetail.NOT_FOUND
        )


class NoDefaultKeypairResourcePolicy(EntityError, web.HTTPInternalServerError):
    error_type = "https://api.backend.ai/probs/no-default-keypair-resource-policy"
    error_title = "No keypair resource policy is marked as the default."

    @override
    def entity_error_code(self) -> EntityErrorCode:
        return EntityErrorCode(
            KeyPairResourcePolicyEntityType(), ActionOperationType.GET, ErrorDetail.NOT_FOUND
        )


class SSHKeypairMismatch(FieldError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/ssh-keypair-mismatch"
    error_title = "The SSH public key does not match the private key."

    @override
    def field_error_code(self) -> FieldErrorCode:
        return FieldErrorCode(
            KeyPairFieldType(), ActionOperationType.CREATE, ErrorDetail.INVALID_PARAMETERS
        )
