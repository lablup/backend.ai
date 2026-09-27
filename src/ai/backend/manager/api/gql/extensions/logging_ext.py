from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any, Final, override

from graphql import GraphQLResolveInfo
from strawberry.extensions.base_extension import SchemaExtension
from strawberry.utils.await_maybe import AwaitableOrValue

from ai.backend.logging.structured import StructuredLogger

log: Final = StructuredLogger(logging.getLogger(__spec__.name))


class GQLLoggingExtension(SchemaExtension):
    """Logs GraphQL operation details for audit purposes."""

    @override
    def resolve(
        self,
        _next: Callable[..., Any],
        root: Any,
        info: GraphQLResolveInfo,
        *args: Any,
        **kwargs: Any,
    ) -> AwaitableOrValue[object]:
        if info.path.prev is None:
            # TODO: Log access_key when StrawberryGQLContext has user info
            log.trace(
                "graphql operation requested",
                operation_type=info.operation.operation,
                field_name=info.field_name,
                operation_name=info.operation.name.value if info.operation.name else None,
            )
        result: AwaitableOrValue[object] = _next(root, info, *args, **kwargs)
        return result
