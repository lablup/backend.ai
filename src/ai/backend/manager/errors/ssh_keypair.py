from typing import override

from aiohttp import web

from ai.backend.common.data.entity.ssh_keypair import SSHKeypairFieldType
from ai.backend.common.exception import ErrorDetail
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.errors.base.field import FieldError, FieldErrorCode


class DefaultSSHKeypairNotFound(FieldError, web.HTTPNotFound):
    error_type = "https://api.backend.ai/probs/default-ssh-keypair-not-found"
    error_title = "The default SSH keypair does not exist."

    @override
    def field_error_code(self) -> FieldErrorCode:
        return FieldErrorCode(SSHKeypairFieldType(), ActionOperationType.GET, ErrorDetail.NOT_FOUND)


class SSHKeyNotFound(FieldError, web.HTTPNotFound):
    error_type = "https://api.backend.ai/probs/ssh-key-not-found"
    error_title = "The SSH key does not exist."

    @override
    def field_error_code(self) -> FieldErrorCode:
        return FieldErrorCode(SSHKeypairFieldType(), ActionOperationType.GET, ErrorDetail.NOT_FOUND)


class DefaultSSHKeyConflict(FieldError, web.HTTPConflict):
    error_type = "https://api.backend.ai/probs/default-ssh-key-conflict"
    error_title = "Another request changed the user's default SSH key at the same time."

    @override
    def field_error_code(self) -> FieldErrorCode:
        return FieldErrorCode(
            SSHKeypairFieldType(), ActionOperationType.UPDATE, ErrorDetail.CONFLICT
        )
