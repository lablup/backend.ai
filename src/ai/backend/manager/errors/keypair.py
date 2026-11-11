"""
Keypair-related exceptions.
"""

from __future__ import annotations

from typing import override

from aiohttp import web

from ai.backend.common.data.entity.resource_policy import KeyPairResourcePolicyEntityType
from ai.backend.common.exception import ErrorDetail
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.errors.base.entity import EntityError, EntityErrorCode


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
