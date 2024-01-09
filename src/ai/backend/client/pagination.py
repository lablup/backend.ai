from __future__ import annotations

import textwrap
from typing import Any, Dict, Final, Sequence, Tuple, TypeVar

from .exceptions import BackendAPIVersionError
from .output.types import FieldSpec, PaginatedResult
from .session import api_session

MAX_PAGE_SIZE: Final = 100
MIN_PAGE_SIZE: Final = 1

T = TypeVar("T")


async def execute_paginated_query(
    root_field: str,
    variables: Dict[str, Tuple[Any, str]],
    fields: Sequence[FieldSpec],
    *,
    limit: int,
    offset: int,
) -> PaginatedResult:
    if limit > MAX_PAGE_SIZE:
        raise ValueError(f"The page size cannot exceed {MAX_PAGE_SIZE}")
    if limit < MIN_PAGE_SIZE:
        raise ValueError(f"The page size cannot be less than {MIN_PAGE_SIZE}")
    query = """
    query($limit:Int!, $offset:Int!, $var_decls) {
      $root_field(
          limit:$limit, offset:$offset, $var_args) {
        items { $fields }
        total_count
      }
    }"""
    query = query.replace("$root_field", root_field)
    query = query.replace("$fields", " ".join(f.field_ref for f in fields))
    query = query.replace(
        "$var_decls",
        ", ".join(f"${key}: {value[1]}" for key, value in variables.items()),
    )
    query = query.replace(
        "$var_args",
        ", ".join(f"{key}:${key}" for key in variables.keys()),
    )
    query = textwrap.dedent(query).strip()
    var_values = {key: value[0] for key, value in variables.items()}
    var_values["limit"] = limit
    var_values["offset"] = offset
    data = await api_session.get().Admin._query(query, var_values)
    return PaginatedResult(
        total_count=data[root_field]["total_count"],
        items=data[root_field]["items"],
        fields=fields,
    )


async def fetch_paginated_result(
    root_field: str,
    variables: Dict[str, Tuple[Any, str]],
    fields: Sequence[FieldSpec],
    *,
    page_offset: int,
    page_size: int,
) -> PaginatedResult:
    if page_size > MAX_PAGE_SIZE:
        raise ValueError(f"The page size cannot exceed {MAX_PAGE_SIZE}")
    if page_size < MIN_PAGE_SIZE:
        raise ValueError(f"The page size cannot be less than {MIN_PAGE_SIZE}")
    if api_session.get().api_version < (6, "20210815"):
        if variables["filter"][0] is not None or variables["order"][0] is not None:
            raise BackendAPIVersionError(
                "filter and order arguments for paginated lists require v6.20210815 or later.",
            )
        # should remove to work with older managers
        variables.pop("filter")
        variables.pop("order")
    result = await execute_paginated_query(
        root_field,
        variables,
        fields,
        limit=page_size,
        offset=page_offset,
    )
    return result
