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
