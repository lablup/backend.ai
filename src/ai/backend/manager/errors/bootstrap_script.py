from typing import override

from aiohttp import web

from ai.backend.common.data.entity.bootstrap_script import BootstrapScriptFieldType
from ai.backend.common.exception import ErrorDetail
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.errors.base.field import FieldError, FieldErrorCode


class DefaultBootstrapScriptNotFound(FieldError, web.HTTPNotFound):
    error_type = "https://api.backend.ai/probs/default-bootstrap-script-not-found"
    error_title = "The default bootstrap script does not exist."

    @override
    def field_error_code(self) -> FieldErrorCode:
        return FieldErrorCode(
            BootstrapScriptFieldType(), ActionOperationType.UPDATE, ErrorDetail.NOT_FOUND
        )


class BootstrapScriptNotFound(FieldError, web.HTTPNotFound):
    error_type = "https://api.backend.ai/probs/bootstrap-script-not-found"
    error_title = "The bootstrap script does not exist."

    @override
    def field_error_code(self) -> FieldErrorCode:
        return FieldErrorCode(
            BootstrapScriptFieldType(), ActionOperationType.CREATE, ErrorDetail.NOT_FOUND
        )
