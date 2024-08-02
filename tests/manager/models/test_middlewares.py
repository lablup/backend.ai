import pytest

from ai.backend.manager.models.gql import GQLDeprecatedQueryCheckMiddleware, GraphQueryContext


@pytest.fixture(scope="module")
def default_context(base_context) -> GraphQueryContext:  # noqa: F811
    return base_context()


async def execute_query(client, query, variables, context_value, caplog, expected_warning_count):
    with caplog.at_level("WARNING"):
        _ = await client.execute_async(
            query,
            variables=variables,
            context_value=context_value,
            middleware=[GQLDeprecatedQueryCheckMiddleware()],
        )
        assert len(caplog.records) == expected_warning_count


@pytest.mark.asyncio
async def test_deprecated_query_logs_warning(default_context, client, caplog, deprecated_query):
    query, variables = deprecated_query
    await execute_query(client, query, variables, default_context, caplog, expected_warning_count=1)


@pytest.mark.asyncio
async def test_non_deprecated_query_does_not_logs_warning(
    default_context, client, caplog, non_deprecated_query
):
    query, variables = non_deprecated_query
    await execute_query(client, query, variables, default_context, caplog, expected_warning_count=0)
