from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any, Final

from graphql import GraphQLResolveInfo
from strawberry.extensions.base_extension import SchemaExtension
from strawberry.utils.await_maybe import AwaitableOrValue

from ai.backend.logging.utils import BraceStyleAdapter

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))


class GQLLoggingExtension(SchemaExtension):
    """Logs GraphQL operation details for audit purposes."""

    def resolve(
        self,
        _next: Callable[..., Any],
        root: Any,
        info: GraphQLResolveInfo,
        *args: str,
        **kwargs: Any,
    ) -> AwaitableOrValue[object]:
        if info.path.prev is None:
            # TODO: Log access_key when StrawberryGQLContext has user info
            log.info(
                "ADMIN.GQL.V2 ({}:{}, op:{})",
                info.operation.operation,
                info.field_name,
                info.operation.name,
            )
        result: AwaitableOrValue[object] = _next(root, info, *args, **kwargs)
        return result
